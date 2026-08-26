<?php

namespace SecureWare\Core;

class Str
{
    public static function slug(string $text): string
    {
        $map = [
            'ą'=>'a','ć'=>'c','ę'=>'e','ł'=>'l','ń'=>'n','ó'=>'o','ś'=>'s','ź'=>'z','ż'=>'z',
            'Ą'=>'a','Ć'=>'c','Ę'=>'e','Ł'=>'l','Ń'=>'n','Ó'=>'o','Ś'=>'s','Ź'=>'z','Ż'=>'z',
        ];
        $text = strtr($text, $map);
        $text = strtolower($text);
        $text = preg_replace('/[^a-z0-9]+/', '-', $text);
        return trim($text, '-');
    }

    public static function excerpt(string $html, int $length = 160): string
    {
        $text = trim(preg_replace('/\s+/', ' ', strip_tags($html)));
        if (mb_strlen($text) <= $length) {
            return $text;
        }

        return mb_substr($text, 0, $length) . '…';
    }

    /** Deterministyczna ikona zastepcza (np. dla kart bloga bez zdjecia glownego) - ta sama tresc zawsze dostaje ta sama ikone. */
    public static function fallbackIcon(string $seed): string
    {
        $icons = ['shield-check', 'cloud-upload', 'server', 'refresh-ccw', 'lock', 'activity', 'layers', 'file-check'];
        return $icons[crc32($seed) % count($icons)];
    }
}
