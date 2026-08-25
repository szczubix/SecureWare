<?php
/** @var bool $success */
/** @var string|null $error */
/** @var array $old */
/** @var string $turnstileSiteKey */
use SecureWare\Core\Csrf;
use SecureWare\Core\Icons;
use SecureWare\Models\Setting;

$settings = Setting::all();
?>
<section class="sw-hero" style="padding:64px 0;">
    <div class="sw-wrap">
        <span class="sw-hero__eyebrow">Kontakt</span>
        <h1 style="font-size:36px;">Porozmawiajmy o <span>ochronie Twoich danych</span></h1>
        <p class="lead">Wypelnij formularz - odpowiadamy zazwyczaj w ciagu jednego dnia roboczego.</p>
    </div>
</section>

<section class="sw-section">
    <div class="sw-wrap sw-contact-grid">
        <div class="sw-contact-info">
            <h2>Dane kontaktowe</h2>
            <p>Chetnie odpowiemy na pytania dotyczace backupu, disaster recovery lub audytu obecnego srodowiska.</p>
            <?php if (!empty($settings['contact_email'])): ?>
                <div class="item"><span class="icon"><?= Icons::svg('mail', 18) ?></span> <?= htmlspecialchars($settings['contact_email'], ENT_QUOTES, 'UTF-8') ?></div>
            <?php endif; ?>
            <?php if (!empty($settings['contact_phone'])): ?>
                <div class="item"><span class="icon"><?= Icons::svg('phone', 18) ?></span> <?= htmlspecialchars($settings['contact_phone'], ENT_QUOTES, 'UTF-8') ?></div>
            <?php endif; ?>
            <?php if (!empty($settings['contact_address'])): ?>
                <div class="item"><span class="icon"><?= Icons::svg('map-pin', 18) ?></span> <?= htmlspecialchars($settings['contact_address'], ENT_QUOTES, 'UTF-8') ?></div>
            <?php endif; ?>
        </div>

        <div>
            <?php if ($success): ?>
                <p class="sw-alert sw-alert--success">Dziekujemy! Twoja wiadomosc zostala wyslana - odpowiemy najszybciej jak to mozliwe.</p>
            <?php else: ?>
                <?php if ($error): ?><p class="sw-alert sw-alert--error"><?= htmlspecialchars($error, ENT_QUOTES, 'UTF-8') ?></p><?php endif; ?>
                <form class="sw-form" method="post" action="/kontakt">
                    <?= Csrf::field() ?>
                    <label>Imie i nazwisko
                        <input type="text" name="name" required value="<?= htmlspecialchars($old['name'] ?? '', ENT_QUOTES, 'UTF-8') ?>">
                    </label>
                    <label>E-mail
                        <input type="email" name="email" required value="<?= htmlspecialchars($old['email'] ?? '', ENT_QUOTES, 'UTF-8') ?>">
                    </label>
                    <label>Telefon (opcjonalnie)
                        <input type="tel" name="phone" value="<?= htmlspecialchars($old['phone'] ?? '', ENT_QUOTES, 'UTF-8') ?>">
                    </label>
                    <label>Wiadomosc
                        <textarea name="message" required><?= htmlspecialchars($old['message'] ?? '', ENT_QUOTES, 'UTF-8') ?></textarea>
                    </label>
                    <?php if ($turnstileSiteKey): ?>
                        <div class="cf-turnstile" data-sitekey="<?= htmlspecialchars($turnstileSiteKey, ENT_QUOTES, 'UTF-8') ?>"></div>
                        <script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>
                    <?php endif; ?>
                    <button type="submit" class="sw-btn sw-btn--primary">Wyslij wiadomosc</button>
                </form>
            <?php endif; ?>
        </div>
    </div>
</section>
