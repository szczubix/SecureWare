<?php
/** @var array $settings */
/** @var string|null $saved */
use SecureWare\Core\Csrf;
?>
<div class="toolbar">
    <h1>Ustawienia - Integracje</h1>
</div>

<?php if ($saved): ?><p class="alert alert--success">Zapisano ustawienia.</p><?php endif; ?>

<div class="admin-card">
    <h2>Cloudflare Turnstile</h2>
    <p class="hint">Zabezpiecza formularz kontaktowy przed botami. Klucze wygenerujesz w panelu Cloudflare (Turnstile).</p>
    <form method="post" action="integrations" class="form-grid">
        <?= Csrf::field() ?>
        <div class="form-row">
            <div class="field">
                <label>Site key</label>
                <input type="text" name="turnstile_site_key" value="<?= htmlspecialchars($settings['turnstile_site_key'] ?? '', ENT_QUOTES, 'UTF-8') ?>">
            </div>
            <div class="field">
                <label>Secret key</label>
                <input type="text" name="turnstile_secret" value="<?= htmlspecialchars($settings['turnstile_secret'] ?? '', ENT_QUOTES, 'UTF-8') ?>">
            </div>
        </div>

        <h2>Poczta</h2>
        <p class="hint">Adres, z ktorego wysylane sa powiadomienia o nowych zapytaniach z formularza kontaktowego (naglowek "From"). Odbiorca to e-mail kontaktowy z zakladki Branding.</p>
        <div class="field">
            <label>Adres nadawcy (From)</label>
            <input type="email" name="mail_from_address" placeholder="no-reply@twojadomena.pl" value="<?= htmlspecialchars($settings['mail_from_address'] ?? '', ENT_QUOTES, 'UTF-8') ?>">
        </div>

        <h2>Google Analytics</h2>
        <div class="field">
            <label>GA4 Measurement ID</label>
            <input type="text" name="ga_measurement_id" placeholder="G-XXXXXXXXXX" value="<?= htmlspecialchars($settings['ga_measurement_id'] ?? '', ENT_QUOTES, 'UTF-8') ?>">
        </div>

        <h2>CookieYes (baner zgod cookies)</h2>
        <div class="field">
            <label>Skrypt CookieYes</label>
            <textarea name="cookieyes_script" rows="3" placeholder='&lt;script id="cookieyes" type="text/javascript" src="https://cdn-cookieyes.com/client_data/XXXXXXXXXXXXXXXXXXXX/script.js"&gt;&lt;/script&gt;'><?= htmlspecialchars($settings['cookieyes_script'] ?? '', ENT_QUOTES, 'UTF-8') ?></textarea>
            <span class="hint">Wklej caly tag &lt;script&gt; wygenerowany w panelu cookieyes.com - zostanie wstawiony w sekcji &lt;head&gt; strony.</span>
        </div>

        <div class="form-actions">
            <button type="submit" class="button">Zapisz</button>
        </div>
    </form>
</div>
