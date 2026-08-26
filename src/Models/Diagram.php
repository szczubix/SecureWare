<?php

namespace SecureWare\Models;

use SecureWare\Core\Database;
use SecureWare\Core\DiagramRenderer;

class Diagram
{
    /**
     * Zamienia znaczniki osadzenia wstawione przez edytor tresci
     * (<div class="sw-diagram-embed" data-diagram="SLUG"></div>) na
     * faktyczny, wyrenderowany SVG diagramu o danym slugu. Nieznany slug
     * jest po prostu pomijany (pusty ciag) - nie psuje reszty tresci.
     */
    public static function embedInto(string $html): string
    {
        if (!str_contains($html, 'sw-diagram-embed')) {
            return $html;
        }

        return (string) preg_replace_callback(
            '/<div class="sw-diagram-embed" data-diagram="([a-z0-9-]+)"[^>]*><\/div>/i',
            static function (array $m): string {
                $diagram = self::findBySlug($m[1]);
                return $diagram ? DiagramRenderer::card($diagram) : '';
            },
            $html
        );
    }

    public static function all(): array
    {
        return array_map([self::class, 'decode'], Database::connection()->query('SELECT * FROM diagrams ORDER BY name')->fetchAll());
    }

    public static function find(int $id): ?array
    {
        $stmt = Database::connection()->prepare('SELECT * FROM diagrams WHERE id = :id');
        $stmt->execute(['id' => $id]);
        $row = $stmt->fetch() ?: null;
        return $row ? self::decode($row) : null;
    }

    public static function findBySlug(string $slug): ?array
    {
        $stmt = Database::connection()->prepare('SELECT * FROM diagrams WHERE slug = :slug');
        $stmt->execute(['slug' => $slug]);
        $row = $stmt->fetch() ?: null;
        return $row ? self::decode($row) : null;
    }

    private static function decode(array $diagram): array
    {
        $diagram['nodes'] = json_decode($diagram['nodes'] ?? '[]', true) ?: [];
        $diagram['edges'] = json_decode($diagram['edges'] ?? '[]', true) ?: [];
        return $diagram;
    }

    public static function create(array $data): int
    {
        $stmt = Database::connection()->prepare(
            'INSERT INTO diagrams (name, slug, title, badge, foot, canvas_width, canvas_height, nodes, edges, created_by, created_at, updated_at)
             VALUES (:name, :slug, :title, :badge, :foot, :canvas_width, :canvas_height, :nodes, :edges, :created_by, NOW(), NOW())'
        );
        $stmt->execute(self::params($data));
        return (int) Database::connection()->lastInsertId();
    }

    public static function update(int $id, array $data): void
    {
        $stmt = Database::connection()->prepare(
            'UPDATE diagrams SET name = :name, slug = :slug, title = :title, badge = :badge, foot = :foot,
                    canvas_width = :canvas_width, canvas_height = :canvas_height, nodes = :nodes, edges = :edges, updated_at = NOW()
             WHERE id = :id'
        );
        $params = self::params($data);
        unset($params['created_by']);
        $stmt->execute(array_merge($params, ['id' => $id]));
    }

    private static function params(array $data): array
    {
        return [
            'name'          => $data['name'],
            'slug'          => $data['slug'],
            'title'         => $data['title'] ?? '',
            'badge'         => $data['badge'] ?? '',
            'foot'          => $data['foot'] ?? '',
            'canvas_width'  => (int) ($data['canvas_width'] ?? 480),
            'canvas_height' => (int) ($data['canvas_height'] ?? 380),
            'nodes'         => json_encode($data['nodes'] ?? [], JSON_UNESCAPED_UNICODE),
            'edges'         => json_encode($data['edges'] ?? [], JSON_UNESCAPED_UNICODE),
            'created_by'    => $data['created_by'] ?? null,
        ];
    }

    public static function delete(int $id): void
    {
        $stmt = Database::connection()->prepare('DELETE FROM diagrams WHERE id = :id');
        $stmt->execute(['id' => $id]);
    }

    public static function slugExists(string $slug, ?int $excludeId = null): bool
    {
        $sql = 'SELECT COUNT(*) FROM diagrams WHERE slug = :slug';
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
