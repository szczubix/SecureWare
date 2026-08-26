<?php

namespace SecureWare\Controllers\Site;

use SecureWare\Core\Database;
use SecureWare\Core\Request;
use SecureWare\Core\Response;
use SecureWare\Core\View;
use SecureWare\Models\Article;
use SecureWare\Models\SiteContent;

class BlogController
{
    public function index(Request $request): void
    {
        $page     = max(1, (int) $request->input('page', 1));
        $category = $request->input('kategoria') ?: null;
        $tag      = $request->input('tag') ?: null;

        $result = Article::published($page, 9, $category, $tag);

        $categories = Database::connection()->query('SELECT * FROM categories ORDER BY name')->fetchAll();

        echo View::render('site/blog-index', [
            'articles'        => $result['items'],
            'total'           => $result['total'],
            'page'            => $page,
            'perPage'         => 9,
            'categories'      => $categories,
            'activeCategory'  => $category,
            'content'         => SiteContent::current()['blog'],
            'metaTitle'       => 'Blog — SecureWare',
            'metaDescription' => 'Backup, disaster recovery i bezpieczeństwo danych - artykuły i poradniki.',
        ], 'site/layout');
    }

    public function show(Request $request, string $slug): void
    {
        $article = Article::findBySlug($slug);
        if (!$article) {
            Response::notFound();
        }

        echo View::render('site/blog-single', [
            'article'         => $article,
            'related'         => Article::related((int) $article['id'], $article['category_id'] ? (int) $article['category_id'] : null),
            'metaTitle'       => $article['meta_title'] ?: $article['title'],
            'metaDescription' => $article['meta_description'] ?: $article['excerpt'],
            'ogImage'         => $article['featured_image_path'] ?: null,
        ], 'site/layout');
    }
}
