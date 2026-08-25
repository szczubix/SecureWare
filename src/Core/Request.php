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

        $this->path = '/' . trim($path, '/');
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
