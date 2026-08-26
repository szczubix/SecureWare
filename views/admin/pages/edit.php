<?php
/** @var array|null $page */
/** @var array $allPages */
/** @var string|null $error */
use SecureWare\Core\Config;
use SecureWare\Core\Csrf;

$adminUrl = '/' . Config::get('admin_path');
$isEdit   = $page !== null;
$action   = $isEdit ? $adminUrl . '/pages/' . $page['id'] : $adminUrl . '/pages';
$meta     = $page['meta'] ?? [];
?>
<div class="toolbar">
    <h1><?= $isEdit ? 'Edytuj podstronę' : 'Nowa podstrona' ?></h1>
    <a href="<?= $adminUrl ?>/pages" class="button button--ghost">← Wróć do listy</a>
</div>

<?php if ($error): ?><p class="alert alert--error"><?= htmlspecialchars($error, ENT_QUOTES, 'UTF-8') ?></p><?php endif; ?>

<div class="admin-card">
    <form method="post" action="<?= $action ?>" class="form-grid form-grid--wide">
        <?= Csrf::field() ?>

        <div class="form-row">
            <div class="field">
                <label>Tytuł</label>
                <input type="text" name="title" required value="<?= htmlspecialchars($page['title'] ?? '', ENT_QUOTES, 'UTF-8') ?>">
            </div>
            <div class="field">
                <label>Slug (adres URL)</label>
                <input type="text" name="slug" placeholder="generowany automatycznie" value="<?= htmlspecialchars($page['slug'] ?? '', ENT_QUOTES, 'UTF-8') ?>">
            </div>
        </div>

        <div class="field">
            <label>Treść</label>
            <textarea name="content" id="content-editor"><?= $page['content'] ?? '' ?></textarea>
        </div>

        <div class="form-row">
            <div class="field">
                <label>Szablon</label>
                <select name="template">
                    <?php foreach (['default' => 'Domyślny', 'full-width' => 'Pełna szerokość', 'landing' => 'Landing page'] as $val => $label): ?>
                        <option value="<?= $val ?>" <?= (($page['template'] ?? 'default') === $val) ? 'selected' : '' ?>><?= $label ?></option>
                    <?php endforeach; ?>
                </select>
            </div>
            <div class="field">
                <label>Strona nadrzędna</label>
                <select name="parent_id">
                    <option value="">— brak (strona głównego poziomu) —</option>
                    <?php foreach ($allPages as $p): if ($isEdit && (int) $p['id'] === (int) $page['id']) continue; ?>
                        <option value="<?= (int) $p['id'] ?>" <?= (isset($page['parent_id']) && (int) $page['parent_id'] === (int) $p['id']) ? 'selected' : '' ?>>
                            <?= htmlspecialchars($p['title'], ENT_QUOTES, 'UTF-8') ?>
                        </option>
                    <?php endforeach; ?>
                </select>
            </div>
        </div>

        <div class="field">
            <label>Status</label>
            <select name="status">
                <option value="draft" <?= (($page['status'] ?? 'draft') === 'draft') ? 'selected' : '' ?>>Szkic</option>
                <option value="published" <?= (($page['status'] ?? '') === 'published') ? 'selected' : '' ?>>Opublikowana</option>
            </select>
        </div>

        <div class="field">
            <label>Pola niestandardowe (custom fields)</label>
            <div class="repeatable-rows" id="meta-rows">
                <?php foreach ($meta as $key => $value): ?>
                    <div class="row">
                        <input type="text" name="meta_key[]" value="<?= htmlspecialchars($key, ENT_QUOTES, 'UTF-8') ?>" placeholder="Nazwa pola">
                        <input type="text" name="meta_value[]" value="<?= htmlspecialchars($value, ENT_QUOTES, 'UTF-8') ?>" placeholder="Wartość">
                        <button type="button" class="button button--ghost button--small" data-remove-row>Usuń</button>
                    </div>
                <?php endforeach; ?>
            </div>
            <button type="button" class="button button--ghost button--small" data-add-row="meta-rows" style="align-self:flex-start;margin-top:6px;">+ Dodaj pole</button>
        </div>

        <div class="form-row">
            <div class="field">
                <label>SEO - meta title</label>
                <input type="text" name="meta_title" value="<?= htmlspecialchars($page['meta_title'] ?? '', ENT_QUOTES, 'UTF-8') ?>">
            </div>
            <div class="field">
                <label>SEO - meta description</label>
                <input type="text" name="meta_description" value="<?= htmlspecialchars($page['meta_description'] ?? '', ENT_QUOTES, 'UTF-8') ?>">
            </div>
        </div>

        <div class="form-actions">
            <button type="submit" class="button">Zapisz</button>
            <a href="<?= $adminUrl ?>/pages" class="button button--ghost">Anuluj</a>
        </div>
    </form>
</div>

<script src="/assets/js/admin-editor.js?v=<?= @filemtime(ROOT_PATH . '/assets/js/admin-editor.js') ?: '1' ?>"></script>
<script src="/assets/js/admin.js?v=<?= @filemtime(ROOT_PATH . '/assets/js/admin.js') ?: '1' ?>"></script>
<script>
SecureWareEditor.init('content-editor');
SecureWareAdmin.initRepeatable('meta-rows');
</script>
