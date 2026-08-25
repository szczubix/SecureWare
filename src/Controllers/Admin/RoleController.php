<?php

namespace SecureWare\Controllers\Admin;

use SecureWare\Core\Auth;
use SecureWare\Core\Config;
use SecureWare\Core\Csrf;
use SecureWare\Core\Logger;
use SecureWare\Core\Request;
use SecureWare\Core\Response;
use SecureWare\Core\Session;
use SecureWare\Core\Str;
use SecureWare\Core\View;
use SecureWare\Models\Permission;
use SecureWare\Models\Role;

class RoleController
{
    public function index(Request $request): void
    {
        Auth::requirePermission('roles.view');

        echo View::render('admin/roles/index', ['roles' => Role::all()], 'admin/layout');
    }

    public function create(Request $request): void
    {
        Auth::requirePermission('roles.edit');

        echo View::render('admin/roles/edit', [
            'role' => null, 'permissions' => Permission::all(), 'assignedIds' => [], 'error' => null,
        ], 'admin/layout');
    }

    public function edit(Request $request, string $id): void
    {
        Auth::requirePermission('roles.edit');

        $role = Role::find((int) $id);
        if (!$role) {
            Response::notFound();
        }

        echo View::render('admin/roles/edit', [
            'role' => $role, 'permissions' => Permission::all(),
            'assignedIds' => Role::permissionIds((int) $id), 'error' => null,
        ], 'admin/layout');
    }

    public function store(Request $request): void
    {
        Auth::requirePermission('roles.edit');
        $this->save($request, null);
    }

    public function update(Request $request, string $id): void
    {
        Auth::requirePermission('roles.edit');
        $this->save($request, (int) $id);
    }

    private function save(Request $request, ?int $id): void
    {
        if (!Csrf::verify($request->input('_csrf'))) {
            Response::redirect($this->url());
        }

        $name = trim((string) $request->input('name', ''));
        $slug = Str::slug((string) $request->input('slug', '') ?: $name);

        if ($name === '' || $slug === '') {
            echo View::render('admin/roles/edit', [
                'role' => $id ? Role::find($id) : null, 'permissions' => Permission::all(),
                'assignedIds' => $id ? Role::permissionIds($id) : [],
                'error' => 'Nazwa roli jest wymagana.',
            ], 'admin/layout');
            return;
        }

        if ($id === null) {
            $id = Role::create($name, $slug);
            Logger::record('create', 'role', $id);
        } else {
            Role::update($id, $name, $slug);
            Logger::record('update', 'role', $id);
        }

        $permissionIds = (array) ($request->all()['permissions'] ?? []);
        Role::setPermissions($id, $permissionIds);

        Response::redirect($this->url());
    }

    public function destroy(Request $request, string $id): void
    {
        Auth::requirePermission('roles.delete');

        if (Csrf::verify($request->input('_csrf'))) {
            if (Role::isInUse((int) $id)) {
                Session::flash('error', 'Nie mozna usunac roli przypisanej do uzytkownikow.');
            } else {
                Role::delete((int) $id);
                Logger::record('delete', 'role', (int) $id);
            }
        }

        Response::redirect($this->url());
    }

    private function url(): string
    {
        return '/' . Config::get('admin_path') . '/roles';
    }
}
