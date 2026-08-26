<?php
/** @var array $content */
use SecureWare\Core\Icons;
use SecureWare\Core\Lang;
use SecureWare\Core\Locale;
$h = static fn ($v) => htmlspecialchars((string) $v, ENT_QUOTES, 'UTF-8');
?>
<div class="sw-404">
    <div class="icon"><?= Icons::svg('shield-check', 34) ?></div>
    <h1><?= $h($content['heading']) ?></h1>
    <p><?= $h($content['text']) ?></p>
    <div class="sw-404__links">
        <a href="<?= Locale::url('/') ?>" class="sw-btn sw-btn--primary"><?= $h($content['primary_label']) ?></a>
        <a href="<?= Locale::url('/oferta') ?>" class="sw-btn sw-btn--ghost"><?= Lang::t('404.see_offer') ?></a>
        <a href="<?= Locale::url('/kontakt') ?>" class="sw-btn sw-btn--ghost"><?= Lang::t('404.contact') ?></a>
    </div>
</div>
