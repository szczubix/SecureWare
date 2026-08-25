<?php
/** @var array|null $service */
/** @var string|null $error */
use SecureWare\Core\Config;
use SecureWare\Core\Csrf;

$adminUrl = '/' . Config::get('admin_path');
$isEdit   = $service !== null;
$action   = $isEdit ? $adminUrl . '/services/' . $service['id'] : $adminUrl . '/services';
$meta     = $service['meta'] ?? [];
$icons    = ['shield-check','cloud-upload','map-pin','lock','mail','server','layers','life-buoy','refresh-ccw','clipboard-check','tool','activity','file-check','shield'];
?>
<div class="toolbar">
    <h1><?= $isEdit ? 'Edytuj usluge' : 'Nowa usluga' ?></h1>
    <a href="<?= $adminUrl ?>/services" class="button button--ghost">← Wroc do listy</a>
</div>

<?php if ($error): ?><p class="alert alert--error"><?= htmlspecialchars($error, ENT_QUOTES, 'UTF-8') ?></p><?php endif; ?>

<div class="admin-card">
    <form method="post" action="<?= $action ?>" class="form-grid form-grid--wide">
        <?= Csrf::field() ?>

        <div class="form-row">
            <div class="field">
                <label>Nazwa</label>
                <input type="text" name="name" required value="<?= htmlspecialchars($service['name'] ?? '', ENT_QUOTES, 'UTF-8') ?>">
            </div>
            <div class="field">
                <label>Slug (adres URL: /oferta/...)</label>
                <input type="text" name="slug" placeholder="generowany automatycznie" value="<?= htmlspecialchars($service['slug'] ?? '', ENT_QUOTES, 'UTF-8') ?>">
            </div>
        </div>

        <div class="field">
            <label>Krotki opis (widoczny na liscie ofert)</label>
            <textarea name="short_description" rows="2" required><?= htmlspecialchars($service['short_description'] ?? '', ENT_QUOTES, 'UTF-8') ?></textarea>
        </div>

        <div class="field">
            <label>Tresc pelna</label>
            <textarea name="content" id="content-editor"><?= $service['content'] ?? '' ?></textarea>
        </div>

        <div class="form-row">
            <div class="field">
                <label>Ikona</label>
                <select name="icon">
                    <?php foreach ($icons as $icon): ?>
                        <option value="<?= $icon ?>" <?= (($service['icon'] ?? 'shield') === $icon) ? 'selected' : '' ?>><?= $icon ?></option>
                    <?php endforeach; ?>
                </select>
            </div>
            <div class="field">
                <label>Kolejnosc wyswietlania</label>
                <input type="number" name="position" value="<?= (int) ($service['position'] ?? 0) ?>">
            </div>
        </div>

        <div class="field">
            <label>Status</label>
            <select name="status">
                <option value="draft" <?= (($service['status'] ?? 'draft') === 'draft') ? 'selected' : '' ?>>Szkic</option>
                <option value="published" <?= (($service['status'] ?? '') === 'published') ? 'selected' : '' ?>>Opublikowana</option>
            </select>
        </div>

        <div class="field">
            <label>Pola niestandardowe (custom fields)</label>
            <div class="repeatable-rows" id="meta-rows">
                <?php foreach ($meta as $key => $value): ?>
                    <div class="row">
                        <input type="text" name="meta_key[]" value="<?= htmlspecialchars($key, ENT_QUOTES, 'UTF-8') ?>" placeholder="Nazwa pola">
                        <input type="text" name="meta_value[]" value="<?= htmlspecialchars($value, ENT_QUOTES, 'UTF-8') ?>" placeholder="Wartosc">
                        <button type="button" class="button button--ghost button--small" data-remove-row>Usun</button>
                    </div>
                <?php endforeach; ?>
            </div>
            <button type="button" class="button button--ghost button--small" data-add-row="meta-rows" style="align-self:flex-start;margin-top:6px;">+ Dodaj pole</button>
        </div>

        <div class="form-row">
            <div class="field">
                <label>SEO - meta title</label>
                <input type="text" name="meta_title" value="<?= htmlspecialchars($service['meta_title'] ?? '', ENT_QUOTES, 'UTF-8') ?>">
            </div>
            <div class="field">
                <label>SEO - meta description</label>
                <input type="text" name="meta_description" value="<?= htmlspecialchars($service['meta_description'] ?? '', ENT_QUOTES, 'UTF-8') ?>">
            </div>
        </div>

        <div class="form-actions">
            <button type="submit" class="button">Zapisz</button>
            <a href="<?= $adminUrl ?>/services" class="button button--ghost">Anuluj</a>
        </div>
    </form>
</div>

<script src="/assets/js/admin-editor.js"></script>
<script src="/assets/js/admin.js"></script>
<script>
SecureWareEditor.init('content-editor');
SecureWareAdmin.initRepeatable('meta-rows');
</script>
