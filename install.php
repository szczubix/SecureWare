<?php

/**
 * Instalator webowy - alternatywa dla "php database/seed.php" na hostingu
 * bez dostepu SSH. Importuje schemat bazy i seeduje dane poczatkowe.
 *
 * Po zakonczonej instalacji USUN TEN PLIK (przycisk na dole strony robi to
 * automatycznie) - dopoki tu lezy, kazdy zna jego adres i moze go otworzyc,
 * a strona z haslem administratora nie powinna zostac dostepna dla nikogo
 * poza Toba.
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
        $error = 'Sesja wygasla. Odswiez strone i sprobuj ponownie.';
    } elseif (Installer::isInstalled()) {
        $error = 'Aplikacja jest juz zainstalowana.';
    } else {
        try {
            $log = Installer::migrateSchema();
            $seedResult = Installer::seed();
            $result = ['log' => array_merge($log, $seedResult['log']), 'admin' => $seedResult['admin']];
        } catch (\Throwable $e) {
            $error = 'Instalacja nie powiodla sie: ' . $e->getMessage()
                . ' Sprawdz dane polaczenia z baza w pliku .env.';
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
                Nie udalo sie automatycznie usunac install.php (serwer PHP nie ma prawa zapisu
                do tego katalogu). Skasuj plik <strong>recznie</strong> przez File Manager w
                DirectAdmin - to wazne ze wzgledow bezpieczenstwa.
            </p>
        <?php endif; ?>

        <?php if ($deleted): ?>
            <p class="alert alert--success">Plik install.php zostal usuniety z serwera. Instalacja zakonczona.</p>
            <a href="<?= htmlspecialchars($adminUrl, ENT_QUOTES, 'UTF-8') ?>/login" class="button">Przejdz do logowania</a>

        <?php elseif ($result): ?>
            <p class="alert alert--success">Instalacja zakonczona powodzeniem.</p>
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
                    Haslo: <strong><?= htmlspecialchars($result['admin']['password'], ENT_QUOTES, 'UTF-8') ?></strong><br>
                    Zmien haslo od razu po pierwszym zalogowaniu.
                </div>
            <?php endif; ?>

            <p class="alert alert--error">
                Ze wzgledow bezpieczenstwa usun teraz ten plik (install.php) z serwera -
                dopoki tu lezy, kazdy moze pod niego wejsc.
            </p>
            <form method="post" action="" onsubmit="return confirm('Usunac install.php? Tej operacji nie mozna cofnac.');">
                <?= Csrf::field() ?>
                <input type="hidden" name="action" value="delete_self">
                <button type="submit" class="button button--danger" style="width:100%;">Usun install.php teraz</button>
            </form>
            <p class="hint" style="margin-top:10px;">Nie da sie usunac automatycznie? Skasuj plik recznie przez File Manager w DirectAdmin.</p>

        <?php elseif ($alreadyInstalled): ?>
            <p class="alert alert--success">Aplikacja jest juz zainstalowana.</p>
            <p>Jesli to nie Ty ostatnio instalowales - zmien haslo administratora i sprawdz uzytkownikow w panelu.</p>
            <a href="<?= htmlspecialchars($adminUrl, ENT_QUOTES, 'UTF-8') ?>/login" class="button">Przejdz do logowania</a>
            <form method="post" action="" style="margin-top:14px;" onsubmit="return confirm('Usunac install.php? Tej operacji nie mozna cofnac.');">
                <?= Csrf::field() ?>
                <input type="hidden" name="action" value="delete_self">
                <button type="submit" class="button button--ghost" style="width:100%;">Usun install.php</button>
            </form>

        <?php else: ?>
            <?php if ($error): ?><p class="alert alert--error"><?= htmlspecialchars($error, ENT_QUOTES, 'UTF-8') ?></p><?php endif; ?>
            <p>Ten instalator:</p>
            <ul style="margin:0 0 16px;padding-left:18px;font-size:14px;">
                <li>zaimportuje schemat bazy danych z <code>database/schema.sql</code>,</li>
                <li>utworzy role, uprawnienia i pierwsze konto administratora panelu,</li>
                <li>doda domyslne ustawienia oraz przykladowa tresc (13 uslug, strony, wpisy na blogu).</li>
            </ul>
            <p class="hint">Upewnij sie, ze plik <code>.env</code> ma juz poprawne dane polaczenia z baza danych.</p>
            <form method="post" action="">
                <?= Csrf::field() ?>
                <input type="hidden" name="action" value="install">
                <button type="submit" class="button" style="width:100%;">Zainstaluj</button>
            </form>
        <?php endif; ?>
    </div>
</body>
</html>
