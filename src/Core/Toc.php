<?php

namespace SecureWare\Core;

/**
 * Wyciaga spis tresci z tresci HTML (naglowki <h2>) - uzywane do bocznego,
 * sticky spisu tresci na dluzszych stronach (CMS, artykuly). Dziala na
 * dowolnej tresci z bogatego edytora - dopisuje kazdemu <h2> atrybut id
 * (na bazie Str::slug, z deduplikacja) i zwraca liste pozycji do wyswietlenia.
 */
class Toc
{
    /** @return array{html: string, items: array<int, array{id: string, text: string}>} */
    public static function extract(string $html): array
    {
        $items = [];
        $seen = [];

        $withIds = preg_replace_callback('/<h2>(.*?)<\/h2>/si', function (array $m) use (&$items, &$seen) {
            $text = trim(strip_tags($m[1]));
            if ($text === '') {
                return $m[0];
            }

            $id = Str::slug($text) ?: 'sekcja';
            $base = $id;
            $i = 2;
            while (isset($seen[$id])) {
                $id = $base . '-' . $i++;
            }
            $seen[$id] = true;

            $items[] = ['id' => $id, 'text' => $text];

            return '<h2 id="' . $id . '">' . $m[1] . '</h2>';
        }, $html);

        return ['html' => $withIds ?? $html, 'items' => $items];
    }
}
