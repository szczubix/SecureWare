<?php

namespace SecureWare\Core;

class Request
{
    public string $method;
    public string $path;
    /** @var array<string,string> */
    public array $params = [];

    public function __construct()
    {
        $this->method = strtoupper($_SERVER['REQUEST_METHOD'] ?? 'GET');

        $uri  = $_SERVER['REQUEST_URI'] ?? '/';
        $path = parse_url($uri, PHP_URL_PATH) ?: '/';
        $path = rawurldecode($path);

        // Strip base directory if the app lives in a sub-folder.
        $base = rtrim(dirname($_SERVER['SCRIPT_NAME'] ?? ''), '/');
        if ($base !== '' && str_starts_with($path, $base)) {
            $path = substr($path, strlen($base));
        }

        $path = '/' . trim($path, '/');

        // Jezyk publicznej strony przez prefiks /en - panel admina (sciezka
        // z ADMIN_PATH) zawsze zostaje po polsku, wiec sprawdzamy to jako
        // pierwsze i nie ruszamy sciezki, jesli to panel.
        $adminPath = '/' . trim((string) Config::get('admin_path'), '/');
        if ($path !== $adminPath && !str_starts_with($path, $adminPath . '/')) {
            if ($path === '/en' || str_starts_with($path, '/en/')) {
                Locale::set('en');
                $path = '/' . ltrim(substr($path, 3), '/');
            } else {
                Locale::set('pl');
            }
        }

        $this->path = $path;
    }

    public function input(string $key, mixed $default = null): mixed
    {
        $value = $_POST[$key] ?? $_GET[$key] ?? $default;
        return is_string($value) ? trim($value) : $value;
    }

    public function all(): array
    {
        return array_merge($_GET, $_POST);
    }

    public function isPost(): bool
    {
        return $this->method === 'POST';
    }

    public function file(string $key): ?array
    {
        return isset($_FILES[$key]) && $_FILES[$key]['error'] !== UPLOAD_ERR_NO_FILE
            ? $_FILES[$key]
            : null;
    }

    public function ip(): string
    {
        return $_SERVER['REMOTE_ADDR'] ?? '0.0.0.0';
    }
}
