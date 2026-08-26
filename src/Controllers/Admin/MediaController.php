<?php

namespace SecureWare\Controllers\Admin;

use SecureWare\Core\Auth;
use SecureWare\Core\Config;
use SecureWare\Core\Csrf;
use SecureWare\Core\Logger;
use SecureWare\Core\Request;
use SecureWare\Core\Response;
use SecureWare\Core\Session;
use SecureWare\Core\Str;
use SecureWare\Core\View;
use SecureWare\Models\Media;

class MediaController
{
    private const ALLOWED_MIME = [
        'image/jpeg' => 'jpg',
        'image/png'  => 'png',
        'image/webp' => 'webp',
        'image/gif'  => 'gif',
        'application/pdf' => 'pdf',
    ];
    private const MAX_SIZE = 8 * 1024 * 1024; // 8 MB

    public function index(Request $request): void
    {
        Auth::requirePermission('media.view');

        echo View::render('admin/media/index', [
            'media' => Media::all(),
            'error' => Session::flash('error'),
        ], 'admin/layout');
    }

    public function upload(Request $request): void
    {
        Auth::requirePermission('media.upload');

        if (!Csrf::verify($request->input('_csrf'))) {
            Session::flash('error', 'Sesja wygasła, spróbuj ponownie.');
            Response::redirect($this->url());
        }

        [$media, $error] = $this->storeUpload($request);
        if ($error) {
            Session::flash('error', $error);
        }

        Response::redirect($this->url());
    }

    /**
     * Wariant AJAX uzywany przez edytor tresci (wstawianie obrazkow w
     * artykulach/stronach bez opuszczania formularza) - zwraca JSON zamiast
     * przekierowania.
     */
    public function uploadJson(Request $request): void
    {
        Auth::requirePermission('media.upload');
        header('Content-Type: application/json; charset=UTF-8');

        if (!Csrf::verify($request->input('_csrf'))) {
            http_response_code(419);
            echo json_encode(['ok' => false, 'error' => 'Sesja wygasła, odśwież stronę.']);
            return;
        }

        [$media, $error] = $this->storeUpload($request);
        if ($error) {
            http_response_code(422);
            echo json_encode(['ok' => false, 'error' => $error]);
            return;
        }

        echo json_encode(['ok' => true, 'media' => $media]);
    }

    public function listJson(Request $request): void
    {
        Auth::requirePermission('media.view');
        header('Content-Type: application/json; charset=UTF-8');

        $images = array_values(array_filter(Media::all(200), static fn ($m) => str_starts_with($m['mime'], 'image/')));
        echo json_encode(['ok' => true, 'media' => $images]);
    }

    /**
     * @return array{0: array|null, 1: string|null} [media, error]
     */
    private function storeUpload(Request $request): array
    {
        $file = $request->file('file');
        if (!$file) {
            return [null, 'Nie wybrano pliku.'];
        }

        if ($file['error'] !== UPLOAD_ERR_OK) {
            return [null, 'Błąd podczas wgrywania pliku.'];
        }

        if ($file['size'] > self::MAX_SIZE) {
            return [null, 'Plik jest za duży (limit 8 MB).'];
        }

        $mime = mime_content_type($file['tmp_name']) ?: '';
        if (!isset(self::ALLOWED_MIME[$mime])) {
            return [null, 'Niedozwolony typ pliku. Dozwolone: JPG, PNG, WEBP, GIF, PDF.'];
        }

        $ext        = self::ALLOWED_MIME[$mime];
        $baseName   = Str::slug(pathinfo($file['name'], PATHINFO_FILENAME)) ?: 'plik';
        $uniqueName = $baseName . '-' . bin2hex(random_bytes(4)) . '.' . $ext;

        $subDir    = date('Y/m');
        $uploadDir = ROOT_PATH . '/uploads/' . $subDir;
        if (!is_dir($uploadDir)) {
            mkdir($uploadDir, 0755, true);
        }

        $destination = $uploadDir . '/' . $uniqueName;
        if (!move_uploaded_file($file['tmp_name'], $destination)) {
            return [null, 'Nie udało się zapisać pliku na serwerze.'];
        }

        $publicPath = '/uploads/' . $subDir . '/' . $uniqueName;
        $id = Media::create($uniqueName, $publicPath, $mime, (int) $file['size'], (int) Auth::id());
        Logger::record('upload', 'media', $id);

        return [Media::find($id), null];
    }

    public function destroy(Request $request, string $id): void
    {
        Auth::requirePermission('media.delete');

        if (Csrf::verify($request->input('_csrf'))) {
            $media = Media::delete((int) $id);
            if ($media) {
                $path = ROOT_PATH . $media['path'];
                if (is_file($path)) {
                    unlink($path);
                }
                Logger::record('delete', 'media', (int) $id);
            }
        }

        Response::redirect($this->url());
    }

    private function url(): string
    {
        return '/' . Config::get('admin_path') . '/media';
    }
}
