<?php

namespace SecureWare\Models;

use SecureWare\Core\Database;

class Setting
{
    private static ?array $cache = null;

    public static function all(): array
    {
        if (self::$cache === null) {
            $rows = Database::connection()->query('SELECT `key`, `value` FROM settings')->fetchAll();
            self::$cache = array_column($rows, 'value', 'key');
        }

        return self::$cache;
    }

    public static function get(string $key, mixed $default = null): mixed
    {
        return self::all()[$key] ?? $default;
    }

    public static function set(string $key, string $value): void
    {
        $stmt = Database::connection()->prepare(
            'INSERT INTO settings (`key`, `value`) VALUES (:key, :value)
             ON DUPLICATE KEY UPDATE `value` = VALUES(`value`)'
        );
        $stmt->execute(['key' => $key, 'value' => $value]);

        if (self::$cache !== null) {
            self::$cache[$key] = $value;
        }
    }

    public static function setMany(array $values): void
    {
        foreach ($values as $key => $value) {
            self::set($key, (string) $value);
        }
    }
}
