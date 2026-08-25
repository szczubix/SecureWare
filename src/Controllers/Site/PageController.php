<?php

namespace SecureWare\Controllers\Site;

use SecureWare\Core\Request;
use SecureWare\Core\Response;
use SecureWare\Core\View;
use SecureWare\Models\Page;

class PageController
{
    public function show(Request $request, string $slug): void
    {
        $page = Page::findBySlug($slug);
        if (!$page) {
            Response::notFound();
        }

        echo View::render('site/page', [
            'page'            => $page,
            'metaTitle'       => $page['meta_title'] ?: $page['title'],
            'metaDescription' => $page['meta_description'] ?: '',
        ], 'site/layout');
    }
}
