<?php
/** @var array $settings */
/** @var array $media */
/** @var string|null $saved */
use SecureWare\Core\Csrf;

$navMenu = json_decode($settings['nav_menu'] ?? '[]', true) ?: [];
?>
<div class="toolbar">
    <h1>Ustawienia - Branding</h1>
</div>

<?php if ($saved): ?><p class="alert alert--success">Zapisano ustawienia.</p><?php endif; ?>

<div class="admin-card">
    <form method="post" action="branding" class="form-grid form-grid--wide">
        <?= Csrf::field() ?>

        <div class="form-row">
            <div class="field">
                <label>Nazwa strony</label>
                <input type="text" name="site_name" value="<?= htmlspecialchars($settings['site_name'] ?? '', ENT_QUOTES, 'UTF-8') ?>">
            </div>
            <div class="field">
                <label>Haslo / tagline</label>
                <input type="text" name="site_tagline" value="<?= htmlspecialchars($settings['site_tagline'] ?? '', ENT_QUOTES, 'UTF-8') ?>">
            </div>
        </div>

        <div class="form-row">
            <div class="field">
                <label>Logo</label>
                <select name="logo_media_id">
                    <option value="">— brak —</option>
                    <?php foreach ($media as $m): if (!str_starts_with($m['mime'], 'image/')) continue; ?>
                        <option value="<?= (int) $m['id'] ?>" <?= ((string) ($settings['logo_media_id'] ?? '') === (string) $m['id']) ? 'selected' : '' ?>>
                            <?= htmlspecialchars($m['filename'], ENT_QUOTES, 'UTF-8') ?>
                        </option>
                    <?php endforeach; ?>
                </select>
            </div>
            <div class="field">
                <label>Favicon</label>
                <select name="favicon_media_id">
                    <option value="">— brak —</option>
                    <?php foreach ($media as $m): if (!str_starts_with($m['mime'], 'image/')) continue; ?>
                        <option value="<?= (int) $m['id'] ?>" <?= ((string) ($settings['favicon_media_id'] ?? '') === (string) $m['id']) ? 'selected' : '' ?>>
                            <?= htmlspecialchars($m['filename'], ENT_QUOTES, 'UTF-8') ?>
                        </option>
                    <?php endforeach; ?>
                </select>
            </div>
        </div>

        <div class="form-row">
            <div class="field">
                <label>Kolor podstawowy</label>
                <input type="text" name="color_primary" value="<?= htmlspecialchars($settings['color_primary'] ?? '#0b5fff', ENT_QUOTES, 'UTF-8') ?>">
            </div>
            <div class="field">
                <label>Kolor ciemny (tlo/naglowki)</label>
                <input type="text" name="color_dark" value="<?= htmlspecialchars($settings['color_dark'] ?? '#0a0f1e', ENT_QUOTES, 'UTF-8') ?>">
            </div>
        </div>

        <div class="form-row">
            <div class="field">
                <label>E-mail kontaktowy</label>
                <input type="email" name="contact_email" value="<?= htmlspecialchars($settings['contact_email'] ?? '', ENT_QUOTES, 'UTF-8') ?>">
            </div>
            <div class="field">
                <label>Telefon kontaktowy</label>
                <input type="text" name="contact_phone" value="<?= htmlspecialchars($settings['contact_phone'] ?? '', ENT_QUOTES, 'UTF-8') ?>">
            </div>
        </div>

        <div class="field">
            <label>Adres</label>
            <input type="text" name="contact_address" value="<?= htmlspecialchars($settings['contact_address'] ?? '', ENT_QUOTES, 'UTF-8') ?>">
        </div>

        <div class="form-row">
            <div class="field">
                <label>LinkedIn (URL)</label>
                <input type="url" name="social_linkedin" value="<?= htmlspecialchars($settings['social_linkedin'] ?? '', ENT_QUOTES, 'UTF-8') ?>">
            </div>
            <div class="field">
                <label>X / Twitter (URL)</label>
                <input type="url" name="social_twitter" value="<?= htmlspecialchars($settings['social_twitter'] ?? '', ENT_QUOTES, 'UTF-8') ?>">
            </div>
        </div>

        <div class="field">
            <label>Stopka - tekst</label>
            <input type="text" name="footer_text" value="<?= htmlspecialchars($settings['footer_text'] ?? '', ENT_QUOTES, 'UTF-8') ?>">
        </div>

        <div class="field">
            <label>Menu glowne</label>
            <div class="repeatable-rows" id="nav-rows">
                <?php foreach ($navMenu as $item): ?>
                    <div class="row">
                        <input type="text" name="nav_label[]" value="<?= htmlspecialchars($item['label'] ?? '', ENT_QUOTES, 'UTF-8') ?>" placeholder="Etykieta">
                        <input type="text" name="nav_url[]" value="<?= htmlspecialchars($item['url'] ?? '', ENT_QUOTES, 'UTF-8') ?>" placeholder="/adres">
                        <button type="button" class="button button--ghost button--small" data-remove-row>Usun</button>
                    </div>
                <?php endforeach; ?>
            </div>
            <button type="button" class="button button--ghost button--small" data-add-row="nav-rows" style="align-self:flex-start;margin-top:6px;">+ Dodaj pozycje menu</button>
        </div>

        <div class="form-actions">
            <button type="submit" class="button">Zapisz</button>
        </div>
    </form>
</div>

<script>
(function(){
    var container = document.getElementById('nav-rows');
    var addBtn = document.querySelector('[data-add-row="nav-rows"]');
    if (!container || !addBtn) return;
    container.addEventListener('click', function(e){
        if (e.target.matches('[data-remove-row]')) { e.preventDefault(); e.target.closest('.row').remove(); }
    });
    addBtn.addEventListener('click', function(e){
        e.preventDefault();
        var row = document.createElement('div');
        row.className = 'row';
        row.innerHTML = '<input type="text" name="nav_label[]" placeholder="Etykieta"><input type="text" name="nav_url[]" placeholder="/adres"><button type="button" class="button button--ghost button--small" data-remove-row>Usun</button>';
        container.appendChild(row);
    });
})();
</script>
