<?php

namespace SecureWare\Controllers\Site;

use SecureWare\Core\Database;
use SecureWare\Core\Lang;
use SecureWare\Core\Locale;
use SecureWare\Core\Request;
use SecureWare\Core\Response;
use SecureWare\Core\View;
use SecureWare\Models\Article;
use SecureWare\Models\SiteContent;
use SecureWare\Models\Translation;

class BlogController
{
    public function index(Request $request): void
    {
        $page     = max(1, (int) $request->input('page', 1));
        $category = $request->input('kategoria') ?: null;
        $tag      = $request->input('tag') ?: null;
        $locale   = Locale::current();

        $result = Article::published($page, 9, $category, $tag, $locale);

        $categories = Database::connection()->query('SELECT * FROM categories ORDER BY name')->fetchAll();
        if (!Locale::isDefault()) {
            $categories = array_map(static function (array $c) use ($locale) {
                $c['name'] = Translation::get('category', (int) $c['id'], $locale, 'name', $c['name']);
                return $c;
            }, $categories);
        }

        echo View::render('site/blog-index', [
            'articles'        => $result['items'],
            'total'           => $result['total'],
            'page'            => $page,
            'perPage'         => 9,
            'categories'      => $categories,
            'activeCategory'  => $category,
            'content'         => SiteContent::current($locale)['blog'],
            'metaTitle'       => Lang::t('blog.meta_title'),
            'metaDescription' => Lang::t('blog.meta_description'),
        ], 'site/layout');
    }

    public function show(Request $request, string $slug): void
    {
        $article = Article::findBySlug($slug, Locale::current());
        if (!$article) {
            Response::notFound();
        }

        echo View::render('site/blog-single', [
            'article'         => $article,
            'related'         => Article::related((int) $article['id'], $article['category_id'] ? (int) $article['category_id'] : null, Locale::current()),
            'metaTitle'       => $article['meta_title'] ?: $article['title'],
            'metaDescription' => $article['meta_description'] ?: $article['excerpt'],
            'ogImage'         => $article['featured_image_path'] ?: null,
        ], 'site/layout');
    }
}
