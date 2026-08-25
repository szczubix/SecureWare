<?php

namespace SecureWare\Core;

class Session
{
    public static function start(): void
    {
        if (session_status() === PHP_SESSION_ACTIVE) {
            return;
        }

        $config = Config::get('session');

        session_set_cookie_params([
            'lifetime' => 0,
            'path'     => '/',
            'secure'   => (bool) ($config['secure'] ?? true),
            'httponly' => true,
            'samesite' => 'Lax',
        ]);

        session_name($config['name'] ?? 'sw_session');
        session_start();
    }

    public static function get(string $key, mixed $default = null): mixed
    {
        return $_SESSION[$key] ?? $default;
    }

    public static function set(string $key, mixed $value): void
    {
        $_SESSION[$key] = $value;
    }

    public static function remove(string $key): void
    {
        unset($_SESSION[$key]);
    }

    public static function flash(string $key, ?string $message = null): mixed
    {
        if ($message !== null) {
            $_SESSION['_flash'][$key] = $message;
            return null;
        }

        $value = $_SESSION['_flash'][$key] ?? null;
        unset($_SESSION['_flash'][$key]);
        return $value;
    }

    public static function regenerate(): void
    {
        session_regenerate_id(true);
    }

    public static function destroy(): void
    {
        $_SESSION = [];
        session_destroy();
    }
}
