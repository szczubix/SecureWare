<?php

namespace SecureWare\Controllers\Site;

use SecureWare\Core\Locale;
use SecureWare\Core\Request;
use SecureWare\Core\View;
use SecureWare\Models\Article;
use SecureWare\Models\HomeContent;
use SecureWare\Models\Service;
use SecureWare\Models\Setting;

class HomeController
{
    public function index(Request $request): void
    {
        $settings = Setting::all();
        $tagline  = Locale::isDefault() ? ($settings['site_tagline'] ?? '') : ($settings['site_tagline_en'] ?? $settings['site_tagline'] ?? '');

        echo View::render('site/home', [
            'services'        => Service::published(Locale::current()),
            'latestArticles'  => Article::latest(3, Locale::current()),
            'content'         => HomeContent::current(Locale::current()),
            'metaTitle'       => ($settings['site_name'] ?? 'SecureWare') . ' — ' . ($tagline ?: 'Backup i Disaster Recovery dla firm'),
            'metaDescription' => $tagline,
        ], 'site/layout');
    }
}
