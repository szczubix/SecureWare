<?php

namespace SecureWare\Models;

use SecureWare\Core\Database;

class Permission
{
    public static function all(): array
    {
        return Database::connection()->query('SELECT * FROM permissions ORDER BY `key`')->fetchAll();
    }
}
