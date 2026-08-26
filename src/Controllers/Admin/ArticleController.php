<?php

namespace SecureWare\Controllers\Admin;

use SecureWare\Core\Auth;
use SecureWare\Core\Config;
use SecureWare\Core\Csrf;
use SecureWare\Core\Logger;
use SecureWare\Core\Request;
use SecureWare\Core\Response;
use SecureWare\Core\Session;
use SecureWare\Core\Str;
use SecureWare\Core\View;
use SecureWare\Models\Article;
use SecureWare\Models\Category;
use SecureWare\Models\Media;
use SecureWare\Models\Tag;

class ArticleController
{
    public function index(Request $request): void
    {
        Auth::requirePermission('articles.view');

        echo View::render('admin/articles/index', [
            'articles' => Article::allForAdmin(),
        ], 'admin/layout');
    }

    public function create(Request $request): void
    {
        Auth::requirePermission('articles.edit');

        echo View::render('admin/articles/edit', [
            'article'    => null,
            'categories' => Category::all(),
            'media'      => Media::all(),
            'tagsValue'  => '',
            'error'      => null,
        ], 'admin/layout');
    }

    public function edit(Request $request, string $id): void
    {
        Auth::requirePermission('articles.edit');

        $article = Article::find((int) $id);
        if (!$article) {
            Response::notFound();
        }

        echo View::render('admin/articles/edit', [
            'article'    => $article,
            'categories' => Category::all(),
            'media'      => Media::all(),
            'tagsValue'  => implode(', ', array_column($article['tags'], 'name')),
            'error'      => null,
        ], 'admin/layout');
    }

    public function store(Request $request): void
    {
        Auth::requirePermission('articles.edit');
        $this->save($request, null);
    }

    public function update(Request $request, string $id): void
    {
        Auth::requirePermission('articles.edit');
        $this->save($request, (int) $id);
    }

    private function save(Request $request, ?int $id): void
    {
        if (!Csrf::verify($request->input('_csrf'))) {
            Response::redirect($this->url());
        }

        $title = trim((string) $request->input('title', ''));
        $slug  = Str::slug((string) $request->input('slug', '') ?: $title);

        if ($title === '' || $slug === '') {
            $this->renderError($request, $id, 'Tytuł i slug są wymagane.');
            return;
        }

        if (Article::slugExists($slug, $id)) {
            $slug .= '-' . substr(md5((string) microtime(true)), 0, 5);
        }

        $categoryId = $request->input('category_id') ?: null;
        $newCategory = trim((string) $request->input('new_category', ''));
        if ($newCategory !== '') {
            $categoryId = Category::firstOrCreate($newCategory, Str::slug($newCategory));
        }

        $status      = $request->input('status', 'draft') === 'published' ? 'published' : 'draft';
        $publishedAt = $request->input('published_at') ?: null;
        if ($status === 'published' && !$publishedAt) {
            $publishedAt = date('Y-m-d H:i:s');
        }
        if ($publishedAt) {
            $publishedAt = str_replace('T', ' ', $publishedAt) . (strlen($publishedAt) === 16 ? ':00' : '');
        }

        $data = [
            'title'             => $title,
            'slug'              => $slug,
            'excerpt'           => $request->input('excerpt') ?: Str::excerpt((string) $request->input('content', '')),
            'content'           => (string) $request->input('content', ''),
            'featured_image_id' => $request->input('featured_image_id') ?: null,
            'category_id'       => $categoryId,
            'status'            => $status,
            'meta_title'        => $request->input('meta_title') ?: null,
            'meta_description'  => $request->input('meta_description') ?: null,
            'published_at'      => $publishedAt,
            'author_id'         => Auth::id(),
        ];

        $tagIds = Tag::idsFromString((string) $request->input('tags', ''));

        if ($id === null) {
            $id = Article::create($data);
            Logger::record('create', 'article', $id);
        } else {
            Article::update($id, $data);
            Logger::record('update', 'article', $id);
        }

        Tag::syncArticle($id, $tagIds);

        Response::redirect($this->url());
    }

    public function destroy(Request $request, string $id): void
    {
        Auth::requirePermission('articles.delete');

        if (Csrf::verify($request->input('_csrf'))) {
            Article::delete((int) $id);
            Logger::record('delete', 'article', (int) $id);
        }

        Response::redirect($this->url());
    }

    private function renderError(Request $request, ?int $id, string $message): void
    {
        echo View::render('admin/articles/edit', [
            'article'    => $id ? Article::find($id) : null,
            'categories' => Category::all(),
            'media'      => Media::all(),
            'tagsValue'  => (string) $request->input('tags', ''),
            'error'      => $message,
        ], 'admin/layout');
    }

    private function url(): string
    {
        return '/' . Config::get('admin_path') . '/articles';
    }
}
