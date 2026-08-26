<?php

namespace SecureWare\Controllers\Site;

use SecureWare\Core\Config;
use SecureWare\Core\Database;
use SecureWare\Core\Locale;
use SecureWare\Core\Request;
use SecureWare\Models\Page;
use SecureWare\Models\Service;

class SeoController
{
    public function sitemap(Request $request): void
    {
        $base = Config::get('app')['url'];

        $paths = [
            ['path' => '/', 'lastmod' => null],
            ['path' => '/oferta', 'lastmod' => null],
            ['path' => '/blog', 'lastmod' => null],
            ['path' => '/kontakt', 'lastmod' => null],
        ];

        foreach (Service::published() as $s) {
            $paths[] = ['path' => '/oferta/' . $s['slug'], 'lastmod' => substr($s['updated_at'], 0, 10)];
        }

        foreach (Page::publishedSlugs() as $p) {
            $paths[] = ['path' => '/' . $p['slug'], 'lastmod' => substr($p['updated_at'], 0, 10)];
        }

        $articles = Database::connection()
            ->query("SELECT slug, updated_at FROM articles WHERE status = 'published' AND published_at <= NOW()")
            ->fetchAll();
        foreach ($articles as $a) {
            $paths[] = ['path' => '/blog/' . $a['slug'], 'lastmod' => substr($a['updated_at'], 0, 10)];
        }

        header('Content-Type: application/xml; charset=utf-8');
        echo '<?xml version="1.0" encoding="UTF-8"?>' . "\n";
        echo '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">' . "\n";

        // Kazdy adres wystepuje raz na jezyk (PL bez prefiksu, EN z /en), z
        // wzajemnymi hreflang alternate - tak, by wyszukiwarki poprawnie
        // rozroznialy obie wersje jako te sama tresc w innym jezyku.
        foreach ($paths as $p) {
            foreach (Locale::AVAILABLE as $locale) {
                $loc = $base . Locale::urlIn($locale, $p['path']);
                echo '  <url><loc>' . htmlspecialchars($loc, ENT_QUOTES, 'UTF-8') . '</loc>';
                foreach (Locale::AVAILABLE as $altLocale) {
                    $alt = $base . Locale::urlIn($altLocale, $p['path']);
                    echo '<xhtml:link rel="alternate" hreflang="' . $altLocale . '" href="' . htmlspecialchars($alt, ENT_QUOTES, 'UTF-8') . '"/>';
                }
                if ($p['lastmod']) {
                    echo '<lastmod>' . $p['lastmod'] . '</lastmod>';
                }
                echo '</url>' . "\n";
            }
        }

        echo '</urlset>';
        exit;
    }

    public function robots(Request $request): void
    {
        $base = Config::get('app')['url'];
        header('Content-Type: text/plain; charset=utf-8');
        echo "User-agent: *\n";
        echo "Disallow: /" . Config::get('admin_path') . "/\n";
        echo "Sitemap: {$base}/sitemap.xml\n";
        exit;
    }
}
