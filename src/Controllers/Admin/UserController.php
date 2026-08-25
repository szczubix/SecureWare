<?php

namespace SecureWare\Controllers\Admin;

use SecureWare\Core\Auth;
use SecureWare\Core\Config;
use SecureWare\Core\Csrf;
use SecureWare\Core\Logger;
use SecureWare\Core\Request;
use SecureWare\Core\Response;
use SecureWare\Core\View;
use SecureWare\Models\Role;
use SecureWare\Models\User;

class UserController
{
    public function index(Request $request): void
    {
        Auth::requirePermission('users.view');

        echo View::render('admin/users/index', ['users' => User::all()], 'admin/layout');
    }

    public function create(Request $request): void
    {
        Auth::requirePermission('users.edit');

        echo View::render('admin/users/edit', ['editUser' => null, 'roles' => Role::all(), 'error' => null], 'admin/layout');
    }

    public function edit(Request $request, string $id): void
    {
        Auth::requirePermission('users.edit');

        $user = User::find((int) $id);
        if (!$user) {
            Response::notFound();
        }

        echo View::render('admin/users/edit', ['editUser' => $user, 'roles' => Role::all(), 'error' => null], 'admin/layout');
    }

    public function store(Request $request): void
    {
        Auth::requirePermission('users.edit');
        $this->save($request, null);
    }

    public function update(Request $request, string $id): void
    {
        Auth::requirePermission('users.edit');
        $this->save($request, (int) $id);
    }

    private function save(Request $request, ?int $id): void
    {
        if (!Csrf::verify($request->input('_csrf'))) {
            Response::redirect($this->url());
        }

        $name     = trim((string) $request->input('name', ''));
        $email    = trim((string) $request->input('email', ''));
        $roleId   = (int) $request->input('role_id', 0);
        $status   = $request->input('status', 'active') === 'disabled' ? 'disabled' : 'active';
        $password = (string) $request->input('password', '');

        if ($name === '' || !filter_var($email, FILTER_VALIDATE_EMAIL) || !$roleId) {
            echo View::render('admin/users/edit', [
                'editUser' => $id ? User::find($id) : null,
                'roles'    => Role::all(),
                'error'    => 'Podaj poprawne imie, e-mail oraz role.',
            ], 'admin/layout');
            return;
        }

        if ($id === null) {
            if ($password === '') {
                echo View::render('admin/users/edit', [
                    'editUser' => null, 'roles' => Role::all(),
                    'error'    => 'Haslo jest wymagane dla nowego uzytkownika.',
                ], 'admin/layout');
                return;
            }
            $newId = User::create($name, $email, $password, $roleId, $status);
            Logger::record('create', 'user', $newId);
        } else {
            User::update($id, $name, $email, $roleId, $status, $password !== '' ? $password : null);
            Logger::record('update', 'user', $id);
        }

        Response::redirect($this->url());
    }

    public function destroy(Request $request, string $id): void
    {
        Auth::requirePermission('users.delete');

        if (Csrf::verify($request->input('_csrf')) && (int) $id !== Auth::id()) {
            User::delete((int) $id);
            Logger::record('delete', 'user', (int) $id);
        }

        Response::redirect($this->url());
    }

    private function url(): string
    {
        return '/' . Config::get('admin_path') . '/users';
    }
}
