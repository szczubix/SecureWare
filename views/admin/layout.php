<?php
/** @var string $content */
use SecureWare\Core\Auth;
use SecureWare\Core\Config;
use SecureWare\Core\Csrf;
use SecureWare\Core\View;

$adminUrl = '/' . Config::get('admin_path');
$user     = Auth::user();
?><!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Panel administracyjny · SecureWare</title>
<link rel="icon" href="/assets/img/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/assets/css/admin.css">
</head>
<body class="admin">
<?php if ($user): ?>
<div class="admin-shell">
    <aside class="admin-sidebar">
        <div class="admin-sidebar__brand">SecureWare<span>panel</span></div>
        <nav class="admin-nav">
            <?php if (Auth::can('dashboard.view')): ?><a href="<?= $adminUrl ?>">Pulpit</a><?php endif; ?>
            <?php if (Auth::can('articles.view')): ?><a href="<?= $adminUrl ?>/articles">Artykuly (blog)</a><?php endif; ?>
            <?php if (Auth::can('pages.view')): ?><a href="<?= $adminUrl ?>/pages">Podstrony</a><?php endif; ?>
            <?php if (Auth::can('services.view')): ?><a href="<?= $adminUrl ?>/services">Oferta (uslugi)</a><?php endif; ?>
            <?php if (Auth::can('media.view')): ?><a href="<?= $adminUrl ?>/media">Biblioteka mediow</a><?php endif; ?>
            <?php if (Auth::can('leads.view')): ?><a href="<?= $adminUrl ?>/leads">Zapytania</a><?php endif; ?>
            <?php if (Auth::can('users.view')): ?><a href="<?= $adminUrl ?>/users">Uzytkownicy</a><?php endif; ?>
            <?php if (Auth::can('roles.view')): ?><a href="<?= $adminUrl ?>/roles">Role i uprawnienia</a><?php endif; ?>
            <?php if (Auth::can('settings.edit')): ?>
                <a href="<?= $adminUrl ?>/settings/branding">Branding</a>
                <a href="<?= $adminUrl ?>/settings/integrations">Integracje</a>
            <?php endif; ?>
            <?php if (Auth::can('logs.view')): ?><a href="<?= $adminUrl ?>/logs">Logi aktywnosci</a><?php endif; ?>
        </nav>
    </aside>
    <div class="admin-main">
        <header class="admin-topbar">
            <div></div>
            <div class="admin-topbar__user">
                <span><?= View::e($user['name']) ?> · <?= View::e($user['role_name']) ?></span>
                <form method="post" action="<?= $adminUrl ?>/logout">
                    <?= Csrf::field() ?>
                    <button type="submit" class="link-button">Wyloguj</button>
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
