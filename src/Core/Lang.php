<?php

namespace SecureWare\Core;

/**
 * Male slowniki tekstow interfejsu (lang/pl.php, lang/en.php) - tylko dla
 * krotkich etykiet UI, ktore nie sa tresc a zarzadzana w panelu. Uzycie:
 * Lang::t('offer.read_more'). Placeholder %s wspierany przez sprintf.
 */
class Lang
{
    private static array $dictionaries = [];

    public static function t(string $key, string ...$args): string
    {
        $locale = Locale::current();
        $dict = self::dictionary($locale);
        $value = $dict[$key] ?? self::dictionary(Locale::DEFAULT)[$key] ?? $key;

        return $args ? sprintf($value, ...$args) : $value;
    }

    private static function dictionary(string $locale): array
    {
        if (!isset(self::$dictionaries[$locale])) {
            $path = ROOT_PATH . '/lang/' . $locale . '.php';
            self::$dictionaries[$locale] = is_file($path) ? require $path : [];
        }

        return self::$dictionaries[$locale];
    }
}
