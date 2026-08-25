<?php

namespace SecureWare\Models;

use SecureWare\Core\Database;

class Lead
{
    public static function all(): array
    {
        return Database::connection()->query('SELECT * FROM leads ORDER BY created_at DESC')->fetchAll();
    }

    public static function create(string $name, string $email, ?string $phone, string $message, string $sourcePage): int
    {
        $stmt = Database::connection()->prepare(
            'INSERT INTO leads (name, email, phone, message, source_page, status, created_at)
             VALUES (:name, :email, :phone, :message, :source_page, "new", NOW())'
        );
        $stmt->execute([
            'name'        => $name,
            'email'       => $email,
            'phone'       => $phone,
            'message'     => $message,
            'source_page' => $sourcePage,
        ]);

        return (int) Database::connection()->lastInsertId();
    }

    public static function setStatus(int $id, string $status): void
    {
        $stmt = Database::connection()->prepare('UPDATE leads SET status = :status WHERE id = :id');
        $stmt->execute(['status' => $status, 'id' => $id]);
    }
}
