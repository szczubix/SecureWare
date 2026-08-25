<?php

namespace SecureWare\Controllers\Admin;

use SecureWare\Core\Auth;
use SecureWare\Core\Database;
use SecureWare\Core\Request;
use SecureWare\Core\View;

class DashboardController
{
    public function index(Request $request): void
    {
        Auth::requirePermission('dashboard.view');

        $pdo = Database::connection();
        $stats = [
            'articles' => (int) $pdo->query('SELECT COUNT(*) FROM articles')->fetchColumn(),
            'pages'    => (int) $pdo->query('SELECT COUNT(*) FROM pages')->fetchColumn(),
            'services' => (int) $pdo->query('SELECT COUNT(*) FROM services')->fetchColumn(),
            'leads_new'=> (int) $pdo->query("SELECT COUNT(*) FROM leads WHERE status = 'new'")->fetchColumn(),
        ];

        echo View::render('admin/dashboard', ['stats' => $stats], 'admin/layout');
    }
}
