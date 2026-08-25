<?php

namespace SecureWare\Models;

use SecureWare\Core\Database;

class Role
{
    public static function all(): array
    {
        return Database::connection()->query('SELECT * FROM roles ORDER BY id')->fetchAll();
    }

    public static function find(int $id): ?array
    {
        $stmt = Database::connection()->prepare('SELECT * FROM roles WHERE id = :id');
        $stmt->execute(['id' => $id]);
        return $stmt->fetch() ?: null;
    }

    public static function create(string $name, string $slug): int
    {
        $stmt = Database::connection()->prepare('INSERT INTO roles (name, slug) VALUES (:name, :slug)');
        $stmt->execute(['name' => $name, 'slug' => $slug]);
        return (int) Database::connection()->lastInsertId();
    }

    public static function update(int $id, string $name, string $slug): void
    {
        $stmt = Database::connection()->prepare('UPDATE roles SET name = :name, slug = :slug WHERE id = :id');
        $stmt->execute(['name' => $name, 'slug' => $slug, 'id' => $id]);
    }

    public static function delete(int $id): void
    {
        $stmt = Database::connection()->prepare('DELETE FROM roles WHERE id = :id');
        $stmt->execute(['id' => $id]);
    }

    public static function isInUse(int $id): bool
    {
        $stmt = Database::connection()->prepare('SELECT COUNT(*) FROM users WHERE role_id = :id');
        $stmt->execute(['id' => $id]);
        return (int) $stmt->fetchColumn() > 0;
    }

    public static function setPermissions(int $roleId, array $permissionIds): void
    {
        $pdo = Database::connection();
        $pdo->prepare('DELETE FROM role_permissions WHERE role_id = :role_id')->execute(['role_id' => $roleId]);

        if (!$permissionIds) {
            return;
        }

        $stmt = $pdo->prepare('INSERT INTO role_permissions (role_id, permission_id) VALUES (:role_id, :permission_id)');
        foreach ($permissionIds as $permissionId) {
            $stmt->execute(['role_id' => $roleId, 'permission_id' => (int) $permissionId]);
        }
    }

    public static function permissionIds(int $roleId): array
    {
        $stmt = Database::connection()->prepare('SELECT permission_id FROM role_permissions WHERE role_id = :role_id');
        $stmt->execute(['role_id' => $roleId]);
        return array_map('intval', $stmt->fetchAll(\PDO::FETCH_COLUMN));
    }
}
