<?php
/** @var array $groups */
use SecureWare\Core\Icons;

$hasAny = (bool) array_filter($groups);
?>
<section class="sw-hero" style="padding:64px 0;">
    <div class="sw-wrap">
        <span class="sw-hero__eyebrow sw-anim-in sw-delay-1">Oferta</span>
        <h1 class="sw-anim-in sw-delay-2" style="font-size:36px;">Pelen zakres ochrony <span>danych</span> dla firm</h1>
        <p class="lead sw-anim-in sw-delay-3">13 uslug pokrywajacych caly cykl zycia backupu — od wdrozenia, przez codzienne zarzadzanie, po disaster recovery i testy odtwarzania.</p>
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
                    <a class="more" href="/oferta/<?= htmlspecialchars($s['slug'], ENT_QUOTES, 'UTF-8') ?>">Dowiedz sie wiecej <?= Icons::svg('arrow-right', 14) ?></a>
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
                <h2>Nie wiesz, ktora usluga jest dla Ciebie?</h2>
                <p>Porozmawiajmy — dobierzemy rozwiazanie do skali i budzetu Twojej firmy.</p>
            </div>
            <a href="/kontakt" class="sw-btn sw-btn--dark">Skontaktuj sie</a>
        </div>
    </div>
</section>
