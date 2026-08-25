<?php

namespace SecureWare\Core;

class Logger
{
    public static function record(string $action, string $entityType, ?int $entityId = null, ?int $userId = null): void
    {
        $userId ??= Auth::id();

        $stmt = Database::connection()->prepare(
            'INSERT INTO activity_log (user_id, action, entity_type, entity_id, ip, created_at)
             VALUES (:user_id, :action, :entity_type, :entity_id, :ip, NOW())'
        );

        $stmt->execute([
            'user_id'     => $userId,
            'action'      => $action,
            'entity_type' => $entityType,
            'entity_id'   => $entityId,
            'ip'          => $_SERVER['REMOTE_ADDR'] ?? '0.0.0.0',
        ]);
    }
}
