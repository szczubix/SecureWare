<?php

namespace SecureWare\Core;

/**
 * Aktualny jezyk publicznej strony (panel admina zawsze zostaje w PL).
 * Ustawiany raz, w konstruktorze Request, na podstawie prefiksu /en/ w
 * adresie - kontrolery/widoki odczytuja go stad zamiast dostawac locale
 * jako osobny parametr wszedzie.
 */
class Locale
{
    public const DEFAULT = 'pl';
    public const AVAILABLE = ['pl', 'en'];

    private static string $current = self::DEFAULT;

    public static function set(string $locale): void
    {
        self::$current = in_array($locale, self::AVAILABLE, true) ? $locale : self::DEFAULT;
    }

    public static function current(): string
    {
        return self::$current;
    }

    public static function isDefault(): bool
    {
        return self::$current === self::DEFAULT;
    }

    /** Prefiks do budowania linkow ('' dla PL, '/en' dla EN). */
    public static function prefix(): string
    {
        return self::$current === self::DEFAULT ? '' : '/' . self::$current;
    }

    /** Buduje link do tej samej sciezki w innym jezyku, np. dla przelacznika PL/EN. */
    public static function urlIn(string $locale, string $path): string
    {
        $path = '/' . ltrim($path, '/');
        if ($path === '/') {
            $path = '';
        }
        $prefix = $locale === self::DEFAULT ? '' : '/' . $locale;
        return $prefix . $path ?: '/';
    }

    /**
     * Dodaje prefiks biezacego jezyka do wewnetrznego linku (np. "/oferta"
     * -> "/en/oferta" gdy jezyk to EN) - linki zewnetrzne/mailto/tel/kotwice
     * zostaja bez zmian. Uzywac wszedzie, gdzie widok generuje href do
     * innej strony serwisu.
     */
    public static function url(string $path): string
    {
        if ($path === '' || preg_match('#^(https?:)?//#', $path) || str_starts_with($path, 'mailto:') || str_starts_with($path, 'tel:') || str_starts_with($path, '#')) {
            return $path;
        }

        return self::prefix() . '/' . ltrim($path, '/');
    }
}
