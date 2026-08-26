<?php

namespace SecureWare\Models;

use SecureWare\Core\Database;

class Service
{
    private const TRANSLATABLE = ['name', 'short_description', 'content', 'meta_title', 'meta_description'];

    public static function all(): array
    {
        return Database::connection()->query('SELECT * FROM services ORDER BY position, name')->fetchAll();
    }

    public static function published(string $locale = 'pl'): array
    {
        $rows = Database::connection()
            ->query("SELECT * FROM services WHERE status = 'published' ORDER BY position, name")
            ->fetchAll();

        return Translation::applyToMany($rows, 'service', $locale, self::TRANSLATABLE);
    }

    public static function find(int $id): ?array
    {
        $stmt = Database::connection()->prepare('SELECT * FROM services WHERE id = :id');
        $stmt->execute(['id' => $id]);
        return self::decode($stmt->fetch() ?: null);
    }

    public static function findBySlug(string $slug, string $locale = 'pl'): ?array
    {
        $stmt = Database::connection()->prepare("SELECT * FROM services WHERE slug = :slug AND status = 'published'");
        $stmt->execute(['slug' => $slug]);
        $service = self::decode($stmt->fetch() ?: null);

        return $service ? Translation::applyTo($service, 'service', $locale, self::TRANSLATABLE) : null;
    }

    private static function decode(?array $service): ?array
    {
        if ($service) {
            $service['meta'] = json_decode($service['meta'] ?? '[]', true) ?: [];
        }
        return $service;
    }

    public static function create(array $data): int
    {
        $stmt = Database::connection()->prepare(
            'INSERT INTO services (name, slug, icon, short_description, content, position, status, meta,
                                    meta_title, meta_description, created_at, updated_at)
             VALUES (:name, :slug, :icon, :short_description, :content, :position, :status, :meta,
                     :meta_title, :meta_description, NOW(), NOW())'
        );
        $stmt->execute(self::params($data));
        return (int) Database::connection()->lastInsertId();
    }

    public static function update(int $id, array $data): void
    {
        $stmt = Database::connection()->prepare(
            'UPDATE services SET name = :name, slug = :slug, icon = :icon, short_description = :short_description,
                    content = :content, position = :position, status = :status, meta = :meta,
                    meta_title = :meta_title, meta_description = :meta_description, updated_at = NOW()
             WHERE id = :id'
        );
        $stmt->execute(array_merge(self::params($data), ['id' => $id]));
    }

    private static function params(array $data): array
    {
        return [
            'name'              => $data['name'],
            'slug'              => $data['slug'],
            'icon'              => $data['icon'] ?? 'shield',
            'short_description' => $data['short_description'] ?? '',
            'content'           => $data['content'] ?? '',
            'position'          => (int) ($data['position'] ?? 0),
            'status'            => $data['status'] ?? 'draft',
            'meta'              => json_encode($data['meta'] ?? [], JSON_UNESCAPED_UNICODE),
            'meta_title'        => $data['meta_title'] ?? null,
            'meta_description'  => $data['meta_description'] ?? null,
        ];
    }

    public static function delete(int $id): void
    {
        $stmt = Database::connection()->prepare('DELETE FROM services WHERE id = :id');
        $stmt->execute(['id' => $id]);
    }

    public static function slugExists(string $slug, ?int $excludeId = null): bool
    {
        $sql = 'SELECT COUNT(*) FROM services WHERE slug = :slug';
        $params = ['slug' => $slug];
        if ($excludeId) {
            $sql .= ' AND id != :id';
            $params['id'] = $excludeId;
        }
        $stmt = Database::connection()->prepare($sql);
        $stmt->execute($params);
        return (int) $stmt->fetchColumn() > 0;
    }
}
