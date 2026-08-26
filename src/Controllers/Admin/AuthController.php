<?php

namespace SecureWare\Controllers\Admin;

use SecureWare\Core\Auth;
use SecureWare\Core\Config;
use SecureWare\Core\Csrf;
use SecureWare\Core\Request;
use SecureWare\Core\Response;
use SecureWare\Core\View;

class AuthController
{
    public function showLogin(Request $request): void
    {
        if (Auth::check()) {
            Response::redirect($this->adminUrl());
        }

        echo View::render('admin/login', ['error' => null]);
    }

    public function login(Request $request): void
    {
        if (!Csrf::verify($request->input('_csrf'))) {
            echo View::render('admin/login', ['error' => 'Sesja wygasła, spróbuj ponownie.']);
            return;
        }

        $email    = $request->input('email', '');
        $password = $request->input('password', '');

        $result = Auth::attempt((string) $email, (string) $password, $request->ip());

        if ($result === 'locked') {
            echo View::render('admin/login', ['error' => 'Zbyt wiele nieudanych prób logowania. Spróbuj ponownie za 15 minut.']);
            return;
        }

        if ($result !== true) {
            echo View::render('admin/login', ['error' => 'Nieprawidłowy e-mail lub hasło.']);
            return;
        }

        Response::redirect($this->adminUrl());
    }

    public function logout(Request $request): void
    {
        if (Csrf::verify($request->input('_csrf'))) {
            Auth::logout();
        }
        Response::redirect($this->adminUrl() . '/login');
    }

    private function adminUrl(): string
    {
        return '/' . Config::get('admin_path');
    }
}
