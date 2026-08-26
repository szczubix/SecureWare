<?php

namespace SecureWare\Core;

use PDOException;

/**
 * Wspolna logika instalacji (import schematu + seed danych poczatkowych),
 * uzywana zarowno przez database/seed.php (CLI, dla osob z dostepem SSH)
 * jak i install.php (przegladarka, dla hostingu bez SSH). Trzymanie tego
 * w jednym miejscu gwarantuje, ze oba sposoby robia dokladnie to samo.
 */
class Installer
{
    /**
     * @return string[] etykiety uprawnien: klucz => opis
     */
    private static function permissions(): array
    {
        return [
            'dashboard.view'   => 'Podgląd panelu',
            'articles.view'    => 'Przeglądanie artykułów',
            'articles.edit'    => 'Edycja artykułów',
            'articles.delete'  => 'Usuwanie artykułów',
            'pages.view'       => 'Przeglądanie podstron',
            'pages.edit'       => 'Edycja podstron',
            'pages.delete'     => 'Usuwanie podstron',
            'services.view'    => 'Przeglądanie usług (oferta)',
            'services.edit'    => 'Edycja usług (oferta)',
            'services.delete'  => 'Usuwanie usług (oferta)',
            'media.view'       => 'Przeglądanie biblioteki mediów',
            'media.upload'     => 'Wgrywanie plików',
            'media.delete'     => 'Usuwanie plików',
            'users.view'       => 'Przeglądanie użytkowników',
            'users.edit'       => 'Edycja użytkowników',
            'users.delete'     => 'Usuwanie użytkowników',
            'roles.view'       => 'Przeglądanie ról',
            'roles.edit'       => 'Edycja ról i uprawnień',
            'roles.delete'     => 'Usuwanie ról',
            'settings.edit'    => 'Edycja ustawień (branding/integracje)',
            'logs.view'        => 'Podgląd logów aktywności',
            'leads.view'       => 'Przeglądanie zapytań (leadów)',
            'leads.edit'       => 'Zarządzanie statusem zapytań',
            'diagrams.view'    => 'Przeglądanie diagramów',
            'diagrams.edit'    => 'Edycja diagramów (kreator)',
            'diagrams.delete'  => 'Usuwanie diagramów',
        ];
    }

    /**
     * Czy aplikacja jest juz zainstalowana (istnieje conajmniej jeden
     * uzytkownik panelu)? Zwraca false rowniez, gdy tabele jeszcze nie
     * istnieja (swiezy install, przed importem schematu).
     */
    public static function isInstalled(): bool
    {
        try {
            return (int) Database::connection()->query('SELECT COUNT(*) FROM users')->fetchColumn() > 0;
        } catch (PDOException $e) {
            return false;
        }
    }

    /**
     * Importuje database/schema.sql (CREATE TABLE IF NOT EXISTS - bezpieczne
     * do wielokrotnego uruchamiania).
     *
     * @return string[] log
     */
    public static function migrateSchema(): array
    {
        $sql = file_get_contents(ROOT_PATH . '/database/schema.sql');
        if ($sql === false) {
            return ['Nie znaleziono pliku database/schema.sql.'];
        }

        $pdo   = Database::connection();
        $count = 0;
        foreach (self::splitStatements($sql) as $statement) {
            $pdo->exec($statement);
            $count++;
        }

        return ["Schemat bazy danych: OK ({$count} zapytań)"];
    }

    /**
     * Dodaje nowe uprawnienia (dodane w kodzie po pierwszej instalacji) do
     * istniejacej bazy i przyznaje je roli Administrator - bezpieczne do
     * wielokrotnego uruchamiania, nie rusza istniejacych przypisan innych
     * rol (np. reczne ograniczenia na roli Redaktor/Sprzedaz zostaja).
     *
     * @return string[] log
     */
    public static function syncPermissions(): array
    {
        $pdo = Database::connection();

        $stmt = $pdo->prepare('INSERT IGNORE INTO permissions (`key`, label) VALUES (:key, :label)');
        foreach (self::permissions() as $key => $label) {
            $stmt->execute(['key' => $key, 'label' => $label]);
        }

        $adminRoleId = $pdo->query("SELECT id FROM roles WHERE slug = 'administrator'")->fetchColumn();
        if ($adminRoleId) {
            $grant = $pdo->prepare(
                'INSERT IGNORE INTO role_permissions (role_id, permission_id)
                 SELECT :role_id, id FROM permissions'
            );
            $grant->execute(['role_id' => $adminRoleId]);
        }

        return ['Uprawnienia: zsynchronizowano.'];
    }

