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
use SecureWare\Models\Diagram;

class DiagramController
{
    public function index(Request $request): void
    {
        Auth::requirePermission('diagrams.view');

        echo View::render('admin/diagrams/index', ['diagrams' => Diagram::all()], 'admin/layout');
    }

    public function listJson(Request $request): void
    {
        Auth::requirePermission('diagrams.view');
        header('Content-Type: application/json; charset=UTF-8');

        $diagrams = array_map(
            static fn (array $d) => ['id' => $d['id'], 'name' => $d['name'], 'slug' => $d['slug']],
            Diagram::all()
        );
        echo json_encode(['ok' => true, 'diagrams' => $diagrams]);
    }

    public function create(Request $request): void
    {
        Auth::requirePermission('diagrams.edit');

        echo View::render('admin/diagrams/edit', ['diagram' => null, 'error' => null], 'admin/layout');
    }

    public function edit(Request $request, string $id): void
    {
        Auth::requirePermission('diagrams.edit');

        $diagram = Diagram::find((int) $id);
        if (!$diagram) {
            Response::notFound();
        }

        echo View::render('admin/diagrams/edit', ['diagram' => $diagram, 'error' => null], 'admin/layout');
    }

    public function store(Request $request): void
    {
        Auth::requirePermission('diagrams.edit');
        $this->save($request, null);
    }

    public function update(Request $request, string $id): void
    {
        Auth::requirePermission('diagrams.edit');
        $this->save($request, (int) $id);
    }

    private function save(Request $request, ?int $id): void
    {
        if (!Csrf::verify($request->input('_csrf'))) {
            Response::redirect($this->url());
        }

        $name = trim((string) $request->input('name', ''));
        $slug = Str::slug((string) $request->input('slug', '') ?: $name);

        $nodes = json_decode((string) $request->input('nodes_json', '[]'), true);
        $edges = json_decode((string) $request->input('edges_json', '[]'), true);

        if ($name === '' || $slug === '' || !is_array($nodes)) {
            echo View::render('admin/diagrams/edit', [
                'diagram' => $id ? Diagram::find($id) : null,
                'error'   => 'Nazwa jest wymagana, a diagram musi mieć poprawne dane.',
            ], 'admin/layout');
            return;
        }

        if (Diagram::slugExists($slug, $id)) {
            $slug .= '-' . substr(md5((string) microtime(true)), 0, 5);
        }

        $data = [
            'name'          => $name,
            'slug'          => $slug,
            'title'         => (string) $request->input('title', ''),
            'badge'         => (string) $request->input('badge', ''),
            'foot'          => (string) $request->input('foot', ''),
            'canvas_width'  => (int) $request->input('canvas_width', 480),
            'canvas_height' => (int) $request->input('canvas_height', 380),
            'nodes'         => $nodes,
            'edges'         => is_array($edges) ? $edges : [],
            'created_by'    => Auth::id(),
        ];

        if ($id === null) {
            $id = Diagram::create($data);
            Logger::record('create', 'diagram', $id);
        } else {
            Diagram::update($id, $data);
            Logger::record('update', 'diagram', $id);
        }

        Response::redirect($this->url());
    }

    public function destroy(Request $request, string $id): void
    {
        Auth::requirePermission('diagrams.delete');

        if (Csrf::verify($request->input('_csrf'))) {
            Diagram::delete((int) $id);
            Logger::record('delete', 'diagram', (int) $id);
        }

        Response::redirect($this->url());
    }

    private function url(): string
    {
        return '/' . Config::get('admin_path') . '/diagrams';
    }
}
