<?php
/** @var string $content */
use SecureWare\Core\Auth;
use SecureWare\Core\Config;
use SecureWare\Core\Csrf;
use SecureWare\Core\Icons;
use SecureWare\Core\View;

$adminUrl    = '/' . Config::get('admin_path');
$user        = Auth::user();
$currentPath = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH) ?: '/';

$isActive = function (string $href) use ($currentPath, $adminUrl): bool {
    if ($href === $adminUrl) {
        return $currentPath === $adminUrl || $currentPath === $adminUrl . '/';
    }
    return str_starts_with($currentPath, $href);
};
?><!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Panel administracyjny · SecureWare</title>
<link rel="icon" href="/assets/img/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/css/admin.css?v=<?= @filemtime(ROOT_PATH . '/assets/css/admin.css') ?: '1' ?>">
</head>
<body class="admin">
<?php if ($user): ?>
<div class="admin-shell">
    <aside class="admin-sidebar">
        <div class="admin-sidebar__brand"><?= Icons::svg('shield-check', 20) ?> SecureWare<span>panel</span></div>
        <nav class="admin-nav">
            <?php if (Auth::can('dashboard.view')): ?><a href="<?= $adminUrl ?>" class="<?= $isActive($adminUrl) && $currentPath === $adminUrl ? 'is-active' : '' ?>"><?= Icons::svg('grid', 17) ?> Pulpit</a><?php endif; ?>
            <?php if (Auth::can('articles.view')): ?><a href="<?= $adminUrl ?>/articles" class="<?= $isActive("$adminUrl/articles") ? 'is-active' : '' ?>"><?= Icons::svg('file-check', 17) ?> Artykuly (blog)</a><?php endif; ?>
            <?php if (Auth::can('pages.view')): ?><a href="<?= $adminUrl ?>/pages" class="<?= $isActive("$adminUrl/pages") ? 'is-active' : '' ?>"><?= Icons::svg('layers', 17) ?> Podstrony</a><?php endif; ?>
            <?php if (Auth::can('services.view')): ?><a href="<?= $adminUrl ?>/services" class="<?= $isActive("$adminUrl/services") ? 'is-active' : '' ?>"><?= Icons::svg('server', 17) ?> Oferta (uslugi)</a><?php endif; ?>
            <?php if (Auth::can('media.view')): ?><a href="<?= $adminUrl ?>/media" class="<?= $isActive("$adminUrl/media") ? 'is-active' : '' ?>"><?= Icons::svg('image', 17) ?> Biblioteka mediow</a><?php endif; ?>
            <?php if (Auth::can('leads.view')): ?><a href="<?= $adminUrl ?>/leads" class="<?= $isActive("$adminUrl/leads") ? 'is-active' : '' ?>"><?= Icons::svg('inbox', 17) ?> Zapytania</a><?php endif; ?>
            <?php if (Auth::can('users.view')): ?><a href="<?= $adminUrl ?>/users" class="<?= $isActive("$adminUrl/users") ? 'is-active' : '' ?>"><?= Icons::svg('users', 17) ?> Uzytkownicy</a><?php endif; ?>
            <?php if (Auth::can('roles.view')): ?><a href="<?= $adminUrl ?>/roles" class="<?= $isActive("$adminUrl/roles") ? 'is-active' : '' ?>"><?= Icons::svg('shield', 17) ?> Role i uprawnienia</a><?php endif; ?>
            <?php if (Auth::can('settings.edit')): ?>
                <a href="<?= $adminUrl ?>/settings/branding" class="<?= $isActive("$adminUrl/settings/branding") ? 'is-active' : '' ?>"><?= Icons::svg('sliders', 17) ?> Branding</a>
                <a href="<?= $adminUrl ?>/settings/integrations" class="<?= $isActive("$adminUrl/settings/integrations") ? 'is-active' : '' ?>"><?= Icons::svg('plug', 17) ?> Integracje</a>
            <?php endif; ?>
            <?php if (Auth::can('logs.view')): ?><a href="<?= $adminUrl ?>/logs" class="<?= $isActive("$adminUrl/logs") ? 'is-active' : '' ?>"><?= Icons::svg('list', 17) ?> Logi aktywnosci</a><?php endif; ?>
        </nav>
    </aside>
    <div class="admin-main">
        <header class="admin-topbar">
            <div></div>
            <div class="admin-topbar__user">
                <span class="admin-topbar__avatar"><?= strtoupper(substr($user['name'], 0, 1)) ?></span>
                <span><?= View::e($user['name']) ?> <em><?= View::e($user['role_name']) ?></em></span>
                <form method="post" action="<?= $adminUrl ?>/logout">
                    <?= Csrf::field() ?>
                    <button type="submit" class="link-button" title="Wyloguj"><?= Icons::svg('logout', 17) ?></button>
                </form>
            </div>
        </header>
        <main class="admin-content">
            <?= $content ?>
        </main>
    </div>
</div>
<?php else: ?>
<?= $content ?>
<?php endif; ?>
</body>
</html>
