<?php
/** @var array|null $article */
/** @var array $categories */
/** @var array $media */
/** @var string $tagsValue */
/** @var string|null $error */
use SecureWare\Core\Config;
use SecureWare\Core\Csrf;

$adminUrl = '/' . Config::get('admin_path');
$isEdit   = $article !== null;
$action   = $isEdit ? $adminUrl . '/articles/' . $article['id'] : $adminUrl . '/articles';
$publishedAtValue = $isEdit && $article['published_at'] ? str_replace(' ', 'T', substr($article['published_at'], 0, 16)) : '';
?>
<div class="toolbar">
    <h1><?= $isEdit ? 'Edytuj artykuł' : 'Nowy artykuł' ?></h1>
    <a href="<?= $adminUrl ?>/articles" class="button button--ghost">← Wróć do listy</a>
</div>

<?php if ($error): ?><p class="alert alert--error"><?= htmlspecialchars($error, ENT_QUOTES, 'UTF-8') ?></p><?php endif; ?>

<div class="admin-card">
    <form method="post" action="<?= $action ?>" class="form-grid form-grid--wide">
        <?= Csrf::field() ?>

        <div class="form-row">
            <div class="field">
                <label>Tytuł</label>
                <input type="text" name="title" required value="<?= htmlspecialchars($article['title'] ?? '', ENT_QUOTES, 'UTF-8') ?>">
            </div>
            <div class="field">
                <label>Slug (adres URL)</label>
                <input type="text" name="slug" placeholder="generowany automatycznie" value="<?= htmlspecialchars($article['slug'] ?? '', ENT_QUOTES, 'UTF-8') ?>">
            </div>
        </div>

        <div class="field">
            <label>Zajawka (excerpt)</label>
            <textarea name="excerpt" rows="2"><?= htmlspecialchars($article['excerpt'] ?? '', ENT_QUOTES, 'UTF-8') ?></textarea>
            <span class="hint">Jeśli puste, zostanie wygenerowana automatycznie z treści.</span>
        </div>

        <div class="field">
            <label>Treść</label>
            <textarea name="content" id="content-editor"><?= $article['content'] ?? '' ?></textarea>
        </div>

        <div class="form-row">
            <div class="field">
                <label>Kategoria</label>
                <select name="category_id">
                    <option value="">— brak —</option>
                    <?php foreach ($categories as $c): ?>
                        <option value="<?= (int) $c['id'] ?>" <?= (isset($article['category_id']) && (int) $article['category_id'] === (int) $c['id']) ? 'selected' : '' ?>>
                            <?= htmlspecialchars($c['name'], ENT_QUOTES, 'UTF-8') ?>
                        </option>
                    <?php endforeach; ?>
                </select>
            </div>
            <div class="field">
                <label>...lub nowa kategoria</label>
                <input type="text" name="new_category" placeholder="np. Poradniki">
            </div>
        </div>

        <div class="field">
            <label>Tagi (oddzielone przecinkami)</label>
            <input type="text" name="tags" value="<?= htmlspecialchars($tagsValue, ENT_QUOTES, 'UTF-8') ?>" placeholder="ransomware, dr, backup">
        </div>

        <div class="form-row">
            <div class="field">
                <label>Zdjęcie wyróżniające</label>
                <select name="featured_image_id">
                    <option value="">— brak —</option>
                    <?php foreach ($media as $m): if (!str_starts_with($m['mime'], 'image/')) continue; ?>
                        <option value="<?= (int) $m['id'] ?>" <?= (isset($article['featured_image_id']) && (int) $article['featured_image_id'] === (int) $m['id']) ? 'selected' : '' ?>>
                            <?= htmlspecialchars($m['filename'], ENT_QUOTES, 'UTF-8') ?>
                        </option>
                    <?php endforeach; ?>
                </select>
                <span class="hint">Zarządzaj plikami w <a href="<?= $adminUrl ?>/media">bibliotece mediów</a>.</span>
            </div>
            <div class="field">
                <label>Status</label>
                <select name="status">
                    <option value="draft" <?= (($article['status'] ?? 'draft') === 'draft') ? 'selected' : '' ?>>Szkic</option>
                    <option value="published" <?= (($article['status'] ?? '') === 'published') ? 'selected' : '' ?>>Opublikowany</option>
                </select>
            </div>
        </div>

        <div class="field">
            <label>Data publikacji</label>
            <input type="datetime-local" name="published_at" value="<?= htmlspecialchars($publishedAtValue, ENT_QUOTES, 'UTF-8') ?>">
            <span class="hint">Puste + status "Opublikowany" = publikacja natychmiast.</span>
        </div>

        <div class="form-row">
            <div class="field">
                <label>SEO - meta title</label>
                <input type="text" name="meta_title" value="<?= htmlspecialchars($article['meta_title'] ?? '', ENT_QUOTES, 'UTF-8') ?>">
            </div>
            <div class="field">
                <label>SEO - meta description</label>
                <input type="text" name="meta_description" value="<?= htmlspecialchars($article['meta_description'] ?? '', ENT_QUOTES, 'UTF-8') ?>">
            </div>
        </div>

        <div class="form-actions">
            <button type="submit" class="button">Zapisz</button>
            <a href="<?= $adminUrl ?>/articles" class="button button--ghost">Anuluj</a>
        </div>
    </form>
</div>

<script src="/assets/js/admin-editor.js"></script>
<script>SecureWareEditor.init('content-editor');</script>
