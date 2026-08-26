<?php
/** @var array $groups */
/** @var array $content */
use SecureWare\Core\Icons;
use SecureWare\Core\Lang;
use SecureWare\Core\Locale;

$hasAny = (bool) array_filter($groups);
$h = static fn ($v) => htmlspecialchars((string) $v, ENT_QUOTES, 'UTF-8');
?>
<section class="sw-hero" style="padding:64px 0;">
    <div class="sw-wrap">
        <span class="sw-hero__eyebrow sw-anim-in sw-delay-1"><?= $h($content['eyebrow']) ?></span>
        <h1 class="sw-anim-in sw-delay-2" style="font-size:36px;"><?= $h($content['heading_pre']) ?><span><?= $h($content['heading_highlight']) ?></span><?= $h($content['heading_post']) ?></h1>
        <p class="lead sw-anim-in sw-delay-3"><?= $h($content['lead']) ?></p>
        <div class="sw-highlights sw-anim-in sw-delay-4">
            <?php foreach ($content['highlights'] as $item): ?>
                <span><?= Icons::svg($item['icon'], 16) ?> <?= $h($item['text']) ?></span>
            <?php endforeach; ?>
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
                    <a class="more" href="<?= Locale::url('/oferta/' . $s['slug']) ?>"><?= Lang::t('offer.read_more') ?> <?= Icons::svg('arrow-right', 14) ?></a>
                </div>
            <?php endforeach; ?>
        </div>
    </div>
</section>
<?php endforeach; ?>

<?php if (!$hasAny): ?>
<section class="sw-section"><div class="sw-wrap"><p><?= $h($content['empty_text']) ?></p></div></section>
<?php endif; ?>

<section class="sw-section--tight">
    <div class="sw-wrap">
        <div class="sw-cta reveal">
            <div>
                <h2><?= $h($content['cta_heading']) ?></h2>
                <p><?= $h($content['cta_text']) ?></p>
            </div>
            <a href="<?= Locale::url('/kontakt') ?>" class="sw-btn sw-btn--dark"><?= $h($content['cta_button_label']) ?></a>
        </div>
    </div>
</section>
