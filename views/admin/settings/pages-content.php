<?php
/** @var array $content */
/** @var string|null $saved */
use SecureWare\Core\Csrf;

$icons = ['shield-check','cloud-upload','map-pin','lock','mail','server','layers','life-buoy','refresh-ccw','clipboard-check','tool','activity','file-check','shield'];
$iconSelect = function (string $name, string $selected) use ($icons) {
    echo '<select name="' . htmlspecialchars($name, ENT_QUOTES, 'UTF-8') . '">';
    foreach ($icons as $icon) {
        $sel = $selected === $icon ? ' selected' : '';
        echo '<option value="' . $icon . '"' . $sel . '>' . $icon . '</option>';
    }
    echo '</select>';
};
$h = static fn ($v) => htmlspecialchars((string) $v, ENT_QUOTES, 'UTF-8');
?>
<div class="toolbar">
    <h1>Treść podstron (oferta, blog, kontakt, 404)</h1>
</div>

<?php if ($saved): ?><p class="alert alert--success">Zapisano treść podstron.</p><?php endif; ?>
<p class="admin-hint" style="margin:-8px 0 20px;color:#6b7686;">Nagłówki i wstępy tych podstron — bez zmian w kodzie. Same usługi/artykuły edytujesz w swoich zakładkach.</p>

<form method="post" action="pages-content">
    <?= Csrf::field() ?>

    <div class="admin-card">
        <h2 style="margin-top:0;">Strona /oferta</h2>
        <div class="form-grid form-grid--wide">
            <div class="form-row">
                <div class="field"><label>Eyebrow</label><input type="text" name="offer_eyebrow" value="<?= $h($content['offer']['eyebrow']) ?>"></div>
            </div>
            <div class="form-row">
                <div class="field"><label>Tytuł — przed wyróżnionym słowem</label><input type="text" name="offer_heading_pre" value="<?= $h($content['offer']['heading_pre']) ?>"></div>
                <div class="field"><label>Tytuł — wyróżnione słowo</label><input type="text" name="offer_heading_highlight" value="<?= $h($content['offer']['heading_highlight']) ?>"></div>
                <div class="field"><label>Tytuł — po wyróżnionym słowie</label><input type="text" name="offer_heading_post" value="<?= $h($content['offer']['heading_post']) ?>"></div>
            </div>
            <div class="field"><label>Lead</label><textarea name="offer_lead" rows="2"><?= $h($content['offer']['lead']) ?></textarea></div>

            <h3>Cztery znaczniki pod nagłówkiem</h3>
            <?php foreach ($content['offer']['highlights'] as $i => $item): ?>
                <div class="form-row">
                    <div class="field"><label>Pozycja <?= $i + 1 ?> — ikona</label><?php $iconSelect('offer_highlight_icon[]', $item['icon']); ?></div>
                    <div class="field"><label>Pozycja <?= $i + 1 ?> — tekst</label><input type="text" name="offer_highlight_text[]" value="<?= $h($item['text']) ?>"></div>
                </div>
            <?php endforeach; ?>

            <div class="field"><label>Tekst gdy brak opublikowanych usług</label><input type="text" name="offer_empty_text" value="<?= $h($content['offer']['empty_text']) ?>"></div>

            <h3>Sekcja końcowa (CTA)</h3>
            <div class="field"><label>Nagłówek</label><input type="text" name="offer_cta_heading" value="<?= $h($content['offer']['cta_heading']) ?>"></div>
            <div class="field"><label>Tekst</label><input type="text" name="offer_cta_text" value="<?= $h($content['offer']['cta_text']) ?>"></div>
            <div class="field"><label>Tekst przycisku</label><input type="text" name="offer_cta_button_label" value="<?= $h($content['offer']['cta_button_label']) ?>"></div>
        </div>
    </div>

    <div class="admin-card">
        <h2 style="margin-top:0;">Strona /blog</h2>
        <div class="form-grid form-grid--wide">
            <div class="field"><label>Eyebrow</label><input type="text" name="blog_eyebrow" value="<?= $h($content['blog']['eyebrow']) ?>"></div>
            <div class="form-row">
                <div class="field"><label>Tytuł — przed wyróżnionym słowem</label><input type="text" name="blog_heading_pre" value="<?= $h($content['blog']['heading_pre']) ?>"></div>
                <div class="field"><label>Tytuł — wyróżnione słowo</label><input type="text" name="blog_heading_highlight" value="<?= $h($content['blog']['heading_highlight']) ?>"></div>
                <div class="field"><label>Tytuł — po wyróżnionym słowie</label><input type="text" name="blog_heading_post" value="<?= $h($content['blog']['heading_post']) ?>"></div>
            </div>
            <div class="field"><label>Lead</label><textarea name="blog_lead" rows="2"><?= $h($content['blog']['lead']) ?></textarea></div>
        </div>
    </div>

    <div class="admin-card">
        <h2 style="margin-top:0;">Strona /kontakt</h2>
        <div class="form-grid form-grid--wide">
            <div class="field"><label>Eyebrow</label><input type="text" name="contact_eyebrow" value="<?= $h($content['contact']['eyebrow']) ?>"></div>
            <div class="form-row">
                <div class="field"><label>Tytuł — przed wyróżnionym słowem</label><input type="text" name="contact_heading_pre" value="<?= $h($content['contact']['heading_pre']) ?>"></div>
                <div class="field"><label>Tytuł — wyróżnione słowo</label><input type="text" name="contact_heading_highlight" value="<?= $h($content['contact']['heading_highlight']) ?>"></div>
                <div class="field"><label>Tytuł — po wyróżnionym słowie</label><input type="text" name="contact_heading_post" value="<?= $h($content['contact']['heading_post']) ?>"></div>
            </div>
            <div class="field"><label>Lead</label><textarea name="contact_lead" rows="2"><?= $h($content['contact']['lead']) ?></textarea></div>
            <div class="form-row">
                <div class="field"><label>Nagłówek panelu danych kontaktowych</label><input type="text" name="contact_info_heading" value="<?= $h($content['contact']['info_heading']) ?>"></div>
                <div class="field"><label>Tekst panelu danych kontaktowych</label><input type="text" name="contact_info_text" value="<?= $h($content['contact']['info_text']) ?>"></div>
            </div>
            <div class="field"><label>Komunikat po wysłaniu formularza</label><input type="text" name="contact_success_message" value="<?= $h($content['contact']['success_message']) ?>"></div>
            <div class="field"><label>Tekst przycisku wysyłki</label><input type="text" name="contact_submit_label" value="<?= $h($content['contact']['submit_label']) ?>"></div>
        </div>
    </div>

    <div class="admin-card">
        <h2 style="margin-top:0;">Strona 404 (nie znaleziono)</h2>
        <div class="form-grid form-grid--wide">
            <div class="form-row">
                <div class="field"><label>Nagłówek</label><input type="text" name="nf_heading" value="<?= $h($content['not_found']['heading']) ?>"></div>
                <div class="field"><label>Tekst przycisku głównego</label><input type="text" name="nf_primary_label" value="<?= $h($content['not_found']['primary_label']) ?>"></div>
            </div>
            <div class="field"><label>Tekst</label><textarea name="nf_text" rows="2"><?= $h($content['not_found']['text']) ?></textarea></div>
        </div>
    </div>

    <div class="form-actions">
        <button type="submit" class="button">Zapisz treść podstron</button>
    </div>
</form>
