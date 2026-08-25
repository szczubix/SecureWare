<?php

namespace SecureWare\Models;

use PDO;
use SecureWare\Core\Database;

class ActivityLog
{
    /**
     * @return array{items: array, total: int}
     */
    public static function paginate(int $page = 1, int $perPage = 40): array
    {
        $total = (int) Database::connection()->query('SELECT COUNT(*) FROM activity_log')->fetchColumn();

        $offset = max(0, ($page - 1) * $perPage);
        $stmt = Database::connection()->prepare(
            'SELECT l.*, u.name AS user_name FROM activity_log l
             LEFT JOIN users u ON u.id = l.user_id
             ORDER BY l.created_at DESC LIMIT :limit OFFSET :offset'
        );
        $stmt->bindValue('limit', $perPage, PDO::PARAM_INT);
        $stmt->bindValue('offset', $offset, PDO::PARAM_INT);
        $stmt->execute();

        return ['items' => $stmt->fetchAll(), 'total' => $total];
    }
}
