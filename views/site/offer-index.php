<?php
/** @var array $groups */
use SecureWare\Core\Icons;

$hasAny = (bool) array_filter($groups);
?>
<section class="sw-hero" style="padding:64px 0;">
    <div class="sw-wrap">
        <span class="sw-hero__eyebrow sw-anim-in sw-delay-1">Oferta</span>
        <h1 class="sw-anim-in sw-delay-2" style="font-size:36px;">Pełen zakres ochrony <span>danych</span> dla firm</h1>
        <p class="lead sw-anim-in sw-delay-3">13 usług pokrywających cały cykl życia backupu — od wdrożenia, przez codzienne zarządzanie, po disaster recovery i testy odtwarzania.</p>
        <div class="sw-highlights sw-anim-in sw-delay-4">
            <span><?= Icons::svg('shield-check', 16) ?> Kopie niezmienne (immutable)</span>
            <span><?= Icons::svg('refresh-ccw', 16) ?> Realne testy odtwarzania</span>
            <span><?= Icons::svg('activity', 16) ?> Monitoring 24/7</span>
            <span><?= Icons::svg('file-check', 16) ?> Jasne raporty SLA</span>
        </div>
    </div>
</section>

<?php foreach ($groups as $label => $services): if (!$services) continue; ?>
<section class="sw-section <?= array_key_first($groups) === $label ? '' : 'sw-section--muted' ?>">
    <div class="sw-wrap">
        <div class="sw-section-head reveal" style="margin-bottom:30px;">
            <h5><?= htmlspecialchars($label, ENT_QUOTES, 'UTF-8') ?></h5>
        </div>
        <div class="sw-services-grid reveal-stagger">
            <?php foreach ($services as $s): ?>
                <div class="sw-service-card">
                    <div class="sw-service-card__icon"><?= Icons::svg($s['icon'], 22) ?></div>
                    <h3><?= htmlspecialchars($s['name'], ENT_QUOTES, 'UTF-8') ?></h3>
                    <p><?= htmlspecialchars($s['short_description'], ENT_QUOTES, 'UTF-8') ?></p>
                    <a class="more" href="/oferta/<?= htmlspecialchars($s['slug'], ENT_QUOTES, 'UTF-8') ?>">Dowiedz się więcej <?= Icons::svg('arrow-right', 14) ?></a>
                </div>
            <?php endforeach; ?>
        </div>
    </div>
</section>
<?php endforeach; ?>

<?php if (!$hasAny): ?>
<section class="sw-section"><div class="sw-wrap"><p>Oferta jest aktualnie aktualizowana.</p></div></section>
<?php endif; ?>

<section class="sw-section--tight">
    <div class="sw-wrap">
        <div class="sw-cta reveal">
            <div>
                <h2>Nie wiesz, która usługa jest dla Ciebie?</h2>
                <p>Porozmawiajmy — dobierzemy rozwiązanie do skali i budżetu Twojej firmy.</p>
            </div>
            <a href="/kontakt" class="sw-btn sw-btn--dark">Skontaktuj się</a>
        </div>
    </div>
</section>
