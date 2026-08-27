<?php

/**
 * Narzędzie do jednorazowego odświeżenia domyślnej treści (usługi, strony
 * CMS, wpisy na blogu, etykiety uprawnień, nazwy ról, kilka tekstów w
 * ustawieniach) aktualną wersją z kodu - przydatne, gdy strona została
 * zainstalowana zanim poprawiono literówki/polskie znaki w domyślnej
 * treści. Seed przy zwykłej instalacji nie nadpisuje istniejących
 * wierszy (żeby nie kasować ręcznych edycji), więc to narzędzie robi to
 * świadomie, na żądanie zalogowanego administratora.
 *
 * Uruchamia też Installer::migrateSchema() (CREATE TABLE IF NOT EXISTS),
 * więc importuje też nowe tabele dodane w kodzie po pierwszej instalacji
 * (np. tabelę "diagrams" dla kreatora diagramów) bez ruszania istniejących
 * danych, oraz Installer::seedTranslations() (angielskie tłumaczenia
 * domyślnej treści z database/seed-data/translations-en.php).
 *
 * Usługi i strony CMS: istniejące (dopasowane po slug) są nadpisywane
 * aktualną treścią z kodu; usługi/strony, których jeszcze nie ma (nowe
 * pozycje dopisane w kodzie po pierwszej instalacji, np. nowa usługa w
 * ofercie albo nowa strona), zostają dodane. Nie rusza leadów ani
 * użytkowników. Nadpisuje tagline i tekst stopki w Ustawieniach - jeśli
 * już ręcznie zmieniłeś te dwa pola, zapisz ich obecną treść przed
 * uruchomieniem. Uwaga: treść strony głównej (Ustawienia -> Strona
 * główna) NIE jest tu ruszana - jeśli dodano nową usługę, licznik typu
 * "13 usług" w tej treści trzeba poprawić ręcznie w panelu.
 *
 * Ten plik NIE usuwa się sam (w przeciwieństwie do install.php) - można
 * go uruchomić ponownie w przyszłości. Jeśli wolisz, żeby nie leżał na
 * serwerze między użyciami, usuń go ręcznie po zastosowaniu poprawek.
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

use SecureWare\Core\Auth;
use SecureWare\Core\Config;
use SecureWare\Core\Csrf;
use SecureWare\Core\Installer;
use SecureWare\Core\Session;

Config::load(require ROOT_PATH . '/config/config.php');
Session::start();

$adminUrl = '/' . Config::get('admin_path');

if (!Auth::check()) {
    header('Location: ' . $adminUrl . '/login');
    exit;
}
if (!Auth::can('settings.edit')) {
    http_response_code(403);
    echo 'Brak uprawnień.';
    exit;
}

$log   = null;
$error = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    if (!Csrf::verify($_POST['_csrf'] ?? null)) {
        $error = 'Sesja wygasła. Odśwież stronę i spróbuj ponownie.';
    } else {
        try {
            $log = array_merge(
                Installer::migrateSchema(),
                Installer::syncPermissions(),
                Installer::refreshDefaultContent(),
                Installer::seedTranslations()
            );
        } catch (\Throwable $e) {
            $error = 'Odświeżenie treści nie powiodło się: ' . $e->getMessage();
        }
    }
}
?><!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Odświeżenie treści - SecureWare</title>
<link rel="icon" href="/assets/img/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/assets/css/admin.css?v=<?= @filemtime(ROOT_PATH . '/assets/css/admin.css') ?: '1' ?>">
</head>
<body class="admin admin-login-page">
    <div class="login-card" style="width:560px;">
        <div class="login-card__brand">SecureWare<span>odświeżenie treści</span></div>

        <?php if ($error): ?><p class="alert alert--error"><?= htmlspecialchars($error, ENT_QUOTES, 'UTF-8') ?></p><?php endif; ?>

        <?php if ($log): ?>
            <p class="alert alert--success">Gotowe.</p>
            <ul style="margin:0 0 16px;padding-left:18px;font-size:13.5px;color:var(--sw-muted);">
                <?php foreach ($log as $line): ?>
                    <li><?= htmlspecialchars($line, ENT_QUOTES, 'UTF-8') ?></li>
                <?php endforeach; ?>
            </ul>
            <a href="<?= htmlspecialchars($adminUrl, ENT_QUOTES, 'UTF-8') ?>" class="button">Wróć do panelu</a>
        <?php else: ?>
            <p>To narzędzie nadpisze bieżącą treść domyślnych usług, stron CMS i
            wpisów na blogu (dopasowanych po adresie URL / slug) aktualną wersją
            z kodu, wraz z etykietami uprawnień, nazwami ról, nazwą kategorii
            bloga oraz tagline'em i tekstem stopki w Ustawieniach. Usługi i strony,
            których jeszcze nie masz (nowe pozycje dodane w kodzie od ostatniego
            odświeżenia), zostaną dodane.</p>
            <p class="hint">Jeśli ręcznie edytowałeś którąś z domyślnych usług, stron CMS,
            wpisów na blogu, tagline lub stopkę w panelu - te zmiany zostaną
            nadpisane. Wpisy dodane przez Ciebie w panelu pod innym adresem/slugiem
            nie zostaną ruszone.</p>
            <form method="post" action="" onsubmit="return confirm('Nadpisać domyślną treść aktualną wersją z kodu?');">
                <?= Csrf::field() ?>
                <button type="submit" class="button" style="width:100%;">Odśwież treść</button>
            </form>
        <?php endif; ?>
    </div>
</body>
</html>
