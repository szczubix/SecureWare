<?php
/** @var bool $success */
/** @var string|null $error */
/** @var array $old */
/** @var string $turnstileSiteKey */
/** @var array $content */
use SecureWare\Core\Csrf;
use SecureWare\Core\Icons;
use SecureWare\Core\Lang;
use SecureWare\Core\Locale;
use SecureWare\Models\Setting;

$settings = Setting::all();
$h = static fn ($v) => htmlspecialchars((string) $v, ENT_QUOTES, 'UTF-8');
?>
<section class="sw-hero" style="padding:64px 0;">
    <div class="sw-wrap">
        <span class="sw-hero__eyebrow sw-anim-in sw-delay-1"><?= $h($content['eyebrow']) ?></span>
        <h1 class="sw-anim-in sw-delay-2" style="font-size:36px;"><?= $h($content['heading_pre']) ?><span><?= $h($content['heading_highlight']) ?></span><?= $h($content['heading_post']) ?></h1>
        <p class="lead sw-anim-in sw-delay-3"><?= $h($content['lead']) ?></p>
    </div>
</section>

<section class="sw-section">
    <div class="sw-wrap sw-contact-grid">
        <div class="sw-contact-info reveal">
            <h2><?= $h($content['info_heading']) ?></h2>
            <p><?= $h($content['info_text']) ?></p>
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
                <p class="sw-alert sw-alert--success"><?= $h($content['success_message']) ?></p>
            <?php else: ?>
                <?php if ($error): ?><p class="sw-alert sw-alert--error"><?= htmlspecialchars($error, ENT_QUOTES, 'UTF-8') ?></p><?php endif; ?>
                <form class="sw-form reveal" method="post" action="<?= Locale::url('/kontakt') ?>">
                    <?= Csrf::field() ?>
                    <label><?= Lang::t('contact.label_name') ?>
                        <input type="text" name="name" required value="<?= htmlspecialchars($old['name'] ?? '', ENT_QUOTES, 'UTF-8') ?>">
                    </label>
                    <label><?= Lang::t('contact.label_company') ?>
                        <input type="text" name="company" value="<?= htmlspecialchars($old['company'] ?? '', ENT_QUOTES, 'UTF-8') ?>">
                    </label>
                    <label><?= Lang::t('contact.label_email') ?>
                        <input type="email" name="email" required value="<?= htmlspecialchars($old['email'] ?? '', ENT_QUOTES, 'UTF-8') ?>">
                    </label>
                    <label><?= Lang::t('contact.label_phone') ?>
                        <input type="tel" name="phone" value="<?= htmlspecialchars($old['phone'] ?? '', ENT_QUOTES, 'UTF-8') ?>">
                    </label>
                    <label><?= Lang::t('contact.label_message') ?>
                        <textarea name="message" required><?= htmlspecialchars($old['message'] ?? '', ENT_QUOTES, 'UTF-8') ?></textarea>
                    </label>
                    <?php if ($turnstileSiteKey): ?>
                        <div class="cf-turnstile" data-sitekey="<?= htmlspecialchars($turnstileSiteKey, ENT_QUOTES, 'UTF-8') ?>"></div>
                        <script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>
                    <?php endif; ?>
                    <button type="submit" class="sw-btn sw-btn--primary"><?= $h($content['submit_label']) ?></button>
                </form>
            <?php endif; ?>
        </div>
    </div>
</section>
