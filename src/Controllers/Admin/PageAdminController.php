<?php

namespace SecureWare\Controllers\Admin;

use SecureWare\Core\Auth;
use SecureWare\Core\Config;
use SecureWare\Core\Csrf;
use SecureWare\Core\Logger;
use SecureWare\Core\Request;
use SecureWare\Core\Response;
use SecureWare\Core\Str;
use SecureWare\Core\View;
use SecureWare\Models\Page;

class PageAdminController
{
    public function index(Request $request): void
    {
        Auth::requirePermission('pages.view');

        echo View::render('admin/pages/index', ['pages' => Page::all()], 'admin/layout');
    }

    public function create(Request $request): void
    {
        Auth::requirePermission('pages.edit');

        echo View::render('admin/pages/edit', [
            'page' => null, 'allPages' => Page::all(), 'error' => null,
        ], 'admin/layout');
    }

    public function edit(Request $request, string $id): void
    {
        Auth::requirePermission('pages.edit');

        $page = Page::find((int) $id);
        if (!$page) {
            Response::notFound();
        }

        echo View::render('admin/pages/edit', [
            'page' => $page, 'allPages' => Page::all(), 'error' => null,
        ], 'admin/layout');
    }

    public function store(Request $request): void
    {
        Auth::requirePermission('pages.edit');
        $this->save($request, null);
    }

    public function update(Request $request, string $id): void
    {
        Auth::requirePermission('pages.edit');
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
            echo View::render('admin/pages/edit', [
                'page' => $id ? Page::find($id) : null, 'allPages' => Page::all(),
                'error' => 'Tytul i slug sa wymagane.',
            ], 'admin/layout');
            return;
        }

        if (Page::slugExists($slug, $id)) {
            $slug .= '-' . substr(md5((string) microtime(true)), 0, 5);
        }

        $parentId = $request->input('parent_id') ?: null;
        if ($parentId && $id && (int) $parentId === $id) {
            $parentId = null;
        }

        $data = [
            'title'            => $title,
            'slug'             => $slug,
            'content'          => (string) $request->input('content', ''),
            'template'         => $request->input('template', 'default'),
            'parent_id'        => $parentId,
            'status'           => $request->input('status', 'draft') === 'published' ? 'published' : 'draft',
            'meta'             => $this->metaFromRequest($request),
            'meta_title'       => $request->input('meta_title') ?: null,
            'meta_description' => $request->input('meta_description') ?: null,
        ];

        if ($id === null) {
            $id = Page::create($data);
            Logger::record('create', 'page', $id);
        } else {
            Page::update($id, $data);
            Logger::record('update', 'page', $id);
        }

        Response::redirect($this->url());
    }

    private function metaFromRequest(Request $request): array
    {
        $keys   = $request->all()['meta_key'] ?? [];
        $values = $request->all()['meta_value'] ?? [];
        $meta   = [];

        foreach ((array) $keys as $i => $key) {
            $key = trim((string) $key);
            if ($key === '') {
                continue;
            }
            $meta[$key] = trim((string) ($values[$i] ?? ''));
        }

        return $meta;
    }

    public function destroy(Request $request, string $id): void
    {
        Auth::requirePermission('pages.delete');

        if (Csrf::verify($request->input('_csrf'))) {
            Page::delete((int) $id);
            Logger::record('delete', 'page', (int) $id);
        }

        Response::redirect($this->url());
    }

    private function url(): string
    {
        return '/' . Config::get('admin_path') . '/pages';
    }
}
