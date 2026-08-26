<?php

namespace SecureWare\Models;

use SecureWare\Core\Database;

/**
 * Generyczne tlumaczenia pol tresci (usluga/artykul/strona/kategoria) -
 * jedna tabela zamiast osobnych kolumn *_en na kazdej tabeli, zeby dzialalo
 * dla kazdego obecnego i przyszlego typu tresci bez zmian schematu.
 */
class Translation
{
    public static function get(string $type, int $id, string $locale, string $field, ?string $default = null): ?string
    {
        if ($locale === 'pl' || $id <= 0) {
            return $default;
        }

        $stmt = Database::connection()->prepare(
            'SELECT value FROM translations WHERE entity_type = :type AND entity_id = :id AND locale = :locale AND field = :field'
        );
        $stmt->execute(['type' => $type, 'id' => $id, 'locale' => $locale, 'field' => $field]);
        $value = $stmt->fetchColumn();

        return ($value !== false && $value !== null && $value !== '') ? $value : $default;
    }

    /** @return array<string,string> pole => wartosc */
    public static function getAll(string $type, int $id, string $locale): array
    {
        if ($id <= 0) {
            return [];
        }

        $stmt = Database::connection()->prepare(
            'SELECT field, value FROM translations WHERE entity_type = :type AND entity_id = :id AND locale = :locale'
        );
        $stmt->execute(['type' => $type, 'id' => $id, 'locale' => $locale]);

        return array_column($stmt->fetchAll(), 'value', 'field');
    }

    /** @param array<string,string> $fields pole => wartosc (pusty string usuwa tlumaczenie pola) */
    public static function setMany(string $type, int $id, string $locale, array $fields): void
    {
        $pdo = Database::connection();
        $upsert = $pdo->prepare(
            'INSERT INTO translations (entity_type, entity_id, locale, field, value)
             VALUES (:type, :id, :locale, :field, :value)
             ON DUPLICATE KEY UPDATE value = VALUES(value)'
        );
        $delete = $pdo->prepare(
            'DELETE FROM translations WHERE entity_type = :type AND entity_id = :id AND locale = :locale AND field = :field'
        );

        foreach ($fields as $field => $value) {
            $value = trim((string) $value);
            if ($value === '') {
                $delete->execute(['type' => $type, 'id' => $id, 'locale' => $locale, 'field' => $field]);
            } else {
                $upsert->execute(['type' => $type, 'id' => $id, 'locale' => $locale, 'field' => $field, 'value' => $value]);
            }
        }
    }

    /**
     * Naklada tlumaczenia na wiersz pobrany z bazy (PL) - dla kazdego pola z
     * listy podmienia wartosc, jesli istnieje tlumaczenie, w przeciwnym
     * razie zostawia oryginalna (PL) wartosc jako fallback.
     *
     * @param array<int,string> $fields
     */
    public static function applyTo(array $row, string $type, string $locale, array $fields): array
    {
        if ($locale === 'pl' || empty($row['id'])) {
            return $row;
        }

        $translated = self::getAll($type, (int) $row['id'], $locale);
        foreach ($fields as $field) {
            if (!empty($translated[$field])) {
                $row[$field] = $translated[$field];
            }
        }

        return $row;
    }

    /** Nakłada tłumaczenia na listę wierszy naraz. */
    public static function applyToMany(array $rows, string $type, string $locale, array $fields): array
    {
        if ($locale === 'pl') {
            return $rows;
        }

        return array_map(static fn (array $row) => self::applyTo($row, $type, $locale, $fields), $rows);
    }
}
