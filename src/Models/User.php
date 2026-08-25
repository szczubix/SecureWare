<?php

namespace SecureWare\Models;

use SecureWare\Core\Database;

class User
{
    public static function find(int $id): ?array
    {
        $stmt = Database::connection()->prepare(
            'SELECT u.*, r.name AS role_name, r.slug AS role_slug
             FROM users u JOIN roles r ON r.id = u.role_id
             WHERE u.id = :id'
        );
        $stmt->execute(['id' => $id]);
        return $stmt->fetch() ?: null;
    }

    public static function findByEmail(string $email): ?array
    {
        $stmt = Database::connection()->prepare('SELECT * FROM users WHERE email = :email');
        $stmt->execute(['email' => $email]);
        return $stmt->fetch() ?: null;
    }

    public static function all(): array
    {
        return Database::connection()->query(
            'SELECT u.*, r.name AS role_name FROM users u JOIN roles r ON r.id = u.role_id ORDER BY u.name'
        )->fetchAll();
    }

    public static function create(string $name, string $email, string $password, int $roleId, string $status = 'active'): int
    {
        $stmt = Database::connection()->prepare(
            'INSERT INTO users (name, email, password_hash, role_id, status, created_at)
             VALUES (:name, :email, :password_hash, :role_id, :status, NOW())'
        );
        $stmt->execute([
            'name'          => $name,
            'email'         => $email,
            'password_hash' => password_hash($password, PASSWORD_DEFAULT),
            'role_id'       => $roleId,
            'status'        => $status,
        ]);

        return (int) Database::connection()->lastInsertId();
    }

    public static function update(int $id, string $name, string $email, int $roleId, string $status, ?string $password = null): void
    {
        $sql = 'UPDATE users SET name = :name, email = :email, role_id = :role_id, status = :status';
        $params = ['name' => $name, 'email' => $email, 'role_id' => $roleId, 'status' => $status, 'id' => $id];

        if ($password) {
            $sql .= ', password_hash = :password_hash';
            $params['password_hash'] = password_hash($password, PASSWORD_DEFAULT);
        }

        $sql .= ' WHERE id = :id';

        $stmt = Database::connection()->prepare($sql);
        $stmt->execute($params);
    }

    public static function delete(int $id): void
    {
        $stmt = Database::connection()->prepare('DELETE FROM users WHERE id = :id');
        $stmt->execute(['id' => $id]);
    }

    public static function touchLogin(int $id): void
    {
        $stmt = Database::connection()->prepare('UPDATE users SET last_login_at = NOW() WHERE id = :id');
        $stmt->execute(['id' => $id]);
    }

    /**
     * @return string[]
     */
    public static function permissionsForRole(int $roleId): array
    {
        $stmt = Database::connection()->prepare(
            'SELECT p.key FROM permissions p
             JOIN role_permissions rp ON rp.permission_id = p.id
             WHERE rp.role_id = :role_id'
        );
        $stmt->execute(['role_id' => $roleId]);
        return $stmt->fetchAll(\PDO::FETCH_COLUMN);
    }
}
