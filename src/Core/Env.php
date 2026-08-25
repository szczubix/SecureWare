<?php

namespace SecureWare\Core;

/**
 * Minimalny parser .env - bez zaleznosci od Composera. Celowo NIE uzywa
 * putenv()/getenv(): niektore hostingi (np. shared hosting z "site sandbox")
 * blokuja putenv() ze wzgledow bezpieczenstwa, wiec wartosci trzymamy
 * wylacznie we wlasnej tablicy w pamieci procesu.
 */
class Env
{
    private static bool $loaded = false;

    /** @var array<string, string> */
    private static array $values = [];

    public static function load(string $path): void
    {
        if (self::$loaded || !is_file($path)) {
            self::$loaded = true;
            return;
        }

        foreach (file($path, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES) as $line) {
            $line = trim($line);
            if ($line === '' || str_starts_with($line, '#')) {
                continue;
            }
            if (!str_contains($line, '=')) {
                continue;
            }
            [$key, $value] = explode('=', $line, 2);
            $key   = trim($key);
            $value = trim($value);
            $value = trim($value, "\"'");

            if (!array_key_exists($key, self::$values)) {
                self::$values[$key] = $value;
            }
        }

        self::$loaded = true;
    }

    public static function get(string $key, mixed $default = null): mixed
    {
        $value = self::$values[$key] ?? null;
        if ($value === null) {
            return $default;
        }

        return match (strtolower($value)) {
            'true'  => true,
            'false' => false,
            default => $value,
        };
    }
}
