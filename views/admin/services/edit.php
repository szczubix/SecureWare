<?php
/** @var array|null $service */
/** @var string|null $error */
/** @var string $lang */
/** @var array $translation */
use SecureWare\Core\Config;
use SecureWare\Core\Csrf;

$adminUrl = '/' . Config::get('admin_path');
$isEdit   = $service !== null;
$action   = $isEdit ? $adminUrl . '/services/' . $service['id'] . ($lang === 'en' ? '?lang=en' : '') : $adminUrl . '/services';
$meta     = $service['meta'] ?? [];
$icons    = ['shield-check','cloud-upload','map-pin','lock','mail','server','layers','life-buoy','refresh-ccw','clipboard-check','tool','activity','file-check','shield'];
$isEn     = $lang === 'en';
$t        = static fn (string $field) => $translation[$field] ?? ($isEn ? '' : ($service[$field] ?? ''));
$h        = static fn ($v) => htmlspecialchars((string) $v, ENT_QUOTES, 'UTF-8');
?>
<div class="toolbar">
    <h1><?= $isEdit ? 'Edytuj usługę' : 'Nowa usługa' ?></h1>
    <a href="<?= $adminUrl ?>/services" class="button button--ghost">← Wróć do listy</a>
</div>

<?php if ($isEdit): ?>
<div class="admin-lang-tabs">
    <a href="<?= $adminUrl ?>/services/<?= (int) $service['id'] ?>/edit" class="<?= !$isEn ? 'is-active' : '' ?>">Polski</a>
    <a href="<?= $adminUrl ?>/services/<?= (int) $service['id'] ?>/edit?lang=en" class="<?= $isEn ? 'is-active' : '' ?>">English (EN)</a>
</div>
<?php endif; ?>

<?php if ($error): ?><p class="alert alert--error"><?= $h($error) ?></p><?php endif; ?>

<div class="admin-card">
    <form method="post" action="<?= $action ?>" class="form-grid form-grid--wide">
        <?= Csrf::field() ?>
        <?php if ($isEn): ?><input type="hidden" name="lang" value="en"><?php endif; ?>

        <?php if ($isEn): ?>
            <p class="admin-hint" style="margin:0 0 4px;color:#6b7686;">Tłumaczenie tej usługi na angielski - slug, ikona, kolejność i status są wspólne dla obu języków.</p>
            <div class="field">
                <label>Name</label>
                <input type="text" name="name" value="<?= $h($t('name')) ?>" placeholder="<?= $h($service['name']) ?>">
            </div>
            <div class="field">
                <label>Short description</label>
                <textarea name="short_description" rows="2"><?= $h($t('short_description')) ?></textarea>
            </div>
            <div class="field">
                <label>Full content</label>
                <textarea name="content" id="content-editor"><?= $t('content') ?></textarea>
            </div>
            <div class="form-row">
                <div class="field">
                    <label>SEO - meta title</label>
                    <input type="text" name="meta_title" value="<?= $h($t('meta_title')) ?>">
                </div>
                <div class="field">
                    <label>SEO - meta description</label>
                    <input type="text" name="meta_description" value="<?= $h($t('meta_description')) ?>">
                </div>
            </div>
        <?php else: ?>
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
            <label>Krótki opis (widoczny na liście ofert)</label>
            <textarea name="short_description" rows="2" required><?= htmlspecialchars($service['short_description'] ?? '', ENT_QUOTES, 'UTF-8') ?></textarea>
        </div>

        <div class="field">
            <label>Treść pełna</label>
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
                <label>Kolejność wyświetlania</label>
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
                <input type="text" name="meta_title" value="<?= htmlspecialchars($service['meta_title'] ?? '', ENT_QUOTES, 'UTF-8') ?>">
            </div>
            <div class="field">
                <label>SEO - meta description</label>
                <input type="text" name="meta_description" value="<?= htmlspecialchars($service['meta_description'] ?? '', ENT_QUOTES, 'UTF-8') ?>">
            </div>
        </div>
        <?php endif; ?>

        <div class="form-actions">
            <button type="submit" class="button">Zapisz</button>
            <a href="<?= $adminUrl ?>/services" class="button button--ghost">Anuluj</a>
        </div>
    </form>
</div>

<script src="/assets/js/admin-editor.js?v=<?= @filemtime(ROOT_PATH . '/assets/js/admin-editor.js') ?: '1' ?>"></script>
<script src="/assets/js/admin.js?v=<?= @filemtime(ROOT_PATH . '/assets/js/admin.js') ?: '1' ?>"></script>
<script>
SecureWareEditor.init('content-editor');
<?php if (!$isEn): ?>SecureWareAdmin.initRepeatable('meta-rows');<?php endif; ?>
</script>
