<?php

namespace SecureWare\Controllers\Site;

use SecureWare\Core\Request;
use SecureWare\Core\View;
use SecureWare\Models\Article;
use SecureWare\Models\Service;
use SecureWare\Models\Setting;

class HomeController
{
    public function index(Request $request): void
    {
        $settings = Setting::all();

        echo View::render('site/home', [
            'services'        => Service::published(),
            'latestArticles'  => Article::latest(3),
            'metaTitle'       => ($settings['site_name'] ?? 'SecureWare') . ' — ' . ($settings['site_tagline'] ?? 'Backup i Disaster Recovery dla firm'),
            'metaDescription' => $settings['site_tagline'] ?? '',
        ], 'site/layout');
    }
}
