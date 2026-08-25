<?php

namespace SecureWare\Core;

use SecureWare\Models\User;

class Auth
{
    private const MAX_ATTEMPTS  = 5;
    private const LOCKOUT_MINUTES = 15;

    private static ?array $userCache = null;
    /** @var string[]|null */
    private static ?array $permissionCache = null;

    public static function id(): ?int
    {
        return Session::get('user_id');
    }

    public static function check(): bool
    {
        return self::id() !== null;
    }

    public static function user(): ?array
    {
        if (!self::check()) {
            return null;
        }

        if (self::$userCache === null) {
            self::$userCache = User::find((int) self::id());
        }

        return self::$userCache;
    }

    public static function isLockedOut(string $email, string $ip): bool
    {
        $stmt = Database::connection()->prepare(
            'SELECT COUNT(*) FROM login_attempts
             WHERE (email = :email OR ip = :ip) AND success = 0
               AND created_at > (NOW() - INTERVAL :minutes MINUTE)'
        );
        $stmt->execute(['email' => $email, 'ip' => $ip, 'minutes' => self::LOCKOUT_MINUTES]);

        return (int) $stmt->fetchColumn() >= self::MAX_ATTEMPTS;
    }

    private static function recordAttempt(string $email, string $ip, bool $success): void
    {
        $stmt = Database::connection()->prepare(
            'INSERT INTO login_attempts (email, ip, success, created_at) VALUES (:email, :ip, :success, NOW())'
        );
        $stmt->execute(['email' => $email, 'ip' => $ip, 'success' => $success ? 1 : 0]);
    }

    public static function attempt(string $email, string $password, string $ip): bool|string
    {
        if (self::isLockedOut($email, $ip)) {
            return 'locked';
        }

        $user = User::findByEmail($email);

        if (!$user || $user['status'] !== 'active' || !password_verify($password, $user['password_hash'])) {
            self::recordAttempt($email, $ip, false);
            return false;
        }

        self::recordAttempt($email, $ip, true);

        Session::regenerate();
        Session::set('user_id', $user['id']);
        User::touchLogin((int) $user['id']);

        Logger::record('login', 'user', (int) $user['id'], (int) $user['id']);

        return true;
    }

    public static function logout(): void
    {
        if (self::check()) {
            Logger::record('logout', 'user', self::id(), self::id());
        }

        self::$userCache        = null;
        self::$permissionCache  = null;
        Session::destroy();
    }

    /**
     * @return string[]
     */
    public static function permissions(): array
    {
        if (!self::check()) {
            return [];
        }

        if (self::$permissionCache === null) {
            $user = self::user();
            self::$permissionCache = $user ? User::permissionsForRole((int) $user['role_id']) : [];
        }

        return self::$permissionCache;
    }

    public static function can(string $permission): bool
    {
        return in_array($permission, self::permissions(), true);
    }

    /**
     * Redirects to the admin login page if the user is not authenticated,
     * or aborts with 403 if authenticated but lacking the permission.
     */
    public static function requirePermission(string $permission): void
    {
        $adminPath = Config::get('admin_path');

        if (!self::check()) {
            Response::redirect('/' . $adminPath . '/login');
        }

        if (!self::can($permission)) {
            http_response_code(403);
            echo View::render('admin/403', [], 'admin/layout');
            exit;
        }
    }
}
