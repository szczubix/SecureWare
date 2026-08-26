<?php
/** @var array|null $diagram */
/** @var string|null $error */
use SecureWare\Core\Config;
use SecureWare\Core\Csrf;
use SecureWare\Core\Icons;

$adminUrl = '/' . Config::get('admin_path');
$isEdit   = $diagram !== null;
$action   = $isEdit ? $adminUrl . '/diagrams/' . $diagram['id'] : $adminUrl . '/diagrams';
$h        = static fn ($v) => htmlspecialchars((string) $v, ENT_QUOTES, 'UTF-8');

$icons = ['shield-check','cloud-upload','map-pin','lock','mail','server','layers','life-buoy','refresh-ccw','clipboard-check','tool','activity','file-check','shield'];
$iconLibrary = [];
foreach ($icons as $icon) {
    $iconLibrary[$icon] = Icons::svg($icon, 20);
}

$initialState = [
    'nodes' => $diagram['nodes'] ?? [],
    'edges' => $diagram['edges'] ?? [],
];
?>
<div class="toolbar">
    <h1><?= $isEdit ? 'Edytuj diagram' : 'Nowy diagram' ?></h1>
    <a href="<?= $adminUrl ?>/diagrams" class="button button--ghost">← Wróć do listy</a>
</div>

<?php if ($error): ?><p class="alert alert--error"><?= $h($error) ?></p><?php endif; ?>

<div class="admin-card">
    <form method="post" action="<?= $action ?>" id="diagram-form" class="form-grid form-grid--wide">
        <?= Csrf::field() ?>
        <input type="hidden" name="nodes_json" id="nodes_json">
        <input type="hidden" name="edges_json" id="edges_json">

        <div class="form-row">
            <div class="field"><label>Nazwa diagramu (tylko w panelu)</label><input type="text" name="name" required value="<?= $h($diagram['name'] ?? '') ?>"></div>
            <div class="field"><label>Slug (do wstawienia w treści)</label><input type="text" name="slug" placeholder="generowany automatycznie" value="<?= $h($diagram['slug'] ?? '') ?>"></div>
        </div>
        <div class="form-row">
            <div class="field"><label>Tytuł karty</label><input type="text" name="title" value="<?= $h($diagram['title'] ?? '') ?>"></div>
            <div class="field"><label>Odznaka (np. "Na żywo")</label><input type="text" name="badge" value="<?= $h($diagram['badge'] ?? '') ?>"></div>
            <div class="field"><label>Stopka karty</label><input type="text" name="foot" value="<?= $h($diagram['foot'] ?? '') ?>"></div>
        </div>
        <div class="form-row">
            <div class="field"><label>Szerokość płótna (px)</label><input type="number" id="canvas_width" name="canvas_width" value="<?= (int) ($diagram['canvas_width'] ?? 480) ?>" min="200" max="1200"></div>
            <div class="field"><label>Wysokość płótna (px)</label><input type="number" id="canvas_height" name="canvas_height" value="<?= (int) ($diagram['canvas_height'] ?? 380) ?>" min="150" max="1200"></div>
        </div>

        <div class="diagram-editor">
            <div class="diagram-editor__toolbar">
                <button type="button" class="button button--ghost button--small" data-add-node>+ Dodaj węzeł</button>
                <button type="button" class="button button--ghost button--small" data-connect-mode>Połącz węzły</button>
                <span class="diagram-editor__hint" data-hint>Przeciągnij węzły, by je ustawić.</span>
            </div>
            <div class="diagram-editor__body">
                <div class="diagram-editor__canvas-wrap">
                    <div class="diagram-editor__canvas" id="diagram-canvas">
                        <svg class="diagram-editor__edges" id="diagram-edges" xmlns="http://www.w3.org/2000/svg"></svg>
                        <div id="diagram-nodes"></div>
                    </div>
                </div>
                <div class="diagram-editor__inspector" id="diagram-inspector">
                    <p class="diagram-editor__empty">Kliknij węzeł, aby go edytować.</p>
                </div>
            </div>
            <div class="diagram-editor__edges-list" id="diagram-edges-list"></div>
        </div>

        <div class="form-actions">
            <button type="submit" class="button">Zapisz diagram</button>
            <a href="<?= $adminUrl ?>/diagrams" class="button button--ghost">Anuluj</a>
        </div>
    </form>
</div>

<script type="application/json" id="diagram-initial-state"><?= json_encode($initialState, JSON_UNESCAPED_UNICODE | JSON_HEX_TAG) ?></script>
<script type="application/json" id="diagram-icon-library"><?= json_encode($iconLibrary, JSON_UNESCAPED_UNICODE | JSON_HEX_TAG) ?></script>
<script src="/assets/js/diagram-editor.js?v=<?= @filemtime(ROOT_PATH . '/assets/js/diagram-editor.js') ?: '1' ?>"></script>
