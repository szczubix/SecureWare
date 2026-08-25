<?php

namespace SecureWare\Models;

use SecureWare\Core\Database;
use SecureWare\Core\Str;

class Tag
{
    public static function all(): array
    {
        return Database::connection()->query('SELECT * FROM tags ORDER BY name')->fetchAll();
    }

    public static function findBySlug(string $slug): ?array
    {
        $stmt = Database::connection()->prepare('SELECT * FROM tags WHERE slug = :slug');
        $stmt->execute(['slug' => $slug]);
        return $stmt->fetch() ?: null;
    }

    public static function firstOrCreate(string $name): int
    {
        $slug = Str::slug($name);
        $existing = self::findBySlug($slug);
        if ($existing) {
            return (int) $existing['id'];
        }

        $stmt = Database::connection()->prepare('INSERT INTO tags (name, slug) VALUES (:name, :slug)');
        $stmt->execute(['name' => $name, 'slug' => $slug]);
        return (int) Database::connection()->lastInsertId();
    }

    /**
     * Parses a comma-separated tag string into tag IDs, creating tags as needed.
     */
    public static function idsFromString(string $tagsString): array
    {
        $ids = [];
        foreach (explode(',', $tagsString) as $name) {
            $name = trim($name);
            if ($name === '') {
                continue;
            }
            $ids[] = self::firstOrCreate($name);
        }

        return $ids;
    }

    public static function forArticle(int $articleId): array
    {
        $stmt = Database::connection()->prepare(
            'SELECT t.* FROM tags t JOIN article_tag at ON at.tag_id = t.id WHERE at.article_id = :id ORDER BY t.name'
        );
        $stmt->execute(['id' => $articleId]);
        return $stmt->fetchAll();
    }

    public static function syncArticle(int $articleId, array $tagIds): void
    {
        $pdo = Database::connection();
        $pdo->prepare('DELETE FROM article_tag WHERE article_id = :id')->execute(['id' => $articleId]);

        if (!$tagIds) {
            return;
        }

        $stmt = $pdo->prepare('INSERT INTO article_tag (article_id, tag_id) VALUES (:article_id, :tag_id)');
        foreach (array_unique($tagIds) as $tagId) {
            $stmt->execute(['article_id' => $articleId, 'tag_id' => $tagId]);
        }
    }
}
