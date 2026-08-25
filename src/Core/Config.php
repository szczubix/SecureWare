<?php

namespace SecureWare\Core;

class Config
{
    private static ?array $items = null;

    public static function load(array $items): void
    {
        self::$items = $items;
    }

    public static function all(): array
    {
        return self::$items ?? [];
    }

    public static function get(string $key, mixed $default = null): mixed
    {
        return self::$items[$key] ?? $default;
    }
}
