<?php

/**
 * Importuje schemat bazy danych i seeduje role, uprawnienia, pierwszego
 * administratora, domyslne ustawienia oraz przykladowa tresc (13 uslug,
 * strony CMS, wpisy na blogu). Cala logika zyje w src/Core/Installer.php -
 * ten plik to tylko cienki wrapper CLI dla osob z dostepem SSH.
 *
 * Uruchomienie na serwerze (SSH) lub lokalnie:
 *   php database/seed.php
 *
 * Bez dostepu SSH: uzyj install.php w przegladarce (patrz DEPLOY.md) -
 * robi dokladnie to samo.
 *
 * Skrypt jest idempotentny - mozna go uruchomic wielokrotnie bez duplikowania
 * danych; konto administratora jest tworzone tylko raz (przy pierwszym biegu).
 */

declare(strict_types=1);

define('ROOT_PATH', dirname(__DIR__));
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
use SecureWare\Core\Installer;

Config::load(require ROOT_PATH . '/config/config.php');

function out(string $line): void
{
    fwrite(STDOUT, $line . PHP_EOL);
}

foreach (Installer::migrateSchema() as $line) {
    out($line);
}

$result = Installer::seed();
foreach ($result['log'] as $line) {
    out($line);
}

if ($result['admin']) {
    out('====================================================');
    out('Utworzono konto administratora panelu:');
    out('  URL:    /' . Config::get('admin_path') . '/login');
    out('  E-mail: ' . $result['admin']['email']);
    out('  Haslo:  ' . $result['admin']['password']);
    out('Zmien haslo natychmiast po pierwszym logowaniu.');
    out('====================================================');
}

out('Seed zakonczony.');
