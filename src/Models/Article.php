<?php

namespace SecureWare\Models;

use PDO;
use SecureWare\Core\Database;

class Article
{
    private const SELECT = 'SELECT a.*, c.name AS category_name, c.slug AS category_slug,
                                    u.name AS author_name, m.path AS featured_image_path
                             FROM articles a
                             LEFT JOIN categories c ON c.id = a.category_id
                             LEFT JOIN users u ON u.id = a.author_id
                             LEFT JOIN media m ON m.id = a.featured_image_id';

    public static function find(int $id): ?array
    {
        $stmt = Database::connection()->prepare(self::SELECT . ' WHERE a.id = :id');
        $stmt->execute(['id' => $id]);
        $article = $stmt->fetch() ?: null;
        if ($article) {
            $article['tags'] = Tag::forArticle($id);
        }
        return $article;
    }

    public static function findBySlug(string $slug): ?array
    {
        $stmt = Database::connection()->prepare(self::SELECT . " WHERE a.slug = :slug AND a.status = 'published'");
        $stmt->execute(['slug' => $slug]);
        $article = $stmt->fetch() ?: null;
        if ($article) {
            $article['tags'] = Tag::forArticle((int) $article['id']);
        }
        return $article;
    }

    public static function allForAdmin(): array
    {
        return Database::connection()
            ->query(self::SELECT . ' ORDER BY a.created_at DESC')
            ->fetchAll();
    }

    /**
     * @return array{items: array, total: int}
     */
    public static function published(int $page = 1, int $perPage = 9, ?string $categorySlug = null, ?string $tagSlug = null): array
    {
        $where  = ["a.status = 'published'", 'a.published_at <= NOW()'];
        $params = [];

        if ($categorySlug) {
            $where[] = 'c.slug = :category_slug';
            $params['category_slug'] = $categorySlug;
        }

        $joinTag = '';
        if ($tagSlug) {
            $joinTag = ' JOIN article_tag at2 ON at2.article_id = a.id JOIN tags t2 ON t2.id = at2.tag_id';
            $where[] = 't2.slug = :tag_slug';
            $params['tag_slug'] = $tagSlug;
        }

        $whereSql = implode(' AND ', $where);

        $countStmt = Database::connection()->prepare(
            "SELECT COUNT(DISTINCT a.id) FROM articles a
             LEFT JOIN categories c ON c.id = a.category_id {$joinTag}
             WHERE {$whereSql}"
        );
        $countStmt->execute($params);
        $total = (int) $countStmt->fetchColumn();

        $offset = max(0, ($page - 1) * $perPage);
        $stmt = Database::connection()->prepare(
            self::SELECT . $joinTag . " WHERE {$whereSql}
             GROUP BY a.id
             ORDER BY a.published_at DESC LIMIT :limit OFFSET :offset"
        );
        foreach ($params as $key => $value) {
            $stmt->bindValue($key, $value);
        }
        $stmt->bindValue('limit', $perPage, PDO::PARAM_INT);
        $stmt->bindValue('offset', $offset, PDO::PARAM_INT);
        $stmt->execute();

        return ['items' => $stmt->fetchAll(), 'total' => $total];
    }

    public static function latest(int $limit = 3): array
    {
        $stmt = Database::connection()->prepare(
            self::SELECT . " WHERE a.status = 'published' AND a.published_at <= NOW()
             ORDER BY a.published_at DESC LIMIT :limit"
        );
        $stmt->bindValue('limit', $limit, PDO::PARAM_INT);
        $stmt->execute();
        return $stmt->fetchAll();
    }

    public static function related(int $articleId, ?int $categoryId, int $limit = 3): array
    {
        $stmt = Database::connection()->prepare(
            self::SELECT . " WHERE a.status = 'published' AND a.id != :id
             AND (:category_id1 IS NULL OR a.category_id = :category_id2)
             ORDER BY a.published_at DESC LIMIT :limit"
        );
        $stmt->bindValue('id', $articleId, PDO::PARAM_INT);
        $stmt->bindValue('category_id1', $categoryId, $categoryId === null ? PDO::PARAM_NULL : PDO::PARAM_INT);
        $stmt->bindValue('category_id2', $categoryId, $categoryId === null ? PDO::PARAM_NULL : PDO::PARAM_INT);
        $stmt->bindValue('limit', $limit, PDO::PARAM_INT);
        $stmt->execute();
        return $stmt->fetchAll();
    }

    public static function create(array $data): int
    {
        $stmt = Database::connection()->prepare(
            'INSERT INTO articles (title, slug, excerpt, content, featured_image_id, category_id, status,
                                    meta_title, meta_description, author_id, published_at, created_at, updated_at)
             VALUES (:title, :slug, :excerpt, :content, :featured_image_id, :category_id, :status,
                     :meta_title, :meta_description, :author_id, :published_at, NOW(), NOW())'
        );
        $stmt->execute(self::params($data));
        return (int) Database::connection()->lastInsertId();
    }

    public static function update(int $id, array $data): void
    {
        $stmt = Database::connection()->prepare(
            'UPDATE articles SET title = :title, slug = :slug, excerpt = :excerpt, content = :content,
                    featured_image_id = :featured_image_id, category_id = :category_id, status = :status,
                    meta_title = :meta_title, meta_description = :meta_description,
                    published_at = :published_at, updated_at = NOW()
             WHERE id = :id'
        );
        $stmt->execute(array_merge(self::params($data), ['id' => $id]));
    }

    private static function params(array $data): array
    {
        return [
            'title'              => $data['title'],
            'slug'               => $data['slug'],
            'excerpt'            => $data['excerpt'] ?? null,
            'content'            => $data['content'] ?? '',
            'featured_image_id'  => $data['featured_image_id'] ?: null,
            'category_id'        => $data['category_id'] ?: null,
            'status'             => $data['status'] ?? 'draft',
            'meta_title'         => $data['meta_title'] ?? null,
            'meta_description'   => $data['meta_description'] ?? null,
            'author_id'          => $data['author_id'] ?? null,
            'published_at'       => $data['published_at'] ?? null,
        ];
    }

    public static function delete(int $id): void
    {
        $stmt = Database::connection()->prepare('DELETE FROM articles WHERE id = :id');
        $stmt->execute(['id' => $id]);
    }

    public static function slugExists(string $slug, ?int $excludeId = null): bool
    {
        $sql = 'SELECT COUNT(*) FROM articles WHERE slug = :slug';
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
