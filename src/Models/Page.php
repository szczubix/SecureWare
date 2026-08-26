<?php

namespace SecureWare\Models;

use SecureWare\Core\Database;

class Page
{
    private const TRANSLATABLE = ['title', 'content', 'meta_title', 'meta_description'];

    public static function all(): array
    {
        return Database::connection()->query('SELECT * FROM pages ORDER BY title')->fetchAll();
    }

    public static function find(int $id): ?array
    {
        $stmt = Database::connection()->prepare('SELECT * FROM pages WHERE id = :id');
        $stmt->execute(['id' => $id]);
        return self::decode($stmt->fetch() ?: null);
    }

    public static function findBySlug(string $slug, string $locale = 'pl'): ?array
    {
        $stmt = Database::connection()->prepare("SELECT * FROM pages WHERE slug = :slug AND status = 'published'");
        $stmt->execute(['slug' => $slug]);
        $page = self::decode($stmt->fetch() ?: null);

        return $page ? Translation::applyTo($page, 'page', $locale, self::TRANSLATABLE) : null;
    }

    public static function publishedSlugs(): array
    {
        return Database::connection()->query("SELECT slug, updated_at FROM pages WHERE status = 'published'")->fetchAll();
    }

    private static function decode(?array $page): ?array
    {
        if ($page) {
            $page['meta'] = json_decode($page['meta'] ?? '[]', true) ?: [];
        }
        return $page;
    }

    public static function create(array $data): int
    {
        $stmt = Database::connection()->prepare(
            'INSERT INTO pages (title, slug, content, template, parent_id, status, meta, meta_title, meta_description, created_at, updated_at)
             VALUES (:title, :slug, :content, :template, :parent_id, :status, :meta, :meta_title, :meta_description, NOW(), NOW())'
        );
        $stmt->execute(self::params($data));
        return (int) Database::connection()->lastInsertId();
    }

    public static function update(int $id, array $data): void
    {
        $stmt = Database::connection()->prepare(
            'UPDATE pages SET title = :title, slug = :slug, content = :content, template = :template,
                    parent_id = :parent_id, status = :status, meta = :meta,
                    meta_title = :meta_title, meta_description = :meta_description, updated_at = NOW()
             WHERE id = :id'
        );
        $stmt->execute(array_merge(self::params($data), ['id' => $id]));
    }

    private static function params(array $data): array
    {
        return [
            'title'            => $data['title'],
            'slug'             => $data['slug'],
            'content'          => $data['content'] ?? '',
            'template'         => $data['template'] ?? 'default',
            'parent_id'        => $data['parent_id'] ?: null,
            'status'           => $data['status'] ?? 'draft',
            'meta'             => json_encode($data['meta'] ?? [], JSON_UNESCAPED_UNICODE),
            'meta_title'       => $data['meta_title'] ?? null,
            'meta_description' => $data['meta_description'] ?? null,
        ];
    }

    public static function delete(int $id): void
    {
        $stmt = Database::connection()->prepare('DELETE FROM pages WHERE id = :id');
        $stmt->execute(['id' => $id]);
    }

    public static function slugExists(string $slug, ?int $excludeId = null): bool
    {
        $sql = 'SELECT COUNT(*) FROM pages WHERE slug = :slug';
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
