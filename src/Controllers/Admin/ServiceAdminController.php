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
use SecureWare\Models\Service;

class ServiceAdminController
{
    public function index(Request $request): void
    {
        Auth::requirePermission('services.view');

        echo View::render('admin/services/index', ['services' => Service::all()], 'admin/layout');
    }

    public function create(Request $request): void
    {
        Auth::requirePermission('services.edit');

        echo View::render('admin/services/edit', ['service' => null, 'error' => null], 'admin/layout');
    }

    public function edit(Request $request, string $id): void
    {
        Auth::requirePermission('services.edit');

        $service = Service::find((int) $id);
        if (!$service) {
            Response::notFound();
        }

        echo View::render('admin/services/edit', ['service' => $service, 'error' => null], 'admin/layout');
    }

    public function store(Request $request): void
    {
        Auth::requirePermission('services.edit');
        $this->save($request, null);
    }

    public function update(Request $request, string $id): void
    {
        Auth::requirePermission('services.edit');
        $this->save($request, (int) $id);
    }

    private function save(Request $request, ?int $id): void
    {
        if (!Csrf::verify($request->input('_csrf'))) {
            Response::redirect($this->url());
        }

        $name = trim((string) $request->input('name', ''));
        $slug = Str::slug((string) $request->input('slug', '') ?: $name);

        if ($name === '' || $slug === '') {
            echo View::render('admin/services/edit', [
                'service' => $id ? Service::find($id) : null,
                'error'   => 'Nazwa i slug są wymagane.',
            ], 'admin/layout');
            return;
        }

        if (Service::slugExists($slug, $id)) {
            $slug .= '-' . substr(md5((string) microtime(true)), 0, 5);
        }

        $data = [
            'name'              => $name,
            'slug'              => $slug,
            'icon'              => $request->input('icon', 'shield') ?: 'shield',
            'short_description' => (string) $request->input('short_description', ''),
            'content'           => (string) $request->input('content', ''),
            'position'          => (int) $request->input('position', 0),
            'status'            => $request->input('status', 'draft') === 'published' ? 'published' : 'draft',
            'meta'              => $this->metaFromRequest($request),
            'meta_title'        => $request->input('meta_title') ?: null,
            'meta_description'  => $request->input('meta_description') ?: null,
        ];

        if ($id === null) {
            $id = Service::create($data);
            Logger::record('create', 'service', $id);
        } else {
            Service::update($id, $data);
            Logger::record('update', 'service', $id);
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
        Auth::requirePermission('services.delete');

        if (Csrf::verify($request->input('_csrf'))) {
            Service::delete((int) $id);
            Logger::record('delete', 'service', (int) $id);
        }

        Response::redirect($this->url());
    }

    private function url(): string
    {
        return '/' . Config::get('admin_path') . '/services';
    }
}
