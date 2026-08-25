<?php

/**
 * Seeduje role, uprawnienia, domyslne ustawienia, pierwszego administratora
 * oraz przykladowa tresc (13 uslug, strony CMS, wpisy na blogu).
 *
 * Uruchomienie na serwerze (SSH) lub lokalnie:
 *   php database/seed.php
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
use SecureWare\Core\Database;
use SecureWare\Core\Str;

Config::load(require ROOT_PATH . '/config/config.php');
$pdo = Database::connection();

function out(string $line): void
{
    fwrite(STDOUT, $line . PHP_EOL);
}

// ---------------------------------------------------------------------
// 1. Uprawnienia
// ---------------------------------------------------------------------
$permissions = [
    'dashboard.view'   => 'Podglad panelu',
    'articles.view'    => 'Przegladanie artykulow',
    'articles.edit'    => 'Edycja artykulow',
    'articles.delete'  => 'Usuwanie artykulow',
    'pages.view'       => 'Przegladanie podstron',
    'pages.edit'       => 'Edycja podstron',
    'pages.delete'     => 'Usuwanie podstron',
    'services.view'    => 'Przegladanie uslug (oferta)',
    'services.edit'    => 'Edycja uslug (oferta)',
    'services.delete'  => 'Usuwanie uslug (oferta)',
    'media.view'       => 'Przegladanie biblioteki mediow',
    'media.upload'     => 'Wgrywanie plikow',
    'media.delete'     => 'Usuwanie plikow',
    'users.view'       => 'Przegladanie uzytkownikow',
    'users.edit'       => 'Edycja uzytkownikow',
    'users.delete'     => 'Usuwanie uzytkownikow',
    'roles.view'       => 'Przegladanie rol',
    'roles.edit'       => 'Edycja rol i uprawnien',
    'roles.delete'     => 'Usuwanie rol',
    'settings.edit'    => 'Edycja ustawien (branding/integracje)',
    'logs.view'        => 'Podglad logow aktywnosci',
    'leads.view'       => 'Przegladanie zapytan (leadow)',
    'leads.edit'       => 'Zarzadzanie statusem zapytan',
];

$permIds = [];
$stmt = $pdo->prepare('INSERT IGNORE INTO permissions (`key`, label) VALUES (:key, :label)');
foreach ($permissions as $key => $label) {
    $stmt->execute(['key' => $key, 'label' => $label]);
}
foreach ($pdo->query('SELECT id, `key` FROM permissions')->fetchAll() as $row) {
    $permIds[$row['key']] = (int) $row['id'];
}
out('Uprawnienia: OK (' . count($permIds) . ')');

// ---------------------------------------------------------------------
// 2. Role
// ---------------------------------------------------------------------
$roles = [
    'administrator' => ['name' => 'Administrator', 'permissions' => array_keys($permissions)],
    'redaktor'      => ['name' => 'Redaktor', 'permissions' => [
        'dashboard.view', 'articles.view', 'articles.edit', 'articles.delete',
        'pages.view', 'pages.edit', 'media.view', 'media.upload', 'media.delete',
    ]],
    'sprzedaz'      => ['name' => 'Sprzedaz', 'permissions' => [
        'dashboard.view', 'leads.view', 'leads.edit',
    ]],
];

$roleIds = [];
foreach ($roles as $slug => $def) {
    $pdo->prepare('INSERT IGNORE INTO roles (name, slug) VALUES (:name, :slug)')
        ->execute(['name' => $def['name'], 'slug' => $slug]);
}
foreach ($pdo->query('SELECT id, slug FROM roles')->fetchAll() as $row) {
    $roleIds[$row['slug']] = (int) $row['id'];
}
foreach ($roles as $slug => $def) {
    $pdo->prepare('DELETE FROM role_permissions WHERE role_id = :id')->execute(['id' => $roleIds[$slug]]);
    $ins = $pdo->prepare('INSERT INTO role_permissions (role_id, permission_id) VALUES (:role_id, :permission_id)');
    foreach ($def['permissions'] as $permKey) {
        $ins->execute(['role_id' => $roleIds[$slug], 'permission_id' => $permIds[$permKey]]);
    }
}
out('Role: OK (' . implode(', ', array_column($roles, 'name')) . ')');

// ---------------------------------------------------------------------
// 3. Pierwszy administrator (tylko jesli tabela users jest pusta)
// ---------------------------------------------------------------------
$userCount = (int) $pdo->query('SELECT COUNT(*) FROM users')->fetchColumn();
if ($userCount === 0) {
    $email    = getenv('SEED_ADMIN_EMAIL') ?: 'admin@secureware.pl';
    $password = getenv('SEED_ADMIN_PASSWORD') ?: bin2hex(random_bytes(6));

    $pdo->prepare(
        'INSERT INTO users (name, email, password_hash, role_id, status, created_at) VALUES (:name, :email, :hash, :role_id, "active", NOW())'
    )->execute([
        'name'    => 'Administrator',
        'email'   => $email,
        'hash'    => password_hash($password, PASSWORD_DEFAULT),
        'role_id' => $roleIds['administrator'],
    ]);

    out('====================================================');
    out('Utworzono konto administratora panelu:');
    out('  URL:    /' . Config::get('admin_path') . '/login');
    out('  E-mail: ' . $email);
    out('  Haslo:  ' . $password);
    out('Zmien haslo natychmiast po pierwszym logowaniu.');
    out('====================================================');
} else {
    out('Uzytkownicy juz istnieja - pomijam tworzenie administratora.');
}

// ---------------------------------------------------------------------
// 4. Domyslne ustawienia (branding + integracje)
// ---------------------------------------------------------------------
$settings = [
    'site_name'          => 'SecureWare',
    'site_tagline'       => 'Backup i disaster recovery, ktore dzialaja, gdy najbardziej ich potrzebujesz.',
    'contact_email'      => 'kontakt@secureware.pl',
    'contact_phone'      => '+48 000 000 000',
    'contact_address'    => 'Polska',
    'color_primary'      => '#0ba5ef',
    'color_dark'         => '#182a42',
    'footer_text'        => '© ' . date('Y') . ' SecureWare. Wszelkie prawa zastrzezone.',
    'social_linkedin'    => '',
    'social_twitter'     => '',
    'nav_menu'           => json_encode([
        ['label' => 'Oferta', 'url' => '/oferta'],
        ['label' => 'Blog', 'url' => '/blog'],
        ['label' => 'O nas', 'url' => '/o-nas'],
        ['label' => 'Kontakt', 'url' => '/kontakt'],
    ], JSON_UNESCAPED_UNICODE),
    'turnstile_site_key' => '',
    'turnstile_secret'   => '',
    'ga_measurement_id'  => '',
    'cookieyes_script'   => '',
    'logo_media_id'      => '',
    'favicon_media_id'   => '',
];
$insSetting = $pdo->prepare('INSERT IGNORE INTO settings (`key`, `value`) VALUES (:key, :value)');
foreach ($settings as $key => $value) {
    $insSetting->execute(['key' => $key, 'value' => (string) $value]);
}
out('Ustawienia domyslne: OK');

// ---------------------------------------------------------------------
// 5. Kategoria bloga
// ---------------------------------------------------------------------
$pdo->prepare('INSERT IGNORE INTO categories (name, slug) VALUES (:name, :slug)')
    ->execute(['name' => 'Backup i bezpieczenstwo', 'slug' => 'backup-i-bezpieczenstwo']);
$categoryId = (int) $pdo->query("SELECT id FROM categories WHERE slug = 'backup-i-bezpieczenstwo'")->fetchColumn();

// ---------------------------------------------------------------------
// 6. Uslugi (Oferta) - 13 pozycji
// ---------------------------------------------------------------------
$services = require __DIR__ . '/seed-data/services.php';
$insService = $pdo->prepare(
    'INSERT INTO services (name, slug, icon, short_description, content, position, status, meta, meta_title, meta_description, created_at, updated_at)
     VALUES (:name, :slug, :icon, :short_description, :content, :position, "published", "[]", :meta_title, :meta_description, NOW(), NOW())
     ON DUPLICATE KEY UPDATE name = name'
);
foreach ($services as $i => $s) {
    $insService->execute([
        'name'              => $s['name'],
        'slug'              => $s['slug'],
        'icon'              => $s['icon'],
        'short_description' => $s['short_description'],
        'content'           => $s['content'],
        'position'          => $i,
        'meta_title'        => $s['name'] . ' | SecureWare',
        'meta_description'  => $s['short_description'],
    ]);
}
out('Uslugi (oferta): OK (' . count($services) . ')');

// ---------------------------------------------------------------------
// 7. Podstrony CMS
// ---------------------------------------------------------------------
$pages = require __DIR__ . '/seed-data/pages.php';
$insPage = $pdo->prepare(
    'INSERT IGNORE INTO pages (title, slug, content, template, status, meta, meta_title, meta_description, created_at, updated_at)
     VALUES (:title, :slug, :content, :template, "published", "[]", :meta_title, :meta_description, NOW(), NOW())'
);
foreach ($pages as $p) {
    $insPage->execute([
        'title'            => $p['title'],
        'slug'             => $p['slug'],
        'content'          => $p['content'],
        'template'         => $p['template'] ?? 'default',
        'meta_title'       => $p['title'] . ' | SecureWare',
        'meta_description' => $p['meta_description'] ?? '',
    ]);
}
out('Podstrony CMS: OK (' . count($pages) . ')');

// ---------------------------------------------------------------------
// 8. Przykladowe wpisy na blogu
// ---------------------------------------------------------------------
$adminUserId = (int) $pdo->query('SELECT id FROM users ORDER BY id LIMIT 1')->fetchColumn();
$articles = require __DIR__ . '/seed-data/articles.php';
$insArticle = $pdo->prepare(
    'INSERT IGNORE INTO articles (title, slug, excerpt, content, category_id, status, meta_title, meta_description, author_id, published_at, created_at, updated_at)
     VALUES (:title, :slug, :excerpt, :content, :category_id, "published", :meta_title, :meta_description, :author_id, :published_at, NOW(), NOW())'
);
foreach ($articles as $i => $a) {
    $insArticle->execute([
        'title'            => $a['title'],
        'slug'             => $a['slug'],
        'excerpt'          => $a['excerpt'],
        'content'          => $a['content'],
        'category_id'      => $categoryId,
        'meta_title'       => $a['title'] . ' | SecureWare',
        'meta_description' => $a['excerpt'],
        'author_id'        => $adminUserId ?: null,
        'published_at'     => date('Y-m-d H:i:s', strtotime('-' . $i . ' days')),
    ]);
}
out('Wpisy na blogu: OK (' . count($articles) . ')');

out('Seed zakonczony.');
