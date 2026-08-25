<?php

namespace SecureWare\Controllers\Admin;

use SecureWare\Core\Auth;
use SecureWare\Core\Config;
use SecureWare\Core\Csrf;
use SecureWare\Core\Logger;
use SecureWare\Core\Request;
use SecureWare\Core\Response;
use SecureWare\Core\View;
use SecureWare\Models\Lead;

class LeadController
{
    public function index(Request $request): void
    {
        Auth::requirePermission('leads.view');

        echo View::render('admin/leads/index', ['leads' => Lead::all()], 'admin/layout');
    }

    public function updateStatus(Request $request, string $id): void
    {
        Auth::requirePermission('leads.edit');

        if (Csrf::verify($request->input('_csrf'))) {
            $status = $request->input('status', 'new');
            if (in_array($status, ['new', 'contacted', 'closed'], true)) {
                Lead::setStatus((int) $id, $status);
                Logger::record('update', 'lead', (int) $id);
            }
        }

        Response::redirect('/' . Config::get('admin_path') . '/leads');
    }
}
