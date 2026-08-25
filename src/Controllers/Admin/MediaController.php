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
            Session::flash('error', 'Sesja wygasla, sprobuj ponownie.');
            Response::redirect($this->url());
        }

        $file = $request->file('file');
        if (!$file) {
            Session::flash('error', 'Nie wybrano pliku.');
            Response::redirect($this->url());
        }

        if ($file['error'] !== UPLOAD_ERR_OK) {
            Session::flash('error', 'Blad podczas wgrywania pliku.');
            Response::redirect($this->url());
        }

        if ($file['size'] > self::MAX_SIZE) {
            Session::flash('error', 'Plik jest za duzy (limit 8 MB).');
            Response::redirect($this->url());
        }

        $mime = mime_content_type($file['tmp_name']) ?: '';
        if (!isset(self::ALLOWED_MIME[$mime])) {
            Session::flash('error', 'Niedozwolony typ pliku. Dozwolone: JPG, PNG, WEBP, GIF, PDF.');
            Response::redirect($this->url());
        }

        $ext        = self::ALLOWED_MIME[$mime];
        $baseName   = Str::slug(pathinfo($file['name'], PATHINFO_FILENAME)) ?: 'plik';
        $uniqueName = $baseName . '-' . bin2hex(random_bytes(4)) . '.' . $ext;

        $subDir   = date('Y/m');
        $uploadDir = ROOT_PATH . '/public/uploads/' . $subDir;
        if (!is_dir($uploadDir)) {
            mkdir($uploadDir, 0755, true);
        }

        $destination = $uploadDir . '/' . $uniqueName;
        if (!move_uploaded_file($file['tmp_name'], $destination)) {
            Session::flash('error', 'Nie udalo sie zapisac pliku na serwerze.');
            Response::redirect($this->url());
        }

        $publicPath = '/uploads/' . $subDir . '/' . $uniqueName;
        $id = Media::create($uniqueName, $publicPath, $mime, (int) $file['size'], (int) Auth::id());
        Logger::record('upload', 'media', $id);

        Response::redirect($this->url());
    }

    public function destroy(Request $request, string $id): void
    {
        Auth::requirePermission('media.delete');

        if (Csrf::verify($request->input('_csrf'))) {
            $media = Media::delete((int) $id);
            if ($media) {
                $path = ROOT_PATH . '/public' . $media['path'];
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
