<?php

use SecureWare\Core\Env;

Env::load(ROOT_PATH . '/.env');

return [
    'app' => [
        'env'   => Env::get('APP_ENV', 'production'),
        'debug' => Env::get('APP_DEBUG', false),
        'url'   => rtrim(Env::get('APP_URL', 'http://localhost'), '/'),
    ],

    // Sciezka panelu admina, np. "cloudsecurepanel" -> /cloudsecurepanel/...
    'admin_path' => trim(Env::get('ADMIN_PATH', 'cloudsecurepanel'), '/'),

    'db' => [
        'host'    => Env::get('DB_HOST', 'localhost'),
        'port'    => Env::get('DB_PORT', '3306'),
        'name'    => Env::get('DB_NAME', 'secureware'),
        'user'    => Env::get('DB_USER', 'secureware'),
        'pass'    => Env::get('DB_PASS', ''),
        'charset' => Env::get('DB_CHARSET', 'utf8mb4'),
    ],

    'session' => [
        'name'   => Env::get('SESSION_NAME', 'sw_session'),
        'secure' => Env::get('SESSION_SECURE', true),
    ],
];