    /**
     * @return string[]
     */
    private static function splitStatements(string $sql): array
    {
        $lines = array_filter(
            explode("\n", $sql),
            static fn (string $line): bool => !str_starts_with(trim($line), '--')
        );

        $statements = explode(';', implode("\n", $lines));
        $statements = array_map('trim', $statements);

        return array_filter($statements, static fn (string $s): bool => $s !== '');
    }

    /**
     * Seeduje role, uprawnienia, konto administratora (tylko jesli tabela
     * users jest pusta), domyslne ustawienia oraz przykladowa tresc.
     *
     * @return array{log: string[], admin: array{email: string, password: string}|null}
     */
    public static function seed(): array
    {
        $pdo = Database::connection();
        $log = [];

        // -- Uprawnienia ---------------------------------------------------
        $permissions = self::permissions();
        $permIds     = [];

        $stmt = $pdo->prepare('INSERT IGNORE INTO permissions (`key`, label) VALUES (:key, :label)');
        foreach ($permissions as $key => $label) {
            $stmt->execute(['key' => $key, 'label' => $label]);
        }
        foreach ($pdo->query('SELECT id, `key` FROM permissions')->fetchAll() as $row) {
            $permIds[$row['key']] = (int) $row['id'];
        }
        $log[] = 'Uprawnienia: OK (' . count($permIds) . ')';

        // -- Role ------------------------------------------------------------
        $roles = [
            'administrator' => ['name' => 'Administrator', 'permissions' => array_keys($permissions)],
            'redaktor'      => ['name' => 'Redaktor', 'permissions' => [
                'dashboard.view', 'articles.view', 'articles.edit', 'articles.delete',
                'pages.view', 'pages.edit', 'media.view', 'media.upload', 'media.delete',
                'diagrams.view', 'diagrams.edit',
            ]],
            'sprzedaz'      => ['name' => 'Sprzedaż', 'permissions' => [
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
        $log[] = 'Role: OK (' . implode(', ', array_column($roles, 'name')) . ')';

        // -- Pierwszy administrator -------------------------------------
        $admin     = null;
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

            $admin = ['email' => $email, 'password' => $password];
            $log[] = 'Utworzono konto administratora panelu.';
        } else {
            $log[] = 'Użytkownicy już istnieją - pomijam tworzenie administratora.';
        }

        // -- Domyslne ustawienia -----------------------------------------
        $settings = [
            'site_name'          => 'SecureWare',
            'site_tagline'       => 'Backup i disaster recovery, które działają, gdy najbardziej ich potrzebujesz.',
            'contact_email'      => 'kontakt@secureware.pl',
            'contact_phone'      => '+48 000 000 000',
            'contact_address'    => 'Polska',
            'color_primary'      => '#0ba5ef',
            'color_dark'         => '#182a42',
            'footer_text'        => '© ' . date('Y') . ' SecureWare. Wszelkie prawa zastrzeżone.',
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
            'mail_from_address'  => '',
            'logo_media_id'      => '',
            'favicon_media_id'   => '',
        ];
        $insSetting = $pdo->prepare('INSERT IGNORE INTO settings (`key`, `value`) VALUES (:key, :value)');
        foreach ($settings as $key => $value) {
            $insSetting->execute(['key' => $key, 'value' => (string) $value]);
        }
        $log[] = 'Ustawienia domyślne: OK';

        // -- Kategoria bloga -----------------------------------------------
        $pdo->prepare('INSERT IGNORE INTO categories (name, slug) VALUES (:name, :slug)')
            ->execute(['name' => 'Backup i bezpieczeństwo', 'slug' => 'backup-i-bezpieczenstwo']);
        $categoryId = (int) $pdo->query("SELECT id FROM categories WHERE slug = 'backup-i-bezpieczenstwo'")->fetchColumn();

        // -- Uslugi (Oferta) - 13 pozycji ------------------------------------
        $services   = require ROOT_PATH . '/database/seed-data/services.php';
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
        $log[] = 'Usługi (oferta): OK (' . count($services) . ')';

        // -- Podstrony CMS ---------------------------------------------------
        $pages   = require ROOT_PATH . '/database/seed-data/pages.php';
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
        $log[] = 'Podstrony CMS: OK (' . count($pages) . ')';

        // -- Przykładowe wpisy na blogu --------------------------------------
        $adminUserId = (int) $pdo->query('SELECT id FROM users ORDER BY id LIMIT 1')->fetchColumn();
        $articles    = require ROOT_PATH . '/database/seed-data/articles.php';
        $insArticle  = $pdo->prepare(
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
        $log[] = 'Wpisy na blogu: OK (' . count($articles) . ')';

        foreach (self::seedTranslations() as $line) {
            $log[] = $line;
        }

        return ['log' => $log, 'admin' => $admin];
    }

    /**
     * Wgrywa angielskie tlumaczenia domyslnej tresci (uslugi/strony CMS/
     * artykuly/kategoria + kilka ustawien) z seed-data/translations-en.php.
     * Dopasowanie po slug/kluczu do JUZ ISTNIEJACYCH wierszy - nie tworzy
     * nowych encji. Bezpieczne do wielokrotnego uruchamiania (upsert po
     * unikalnym kluczu entity_type+entity_id+locale+field), wiec dziala
     * zarowno przy pierwszej instalacji jak i przez refresh-content.php.
     *
     * @return string[] log
     */
    public static function seedTranslations(): array
    {
        $pdo = Database::connection();
        $log = [];
        $data = require ROOT_PATH . '/database/seed-data/translations-en.php';

        $upsert = $pdo->prepare(
            'INSERT INTO translations (entity_type, entity_id, locale, field, value)
             VALUES (:type, :id, "en", :field, :value)
             ON DUPLICATE KEY UPDATE value = VALUES(value)'
        );
        $translateFields = function (string $type, int $id, array $fields) use ($upsert): void {
            foreach ($fields as $field => $value) {
                $upsert->execute(['type' => $type, 'id' => $id, 'field' => $field, 'value' => $value]);
            }
        };

        $count = 0;
        foreach ($data['services'] ?? [] as $slug => $fields) {
            $stmt = $pdo->prepare('SELECT id, name, short_description FROM services WHERE slug = :slug');
            $stmt->execute(['slug' => $slug]);
            $row = $stmt->fetch();
            if (!$row) {
                continue;
            }
            $fields += [
                'meta_title'       => $fields['name'] . ' | SecureWare',
                'meta_description' => $fields['short_description'] ?? '',
            ];
            $translateFields('service', (int) $row['id'], $fields);
            $count++;
        }
        $log[] = 'Tłumaczenia usług (EN): OK (' . $count . ')';

        $count = 0;
        foreach ($data['pages'] ?? [] as $slug => $fields) {
            $stmt = $pdo->prepare('SELECT id FROM pages WHERE slug = :slug');
            $stmt->execute(['slug' => $slug]);
            $id = $stmt->fetchColumn();
            if (!$id) {
                continue;
            }
            $fields += ['meta_title' => $fields['title'] . ' | SecureWare'];
            $translateFields('page', (int) $id, $fields);
            $count++;
        }
        $log[] = 'Tłumaczenia podstron CMS (EN): OK (' . $count . ')';

        $count = 0;
        foreach ($data['articles'] ?? [] as $slug => $fields) {
            $stmt = $pdo->prepare('SELECT id FROM articles WHERE slug = :slug');
            $stmt->execute(['slug' => $slug]);
            $id = $stmt->fetchColumn();
            if (!$id) {
                continue;
            }
            $fields += [
                'meta_title'       => $fields['title'] . ' | SecureWare',
                'meta_description' => $fields['excerpt'] ?? '',
            ];
            $translateFields('article', (int) $id, $fields);
            $count++;
        }
        $log[] = 'Tłumaczenia artykułów (EN): OK (' . $count . ')';

        $count = 0;
        foreach ($data['categories'] ?? [] as $slug => $fields) {
            $stmt = $pdo->prepare('SELECT id FROM categories WHERE slug = :slug');
            $stmt->execute(['slug' => $slug]);
            $id = $stmt->fetchColumn();
            if (!$id) {
                continue;
            }
            $translateFields('category', (int) $id, $fields);
            $count++;
        }
        $log[] = 'Tłumaczenia kategorii (EN): OK (' . $count . ')';

        $settings = $data['settings'] ?? [];
        $setSetting = $pdo->prepare(
            'INSERT INTO settings (`key`, `value`) VALUES (:key, :value)
             ON DUPLICATE KEY UPDATE `value` = VALUES(`value`)'
        );
        if (isset($settings['site_tagline_en'])) {
            $setSetting->execute(['key' => 'site_tagline_en', 'value' => $settings['site_tagline_en']]);
        }
        if (isset($settings['footer_text_en'])) {
            $setSetting->execute(['key' => 'footer_text_en', 'value' => str_replace('%YEAR%', date('Y'), $settings['footer_text_en'])]);
        }
        if (isset($settings['nav_menu_en'])) {
            $setSetting->execute(['key' => 'nav_menu_en', 'value' => json_encode($settings['nav_menu_en'], JSON_UNESCAPED_UNICODE)]);
        }
        $log[] = 'Ustawienia EN (tagline/stopka/menu): OK';

        return $log;
    }

    /**
     * Nadpisuje treść domyślnych usług/stron/artykułów (dopasowanych po
     * slug), etykiety uprawnień, nazwy ról oraz kilka domyślnych ustawień
     * aktualną wersją z seed-data/Installer - na wypadek gdyby domyślna
     * treść była błędna w chwili pierwszej instalacji (np. literówki,
     * brak polskich znaków). Nie dotyka leadów, użytkowników ani treści,
     * które nie pochodzą z domyślnego seeda (dopasowanie wyłącznie po
     * istniejącym slug/key, bez wstawiania nowych wierszy).
     *
     * @return string[] log
     */
    public static function refreshDefaultContent(): array
    {
        $pdo = Database::connection();
        $log = [];

        // -- Usługi (Oferta) --------------------------------------------------
        $services = require ROOT_PATH . '/database/seed-data/services.php';
        $updService = $pdo->prepare(
            'UPDATE services SET name = :name, icon = :icon, short_description = :short_description,
             content = :content, meta_title = :meta_title, meta_description = :meta_description
             WHERE slug = :slug'
        );
        $updated = 0;
        foreach ($services as $s) {
            $updService->execute([
                'name'              => $s['name'],
                'icon'              => $s['icon'],
                'short_description' => $s['short_description'],
                'content'           => $s['content'],
                'meta_title'        => $s['name'] . ' | SecureWare',
                'meta_description'  => $s['short_description'],
                'slug'              => $s['slug'],
            ]);
            $updated += $updService->rowCount();
        }
        $log[] = 'Usługi (oferta): zaktualizowano ' . $updated . ' z ' . count($services);

        // -- Podstrony CMS -----------------------------------------------------
        $pages = require ROOT_PATH . '/database/seed-data/pages.php';
        $updPage = $pdo->prepare(
            'UPDATE pages SET title = :title, content = :content, meta_title = :meta_title,
             meta_description = :meta_description WHERE slug = :slug'
        );
        $updated = 0;
        foreach ($pages as $p) {
            $updPage->execute([
                'title'            => $p['title'],
                'content'          => $p['content'],
                'meta_title'       => $p['title'] . ' | SecureWare',
                'meta_description' => $p['meta_description'] ?? '',
                'slug'             => $p['slug'],
            ]);
            $updated += $updPage->rowCount();
        }
        $log[] = 'Podstrony CMS: zaktualizowano ' . $updated . ' z ' . count($pages);

        // -- Wpisy na blogu ------------------------------------------------------
        $articles = require ROOT_PATH . '/database/seed-data/articles.php';
        $updArticle = $pdo->prepare(
            'UPDATE articles SET title = :title, excerpt = :excerpt, content = :content,
             meta_title = :meta_title, meta_description = :meta_description WHERE slug = :slug'
        );
        $updated = 0;
        foreach ($articles as $a) {
            $updArticle->execute([
                'title'            => $a['title'],
                'excerpt'          => $a['excerpt'],
                'content'          => $a['content'],
                'meta_title'       => $a['title'] . ' | SecureWare',
                'meta_description' => $a['excerpt'],
                'slug'             => $a['slug'],
            ]);
            $updated += $updArticle->rowCount();
        }
        $log[] = 'Wpisy na blogu: zaktualizowano ' . $updated . ' z ' . count($articles);

        // -- Kategoria bloga, uprawnienia, role --------------------------------
        $pdo->prepare('UPDATE categories SET name = :name WHERE slug = :slug')
            ->execute(['name' => 'Backup i bezpieczeństwo', 'slug' => 'backup-i-bezpieczenstwo']);

        $updPerm = $pdo->prepare('UPDATE permissions SET label = :label WHERE `key` = :key');
        foreach (self::permissions() as $key => $label) {
            $updPerm->execute(['label' => $label, 'key' => $key]);
        }

        $pdo->prepare('UPDATE roles SET name = :name WHERE slug = :slug')->execute(['name' => 'Sprzedaż', 'slug' => 'sprzedaz']);
        $log[] = 'Etykiety uprawnień, nazwy ról, kategoria bloga: OK';

        // -- Kilka domyślnych ustawień (tylko treść opisowa, nie branding) ----
        $updSetting = $pdo->prepare('UPDATE settings SET `value` = :value WHERE `key` = :key');
        $updSetting->execute(['key' => 'site_tagline', 'value' => 'Backup i disaster recovery, które działają, gdy najbardziej ich potrzebujesz.']);
        $updSetting->execute(['key' => 'footer_text', 'value' => '© ' . date('Y') . ' SecureWare. Wszelkie prawa zastrzeżone.']);
        $log[] = 'Domyślne teksty ustawień (tagline, stopka): OK';

        return $log;
    }
}
