<?php

/**
 * Instalator webowy - alternatywa dla "php database/seed.php" na hostingu
 * bez dostępu SSH. Importuje schemat bazy i seeduje dane początkowe.
 *
 * Po zakończonej instalacji USUŃ TEN PLIK (przycisk na dole strony robi to
 * automatycznie) - dopóki tu leży, każdy zna jego adres i może go otworzyć,
 * a strona z hasłem administratora nie powinna zostać dostępna dla nikogo
 * poza Tobą.
 */

declare(strict_types=1);

define('ROOT_PATH', __DIR__);
define('VIEWS_PATH', ROOT_PATH . '/views');

spl_autoload_register(function (string $class): void {
    $prefix = 'SecureWare\\';
    if (!str_starts_with($class, $prefix)) {
        return;
    }
    $path = ROOT_PATH . '/src/' . str_replace('\\', '/', substr($class, strlen($prefix))) . '.php';
    if (is_file($path)) {
        require $path;
    }
});

use SecureWare\Core\Config;
use SecureWare\Core\Csrf;
use SecureWare\Core\Installer;
use SecureWare\Core\Session;

Config::load(require ROOT_PATH . '/config/config.php');
Session::start();

$adminUrl        = '/' . Config::get('admin_path');
$error           = null;
$result          = null;
$deleted         = false;
$deleteAttempted = false;

if ($_SERVER['REQUEST_METHOD'] === 'POST' && ($_POST['action'] ?? '') === 'delete_self') {
    $deleteAttempted = true;
    if (Csrf::verify($_POST['_csrf'] ?? null)) {
        $deleted = @unlink(__FILE__);
    }
} elseif ($_SERVER['REQUEST_METHOD'] === 'POST' && ($_POST['action'] ?? '') === 'install') {
    if (!Csrf::verify($_POST['_csrf'] ?? null)) {
        $error = 'Sesja wygasła. Odśwież stronę i spróbuj ponownie.';
    } elseif (Installer::isInstalled()) {
        $error = 'Aplikacja jest już zainstalowana.';
    } else {
        try {
            $log = Installer::migrateSchema();
            $seedResult = Installer::seed();
            $result = ['log' => array_merge($log, $seedResult['log']), 'admin' => $seedResult['admin']];
        } catch (\Throwable $e) {
            $error = 'Instalacja nie powiodła się: ' . $e->getMessage()
                . ' Sprawdź dane połączenia z bazą w pliku .env.';
        }
    }
}

$deleteFailed     = $deleteAttempted && !$deleted;
$alreadyInstalled = !$deleted && !$deleteFailed && !$result && Installer::isInstalled();
?><!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Instalacja - SecureWare</title>
<link rel="icon" href="/assets/img/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/assets/css/admin.css">
</head>
<body class="admin admin-login-page">
    <div class="login-card" style="width:520px;">
        <div class="login-card__brand">SecureWare<span>instalator</span></div>

        <?php if ($deleteFailed): ?>
            <p class="alert alert--error">
                Nie udało się automatycznie usunąć install.php (serwer PHP nie ma prawa zapisu
                do tego katalogu). Skasuj plik <strong>ręcznie</strong> przez File Manager w
                DirectAdmin - to ważne ze względów bezpieczeństwa.
            </p>
        <?php endif; ?>

        <?php if ($deleted): ?>
            <p class="alert alert--success">Plik install.php został usunięty z serwera. Instalacja zakończona.</p>
            <a href="<?= htmlspecialchars($adminUrl, ENT_QUOTES, 'UTF-8') ?>/login" class="button">Przejdź do logowania</a>

        <?php elseif ($result): ?>
            <p class="alert alert--success">Instalacja zakończona powodzeniem.</p>
            <ul style="margin:0 0 16px;padding-left:18px;font-size:13.5px;color:var(--sw-muted);">
                <?php foreach ($result['log'] as $line): ?>
                    <li><?= htmlspecialchars($line, ENT_QUOTES, 'UTF-8') ?></li>
                <?php endforeach; ?>
            </ul>

            <?php if ($result['admin']): ?>
                <div class="alert alert--error" style="color:#101828;background:#fffaeb;border-color:#fec84b;">
                    <strong>Zapisz te dane - pokazywane tylko raz:</strong><br>
                    Adres: <?= htmlspecialchars($adminUrl, ENT_QUOTES, 'UTF-8') ?>/login<br>
                    E-mail: <strong><?= htmlspecialchars($result['admin']['email'], ENT_QUOTES, 'UTF-8') ?></strong><br>
                    Hasło: <strong><?= htmlspecialchars($result['admin']['password'], ENT_QUOTES, 'UTF-8') ?></strong><br>
                    Zmień hasło od razu po pierwszym zalogowaniu.
                </div>
            <?php endif; ?>

            <p class="alert alert--error">
                Ze względów bezpieczeństwa usuń teraz ten plik (install.php) z serwera -
                dopóki tu leży, każdy może pod niego wejść.
            </p>
            <form method="post" action="" onsubmit="return confirm('Usunąć install.php? Tej operacji nie można cofnąć.');">
                <?= Csrf::field() ?>
                <input type="hidden" name="action" value="delete_self">
                <button type="submit" class="button button--danger" style="width:100%;">Usuń install.php teraz</button>
            </form>
            <p class="hint" style="margin-top:10px;">Nie da się usunąć automatycznie? Skasuj plik ręcznie przez File Manager w DirectAdmin.</p>

        <?php elseif ($alreadyInstalled): ?>
            <p class="alert alert--success">Aplikacja jest już zainstalowana.</p>
            <p>Jeśli to nie Ty ostatnio instalowałeś - zmień hasło administratora i sprawdź użytkowników w panelu.</p>
            <a href="<?= htmlspecialchars($adminUrl, ENT_QUOTES, 'UTF-8') ?>/login" class="button">Przejdź do logowania</a>
            <form method="post" action="" style="margin-top:14px;" onsubmit="return confirm('Usunąć install.php? Tej operacji nie można cofnąć.');">
                <?= Csrf::field() ?>
                <input type="hidden" name="action" value="delete_self">
                <button type="submit" class="button button--ghost" style="width:100%;">Usuń install.php</button>
            </form>

        <?php else: ?>
            <?php if ($error): ?><p class="alert alert--error"><?= htmlspecialchars($error, ENT_QUOTES, 'UTF-8') ?></p><?php endif; ?>
            <p>Ten instalator:</p>
            <ul style="margin:0 0 16px;padding-left:18px;font-size:14px;">
                <li>zaimportuje schemat bazy danych z <code>database/schema.sql</code>,</li>
                <li>utworzy role, uprawnienia i pierwsze konto administratora panelu,</li>
                <li>doda domyślne ustawienia oraz przykładową treść (13 usług, strony, wpisy na blogu).</li>
            </ul>
            <p class="hint">Upewnij się, że plik <code>.env</code> ma już poprawne dane połączenia z bazą danych.</p>
            <form method="post" action="">
                <?= Csrf::field() ?>
                <input type="hidden" name="action" value="install">
                <button type="submit" class="button" style="width:100%;">Zainstaluj</button>
            </form>
        <?php endif; ?>
    </div>
</body>
</html>
