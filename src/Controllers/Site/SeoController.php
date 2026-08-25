<?php

namespace SecureWare\Controllers\Site;

use SecureWare\Core\Config;
use SecureWare\Core\Database;
use SecureWare\Core\Request;
use SecureWare\Models\Page;
use SecureWare\Models\Service;

class SeoController
{
    public function sitemap(Request $request): void
    {
        $base = Config::get('app')['url'];

        $urls = [
            ['loc' => $base . '/', 'lastmod' => null],
            ['loc' => $base . '/oferta', 'lastmod' => null],
            ['loc' => $base . '/blog', 'lastmod' => null],
            ['loc' => $base . '/kontakt', 'lastmod' => null],
        ];

        foreach (Service::published() as $s) {
            $urls[] = ['loc' => $base . '/oferta/' . $s['slug'], 'lastmod' => substr($s['updated_at'], 0, 10)];
        }

        foreach (Page::publishedSlugs() as $p) {
            $urls[] = ['loc' => $base . '/' . $p['slug'], 'lastmod' => substr($p['updated_at'], 0, 10)];
        }

        $articles = Database::connection()
            ->query("SELECT slug, updated_at FROM articles WHERE status = 'published' AND published_at <= NOW()")
            ->fetchAll();
        foreach ($articles as $a) {
            $urls[] = ['loc' => $base . '/blog/' . $a['slug'], 'lastmod' => substr($a['updated_at'], 0, 10)];
        }

        header('Content-Type: application/xml; charset=utf-8');
        echo '<?xml version="1.0" encoding="UTF-8"?>' . "\n";
        echo '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' . "\n";
        foreach ($urls as $u) {
            echo '  <url><loc>' . htmlspecialchars($u['loc'], ENT_QUOTES, 'UTF-8') . '</loc>';
            if ($u['lastmod']) {
                echo '<lastmod>' . $u['lastmod'] . '</lastmod>';
            }
            echo '</url>' . "\n";
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
