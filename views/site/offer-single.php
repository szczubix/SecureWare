<?php
/** @var array $service */
/** @var array $otherServices */
use SecureWare\Core\Icons;
use SecureWare\Core\Lang;
use SecureWare\Core\Locale;
use SecureWare\Models\Diagram;
?>
<section class="sw-prose-header">
    <div class="sw-wrap">
        <div class="meta"><a href="<?= Locale::url('/oferta') ?>"><?= Lang::t('offer.breadcrumb') ?></a> / <?= htmlspecialchars($service['name'], ENT_QUOTES, 'UTF-8') ?></div>
        <div style="display:flex;align-items:center;gap:16px;">
            <div class="sw-service-card__icon" style="margin:0;"><?= Icons::svg($service['icon'], 26) ?></div>
            <h1><?= htmlspecialchars($service['name'], ENT_QUOTES, 'UTF-8') ?></h1>
        </div>
    </div>
</section>

<div class="sw-service-layout">
    <article class="sw-prose reveal">
        <?= Diagram::embedInto($service['content']) ?>
    </article>

    <aside class="sw-service-sidebar reveal">
        <?php if (!empty($service['short_description'])): ?>
            <p><?= htmlspecialchars($service['short_description'], ENT_QUOTES, 'UTF-8') ?></p>
        <?php endif; ?>
        <a href="<?= Locale::url('/kontakt') ?>" class="sw-btn sw-btn--primary"><?= Lang::t('offer.book_consult') ?></a>
        <?php if (!empty($service['meta'])): ?>
            <h4><?= Lang::t('offer.details_heading') ?></h4>
            <div class="spec">
                <?php foreach ($service['meta'] as $key => $value): ?>
                    <div><strong><?= htmlspecialchars($key, ENT_QUOTES, 'UTF-8') ?></strong><span><?= htmlspecialchars($value, ENT_QUOTES, 'UTF-8') ?></span></div>
                <?php endforeach; ?>
            </div>
        <?php endif; ?>
    </aside>
</div>

<section class="sw-section--tight">
    <div class="sw-wrap">
        <div class="sw-cta reveal">
            <div>
                <h2><?= Lang::t('offer.interested_in', $service['name']) ?></h2>
                <p><?= Lang::t('offer.consult_cta_text') ?></p>
            </div>
            <a href="<?= Locale::url('/kontakt') ?>" class="sw-btn sw-btn--dark"><?= Lang::t('offer.contact_cta') ?></a>
        </div>
    </div>
</section>

<?php if ($otherServices): ?>
<section class="sw-related">
    <div class="sw-wrap">
        <h2 class="reveal" style="font-size:22px;margin-bottom:20px;"><?= Lang::t('offer.other_services') ?></h2>
        <div class="sw-services-grid reveal-stagger">
            <?php foreach (array_slice($otherServices, 0, 3) as $s): ?>
                <div class="sw-service-card">
                    <div class="sw-service-card__icon"><?= Icons::svg($s['icon'], 22) ?></div>
                    <h3><?= htmlspecialchars($s['name'], ENT_QUOTES, 'UTF-8') ?></h3>
                    <p><?= htmlspecialchars($s['short_description'], ENT_QUOTES, 'UTF-8') ?></p>
                    <a class="more" href="<?= Locale::url('/oferta/' . $s['slug']) ?>"><?= Lang::t('offer.read_more') ?> <?= Icons::svg('arrow-right', 14) ?></a>
                </div>
            <?php endforeach; ?>
        </div>
    </div>
</section>
<?php endif; ?>
