<?php

namespace SecureWare\Models;

use SecureWare\Core\Database;

class Category
{
    public static function all(): array
    {
        return Database::connection()->query('SELECT * FROM categories ORDER BY name')->fetchAll();
    }

    public static function find(int $id): ?array
    {
        $stmt = Database::connection()->prepare('SELECT * FROM categories WHERE id = :id');
        $stmt->execute(['id' => $id]);
        return $stmt->fetch() ?: null;
    }

    public static function findBySlug(string $slug): ?array
    {
        $stmt = Database::connection()->prepare('SELECT * FROM categories WHERE slug = :slug');
        $stmt->execute(['slug' => $slug]);
        return $stmt->fetch() ?: null;
    }

    public static function firstOrCreate(string $name, string $slug): int
    {
        $existing = self::findBySlug($slug);
        if ($existing) {
            return (int) $existing['id'];
        }

        $stmt = Database::connection()->prepare('INSERT INTO categories (name, slug) VALUES (:name, :slug)');
        $stmt->execute(['name' => $name, 'slug' => $slug]);
        return (int) Database::connection()->lastInsertId();
    }
}
