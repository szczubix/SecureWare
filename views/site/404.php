<?php
/** @var array $content */
use SecureWare\Core\Icons;
$h = static fn ($v) => htmlspecialchars((string) $v, ENT_QUOTES, 'UTF-8');
?>
<div class="sw-404">
    <div class="icon"><?= Icons::svg('shield-check', 34) ?></div>
    <h1><?= $h($content['heading']) ?></h1>
    <p><?= $h($content['text']) ?></p>
    <div class="sw-404__links">
        <a href="/" class="sw-btn sw-btn--primary"><?= $h($content['primary_label']) ?></a>
        <a href="/oferta" class="sw-btn sw-btn--ghost">Zobacz ofertę</a>
        <a href="/kontakt" class="sw-btn sw-btn--ghost">Kontakt</a>
    </div>
</div>
