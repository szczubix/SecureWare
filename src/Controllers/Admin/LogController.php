<?php

namespace SecureWare\Controllers\Admin;

use SecureWare\Core\Auth;
use SecureWare\Core\Request;
use SecureWare\Core\View;
use SecureWare\Models\ActivityLog;

class LogController
{
    public function index(Request $request): void
    {
        Auth::requirePermission('logs.view');

        $page = max(1, (int) $request->input('page', 1));
        $result = ActivityLog::paginate($page);

        echo View::render('admin/logs/index', [
            'logs'    => $result['items'],
            'total'   => $result['total'],
            'page'    => $page,
            'perPage' => 40,
        ], 'admin/layout');
    }
}
