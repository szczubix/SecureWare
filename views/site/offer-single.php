<?php
/** @var array $service */
/** @var array $otherServices */
use SecureWare\Core\Icons;
?>
<section class="sw-prose-header">
    <div class="sw-wrap">
        <div class="meta"><a href="/oferta">Oferta</a> / <?= htmlspecialchars($service['name'], ENT_QUOTES, 'UTF-8') ?></div>
        <div style="display:flex;align-items:center;gap:16px;">
            <div class="sw-service-card__icon" style="margin:0;"><?= Icons::svg($service['icon'], 26) ?></div>
            <h1><?= htmlspecialchars($service['name'], ENT_QUOTES, 'UTF-8') ?></h1>
        </div>
    </div>
</section>

<article class="sw-prose">
    <?= $service['content'] ?>

    <?php if (!empty($service['meta'])): ?>
        <h2>Szczegoly</h2>
        <ul>
            <?php foreach ($service['meta'] as $key => $value): ?>
                <li><strong><?= htmlspecialchars($key, ENT_QUOTES, 'UTF-8') ?>:</strong> <?= htmlspecialchars($value, ENT_QUOTES, 'UTF-8') ?></li>
            <?php endforeach; ?>
        </ul>
    <?php endif; ?>
</article>

<section class="sw-section--tight">
    <div class="sw-wrap">
        <div class="sw-cta reveal">
            <div>
                <h2>Zainteresowany uslugą <?= htmlspecialchars($service['name'], ENT_QUOTES, 'UTF-8') ?>?</h2>
                <p>Umow bezplatna konsultacje i dowiedz sie, jak wdrozyc to u siebie.</p>
            </div>
            <a href="/kontakt" class="sw-btn sw-btn--dark">Skontaktuj sie</a>
        </div>
    </div>
</section>

<?php if ($otherServices): ?>
<section class="sw-related">
    <div class="sw-wrap">
        <h2 class="reveal" style="font-size:22px;margin-bottom:20px;">Pozostale uslugi</h2>
        <div class="sw-services-grid reveal-stagger">
            <?php foreach (array_slice($otherServices, 0, 3) as $s): ?>
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
<?php endif; ?>
