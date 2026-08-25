<?php

namespace SecureWare\Models;

use SecureWare\Core\Database;

class Media
{
    public static function all(int $limit = 60): array
    {
        $stmt = Database::connection()->prepare('SELECT * FROM media ORDER BY created_at DESC LIMIT :limit');
        $stmt->bindValue('limit', $limit, \PDO::PARAM_INT);
        $stmt->execute();
        return $stmt->fetchAll();
    }

    public static function find(int $id): ?array
    {
        $stmt = Database::connection()->prepare('SELECT * FROM media WHERE id = :id');
        $stmt->execute(['id' => $id]);
        return $stmt->fetch() ?: null;
    }

    public static function create(string $filename, string $path, string $mime, int $size, int $uploadedBy): int
    {
        $stmt = Database::connection()->prepare(
            'INSERT INTO media (filename, path, mime, size, uploaded_by, created_at)
             VALUES (:filename, :path, :mime, :size, :uploaded_by, NOW())'
        );
        $stmt->execute([
            'filename'    => $filename,
            'path'        => $path,
            'mime'        => $mime,
            'size'        => $size,
            'uploaded_by' => $uploadedBy,
        ]);

        return (int) Database::connection()->lastInsertId();
    }

    public static function delete(int $id): ?array
    {
        $media = self::find($id);
        if (!$media) {
            return null;
        }

        $stmt = Database::connection()->prepare('DELETE FROM media WHERE id = :id');
        $stmt->execute(['id' => $id]);

        return $media;
    }
}
