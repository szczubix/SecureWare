<?php
/** @var array $services */
/** @var array $latestArticles */
/** @var array $content */
use SecureWare\Core\Icons;
use SecureWare\Core\Lang;
use SecureWare\Core\Locale;
use SecureWare\Core\Str;

$teaser = array_slice($services, 0, 6);
$h = static fn ($v) => htmlspecialchars((string) $v, ENT_QUOTES, 'UTF-8');

$renderStat = static function (array $item) use ($h) {
    if ($item['count'] !== null && $item['count'] !== '') {
        echo '<strong data-count="' . (int) $item['count'] . '" data-suffix="' . $h($item['suffix']) . '">0' . $h($item['suffix']) . '</strong>';
    } else {
        echo '<strong>' . $h($item['value']) . '</strong>';
    }
    echo '<span>' . $h($item['label']) . '</span>';
};

$hero = $content['hero'];
$offer = $content['offer'];
$stats = $content['stats'];
$platform = $content['platform'];
$rule = $content['rule'];
$ransomware = $content['ransomware'];
$scenario = $content['scenario'];
$calcPromo = $content['calc_promo'];
$why = $content['why'];
$cases = $content['cases'];
$steps = $content['steps'];
$stack = $content['stack'];
$blog = $content['blog'];
$faq = $content['faq'];
$cta = $content['cta'];
?>
<section class="sw-hero">
    <div class="sw-wrap sw-hero__grid">
        <div>
            <span class="sw-hero__eyebrow sw-anim-in sw-delay-1"><?= $h($hero['eyebrow']) ?></span>
            <h1 class="sw-anim-in sw-delay-2"><?= $h($hero['headline_pre']) ?><span><?= $h($hero['headline_highlight']) ?></span><?= $h($hero['headline_post']) ?></h1>
            <p class="lead sw-anim-in sw-delay-3"><?= $h($hero['lead']) ?></p>
            <div class="sw-hero__actions sw-anim-in sw-delay-4">
                <a href="<?= $h(Locale::url($hero['cta_primary_url'])) ?>" class="sw-btn sw-btn--primary"><?= $h($hero['cta_primary_label']) ?></a>
                <a href="<?= $h(Locale::url($hero['cta_secondary_url'])) ?>" class="sw-btn sw-btn--ghost"><?= $h($hero['cta_secondary_label']) ?> <?= Icons::svg('arrow-right', 16) ?></a>
            </div>
            <div class="sw-hero__specs sw-anim-in sw-delay-5">
                <?php foreach ($hero['specs'] as $spec): ?>
                    <div><?php $renderStat($spec); ?></div>
                <?php endforeach; ?>
            </div>
        </div>
        <div class="sw-anim-in sw-delay-3">
            <div class="sw-diagram-card">
                <div class="sw-diagram-card__head">
                    <h3><?= $h($hero['diagram_title']) ?></h3>
                    <span class="sw-diagram-card__live"><?= $h($hero['diagram_badge']) ?></span>
                </div>
                <svg class="sw-diagram" viewBox="0 0 480 380" xmlns="http://www.w3.org/2000/svg">
                    <path class="flow" d="M240,72 L240,140"/>
                    <path class="flow" d="M240,196 C240,240 140,240 140,280"/>
                    <path class="flow" d="M240,196 C240,240 340,240 340,280"/>

                    <g class="node primary">
                        <rect x="160" y="16" width="160" height="56" rx="10"/>
                        <svg class="icon" x="176" y="30" width="22" height="22"><?= Icons::svg('server', 22) ?></svg>
                        <text x="210" y="40">Dane</text>
                        <text x="210" y="56" class="sub">produkcyjne</text>
                    </g>

                    <g class="node">
                        <rect x="160" y="140" width="160" height="56" rx="10"/>
                        <svg class="icon" x="176" y="154" width="22" height="22"><?= Icons::svg('layers', 22) ?></svg>
                        <text x="210" y="164">Kopia lokalna</text>
                        <text x="210" y="180" class="sub">inny nośnik</text>
                    </g>

                    <g class="node">
                        <rect x="60" y="280" width="160" height="70" rx="10"/>
                        <svg class="icon" x="76" y="296" width="20" height="20"><?= Icons::svg('cloud-upload', 20) ?></svg>
                        <text x="106" y="309">Kopia offsite</text>
                        <text x="106" y="325" class="sub">poza siedzibą</text>
                        <g class="verified" transform="translate(206,282)">
                            <circle r="10"/>
                            <svg x="-6" y="-6" width="12" height="12"><?= Icons::svg('check', 12) ?></svg>
                        </g>
                    </g>

                    <g class="node">
                        <rect x="260" y="280" width="160" height="70" rx="10"/>
                        <svg class="icon" x="276" y="296" width="20" height="20"><?= Icons::svg('lock', 20) ?></svg>
                        <text x="306" y="309">Immutable</text>
                        <text x="306" y="325" class="sub">offline / niezmienna</text>
                        <g class="verified" transform="translate(406,282)">
                            <circle r="10"/>
                            <svg x="-6" y="-6" width="12" height="12"><?= Icons::svg('check', 12) ?></svg>
                        </g>
                    </g>
                </svg>
                <div class="sw-diagram-card__foot"><?= $h($hero['diagram_foot']) ?></div>
            </div>
        </div>
    </div>
</section>

<div class="sw-ticker" aria-hidden="true">
    <div class="sw-ticker__track">
        <?php foreach (array_merge($services, $services) as $s): ?>
            <span><?= htmlspecialchars($s['name'], ENT_QUOTES, 'UTF-8') ?></span>
        <?php endforeach; ?>
    </div>
</div>

<section class="sw-stack">
    <div class="sw-wrap">
        <p class="sw-stack__label reveal"><?= $h($stack['eyebrow']) ?></p>
        <div class="sw-stack__row reveal-stagger">
            <?php foreach (array_filter(array_map('trim', explode("\n", $stack['items']))) as $item): ?>
                <span class="sw-stack__item"><?= htmlspecialchars($item, ENT_QUOTES, 'UTF-8') ?></span>
            <?php endforeach; ?>
        </div>
    </div>
</section>

<section class="sw-section">
    <div class="sw-wrap">
        <div class="sw-section-head reveal">
            <h5><?= $h($offer['eyebrow']) ?></h5>
            <h2><?= $h($offer['heading']) ?></h2>
            <p><?= $h($offer['intro']) ?></p>
        </div>
        <div class="sw-services-grid reveal-stagger">
            <?php foreach ($teaser as $s): ?>
                <div class="sw-service-card">
                    <div class="sw-service-card__icon"><?= Icons::svg($s['icon'], 22) ?></div>
                    <h3><?= htmlspecialchars($s['name'], ENT_QUOTES, 'UTF-8') ?></h3>
                    <p><?= htmlspecialchars($s['short_description'], ENT_QUOTES, 'UTF-8') ?></p>
                    <a class="more" href="<?= Locale::url('/oferta/' . $s['slug']) ?>"><?= Lang::t('offer.read_more') ?> <?= Icons::svg('arrow-right', 14) ?></a>
                </div>
            <?php endforeach; ?>
        </div>
        <div class="reveal" style="text-align:center;margin-top:36px;">
            <a href="<?= Locale::url('/oferta') ?>" class="sw-btn sw-btn--dark"><?= $h($offer['cta_label']) ?></a>
        </div>
    </div>
</section>

<section class="sw-section sw-section--tight">
    <div class="sw-wrap">
        <div class="sw-stats-band reveal">
            <div class="sw-stats reveal-stagger reveal-stagger--pop">
                <?php foreach ($stats['items'] as $stat): ?>
                    <div><?php $renderStat($stat); ?></div>
                <?php endforeach; ?>
            </div>
        </div>
    </div>
</section>

<section class="sw-section">
    <div class="sw-wrap">
        <div class="sw-section-head reveal">
            <h5><?= $h($platform['eyebrow']) ?></h5>
            <h2><?= $h($platform['heading']) ?></h2>
            <p><?= $h($platform['intro']) ?></p>
        </div>
        <div class="sw-platform reveal">
            <div class="sw-platform__tabs" role="tablist">
                <?php foreach ($platform['tabs'] as $i => $tab): $key = ['backup', 'dr', 'monitoring'][$i] ?? 'tab' . $i; ?>
                    <button type="button" class="sw-platform__tab<?= $i === 0 ? ' is-active' : '' ?>" data-tab="<?= $key ?>" role="tab" aria-selected="<?= $i === 0 ? 'true' : 'false' ?>">
                        <span class="icon"><?= Icons::svg($tab['icon'], 20) ?></span>
                        <span><strong><?= $h($tab['title']) ?></strong><small><?= $h($tab['subtitle']) ?></small></span>
                    </button>
                <?php endforeach; ?>
            </div>
            <div class="sw-platform__panels">
                <?php foreach ($platform['tabs'] as $i => $tab): $key = ['backup', 'dr', 'monitoring'][$i] ?? 'tab' . $i; ?>
                    <div class="sw-platform__panel<?= $i === 0 ? ' is-active' : '' ?>" data-panel="<?= $key ?>">
                        <h3><?= $h($tab['panel_title']) ?></h3>
                        <p><?= $h($tab['panel_text']) ?></p>
                        <ul>
                            <?php foreach (preg_split('/\r?\n/', trim((string) $tab['bullets'])) as $bullet): if (trim($bullet) === '') continue; ?>
                                <li><?= Icons::svg('check', 14) ?> <?= $h($bullet) ?></li>
                            <?php endforeach; ?>
                        </ul>
                    </div>
                <?php endforeach; ?>
            </div>
        </div>
    </div>
</section>

<section class="sw-section">
    <div class="sw-wrap">
        <div class="sw-section-head reveal">
            <h5><?= $h($rule['eyebrow']) ?></h5>
            <h2><?= $h($rule['heading']) ?></h2>
            <p><?= $h($rule['intro']) ?></p>
        </div>
        <div class="sw-rule reveal">
            <svg class="sw-rule__line" viewBox="0 0 1000 24" preserveAspectRatio="none" aria-hidden="true">
                <path class="base" d="M0,12 H1000"/>
                <path class="flow" d="M0,12 H1000"/>
            </svg>
            <span class="sw-rule__packet" aria-hidden="true"></span>
            <div class="sw-rule__row reveal-stagger">
                <?php foreach ($rule['items'] as $item): ?>
                    <div class="sw-rule__item">
                        <button type="button" class="sw-rule__node" aria-expanded="false">
                            <span class="icon-badge"><?= Icons::svg($item['icon'], 18) ?></span>
                            <span class="num"><?= $h($item['num']) ?></span>
                            <span class="label"><?= $h($item['label']) ?></span>
                            <?= Icons::svg('chevron-down', 14) ?>
                        </button>
                        <div class="sw-rule__panel">
                            <p><?= $h($item['text']) ?></p>
                        </div>
                    </div>
                <?php endforeach; ?>
            </div>
        </div>
    </div>
</section>

<section class="sw-section sw-section--tight">
    <div class="sw-wrap">
        <div class="sw-section-head reveal">
            <h5><?= $h($ransomware['eyebrow']) ?></h5>
            <h2><?= $h($ransomware['heading']) ?></h2>
            <p><?= $h($ransomware['intro']) ?></p>
        </div>
        <div class="sw-ransomware reveal">
            <div class="sw-ransomware__track">
                <div class="sw-ransomware__node" data-node="1">
                    <span class="icon-badge"><?= Icons::svg('server', 18) ?></span>
                    <span class="label">Dane produkcyjne</span>
                    <span class="sw-ransomware__mark">✕</span>
                </div>
                <div class="sw-ransomware__node" data-node="2">
                    <span class="icon-badge"><?= Icons::svg('layers', 18) ?></span>
                    <span class="label">Kopia lokalna</span>
                    <span class="sw-ransomware__mark">✕</span>
                </div>
                <div class="sw-ransomware__node sw-ransomware__node--safe" data-node="3">
                    <span class="icon-badge"><?= Icons::svg('lock', 18) ?></span>
                    <span class="label">Kopia immutable</span>
                    <span class="sw-ransomware__shield"><?= Icons::svg('shield-check', 13) ?> <?= $h($ransomware['protected_label']) ?></span>
                </div>
                <div class="sw-ransomware__actor" aria-hidden="true"><?= Icons::svg('bug', 20) ?></div>
            </div>
        </div>
    </div>
</section>

<section class="sw-section">
    <div class="sw-wrap">
        <div class="sw-section-head reveal">
            <h5><?= $h($scenario['eyebrow']) ?></h5>
            <h2><?= $h($scenario['heading']) ?></h2>
            <p><?= $h($scenario['intro']) ?></p>
        </div>
        <div class="sw-scenario">
            <div class="sw-scenario__panel sw-scenario__panel--threat reveal">
                <div class="sw-scenario__avatars">
                    <span class="sw-scenario__avatar sw-scenario__avatar--attacker"><?= Icons::svg('bug', 16) ?></span>
                    <span class="sw-scenario__avatar sw-scenario__avatar--ceo"><?= Icons::svg('user', 16) ?></span>
                </div>
                <span class="sw-scenario__badge"><?= Icons::svg('lock', 13) ?> <?= $h($scenario['threat_badge']) ?></span>
                <div class="sw-scenario__bubble reveal-stagger">
                    <?php foreach (preg_split('/\r?\n/', trim((string) $scenario['threat_lines'])) as $line): if (trim($line) === '') continue; ?>
                        <p class="sw-scenario__line"><?= $h($line) ?></p>
                    <?php endforeach; ?>
                    <p class="sw-scenario__amount"><strong data-count="<?= (int) $scenario['threat_amount'] ?>" data-suffix="<?= $h($scenario['threat_suffix']) ?>">0<?= $h($scenario['threat_suffix']) ?></strong></p>
                    <p class="sw-scenario__deadline"><?= Icons::svg('activity', 13) ?> <?= $h($scenario['threat_deadline']) ?></p>
                </div>
            </div>
            <div class="sw-scenario__vs">VS</div>
            <div class="sw-scenario__panel sw-scenario__panel--safe reveal">
                <div class="sw-scenario__avatars">
                    <span class="sw-scenario__avatar sw-scenario__avatar--admin"><?= Icons::svg('user', 16) ?></span>
                </div>
                <span class="sw-scenario__badge sw-scenario__badge--safe"><?= Icons::svg('shield-check', 13) ?> <?= $h($scenario['safe_badge']) ?></span>
                <div class="sw-scenario__bubble sw-scenario__bubble--safe reveal-stagger">
                    <p class="sw-scenario__line"><?= $h($scenario['safe_intro']) ?></p>
                    <ul class="sw-scenario__checklist">
                        <?php foreach (preg_split('/\r?\n/', trim((string) $scenario['safe_checklist'])) as $item): if (trim($item) === '') continue; ?>
                            <li><?= Icons::svg('check', 13) ?> <?= $h($item) ?></li>
                        <?php endforeach; ?>
                    </ul>
                    <p class="sw-scenario__result"><?= Icons::svg('shield-check', 13) ?> <?= $h($scenario['safe_result']) ?></p>
                </div>
            </div>
        </div>
    </div>
</section>

<section class="sw-section sw-section--tight">
    <div class="sw-wrap">
        <div class="sw-calc-promo reveal">
            <div>
                <span class="sw-calc-promo__eyebrow"><?= $h($calcPromo['eyebrow']) ?></span>
                <h2><?= $h($calcPromo['heading']) ?></h2>
                <p><?= $h($calcPromo['text']) ?></p>
            </div>
            <a href="<?= Locale::url('/kalkulator-kosztu-przestoju') ?>" class="sw-btn sw-btn--primary"><?= $h($calcPromo['button_label']) ?> <?= Icons::svg('arrow-right', 14) ?></a>
        </div>
    </div>
</section>

<section class="sw-section sw-section--muted">
    <div class="sw-wrap sw-why">
        <div class="sw-why__intro reveal">
            <h5><?= $h($why['eyebrow']) ?></h5>
            <h2><?= $h($why['heading']) ?></h2>
            <p><?= $h($why['intro']) ?></p>
            <a href="<?= Locale::url('/kontakt') ?>" class="sw-why__link"><?= $h($why['link_label']) ?> <?= Icons::svg('arrow-right', 14) ?></a>
        </div>
        <div class="sw-why__list reveal-stagger">
            <?php foreach ($why['items'] as $i => $item): ?>
                <div class="sw-why__item">
                    <span class="num"><?= str_pad((string) ($i + 1), 2, '0', STR_PAD_LEFT) ?></span>
                    <div>
                        <h4><?= $h($item['title']) ?></h4>
                        <p><?= $h($item['text']) ?></p>
                    </div>
                </div>
            <?php endforeach; ?>
        </div>
    </div>
</section>

<section class="sw-section">
    <div class="sw-wrap">
        <div class="sw-section-head reveal">
            <h5><?= $h($cases['eyebrow']) ?></h5>
            <h2><?= $h($cases['heading']) ?></h2>
            <p><?= $h($cases['intro']) ?></p>
        </div>
        <div class="sw-cases reveal-stagger">
            <?php foreach ($cases['items'] as $case): ?>
                <div class="sw-case">
                    <div class="sw-case__head">
                        <span class="sw-case__icon"><?= Icons::svg($case['icon'], 20) ?></span>
                        <span class="sw-case__industry"><?= $h($case['industry']) ?></span>
                    </div>
                    <h3><?= $h($case['title']) ?></h3>
                    <p><?= $h($case['situation']) ?></p>
                    <div class="sw-case__metrics">
                        <div><strong><?= $h($case['metric1_value']) ?></strong><span><?= $h($case['metric1_label']) ?></span></div>
                        <div><strong><?= $h($case['metric2_value']) ?></strong><span><?= $h($case['metric2_label']) ?></span></div>
                        <div><strong><?= $h($case['metric3_value']) ?></strong><span><?= $h($case['metric3_label']) ?></span></div>
                    </div>
                </div>
            <?php endforeach; ?>
        </div>
    </div>
</section>

<section class="sw-section">
    <div class="sw-wrap">
        <div class="sw-section-head reveal">
            <h5><?= $h($steps['eyebrow']) ?></h5>
            <h2><?= $h($steps['heading']) ?></h2>
            <p><?= $h($steps['intro']) ?></p>
        </div>
        <div class="sw-steps reveal-stagger">
            <?php foreach ($steps['items'] as $i => $item): ?>
                <div class="sw-step">
                    <span class="sw-step__num"><?= $i + 1 ?></span>
                    <h4><?= $h($item['title']) ?></h4>
                    <p><?= $h($item['text']) ?></p>
                </div>
            <?php endforeach; ?>
        </div>
    </div>
</section>

<?php if ($latestArticles): ?>
<section class="sw-section">
    <div class="sw-wrap">
        <div class="sw-section-head reveal">
            <h5><?= $h($blog['eyebrow']) ?></h5>
            <h2><?= $h($blog['heading']) ?></h2>
        </div>
        <div class="sw-blog-grid reveal-stagger">
            <?php foreach ($latestArticles as $a): ?>
                <a class="sw-blog-card" href="<?= Locale::url('/blog/' . $a['slug']) ?>">
                    <div class="sw-blog-card__img<?= $a['featured_image_path'] ? '' : ' sw-blog-card__img--empty' ?>"><?php if ($a['featured_image_path']): ?><img src="<?= htmlspecialchars($a['featured_image_path'], ENT_QUOTES, 'UTF-8') ?>" alt=""><?php else: ?><span class="sw-blog-card__ph"><?= Icons::svg(Str::fallbackIcon($a['slug']), 34) ?></span><?php endif; ?></div>
                    <div class="sw-blog-card__body">
                        <span class="meta"><?= htmlspecialchars($a['category_name'] ?? 'Blog', ENT_QUOTES, 'UTF-8') ?></span>
                        <h3><?= htmlspecialchars($a['title'], ENT_QUOTES, 'UTF-8') ?></h3>
                        <p><?= htmlspecialchars(Str::excerpt($a['excerpt'] ?: $a['content'], 100), ENT_QUOTES, 'UTF-8') ?></p>
                    </div>
                </a>
            <?php endforeach; ?>
        </div>
    </div>
</section>
<?php endif; ?>

<section class="sw-section sw-section--muted">
    <div class="sw-wrap">
        <div class="sw-section-head reveal">
            <h5><?= $h($faq['eyebrow']) ?></h5>
            <h2><?= $h($faq['heading']) ?></h2>
        </div>
        <div class="sw-faq reveal">
            <?php foreach ($faq['items'] as $i => $item): ?>
                <details<?= $i === 0 ? ' open' : '' ?>>
                    <summary><?= $h($item['question']) ?></summary>
                    <p><?= $h($item['answer']) ?></p>
                </details>
            <?php endforeach; ?>
        </div>
    </div>
</section>

<section class="sw-section--tight">
    <div class="sw-wrap">
        <div class="sw-cta reveal">
            <div>
                <h2><?= $h($cta['heading']) ?></h2>
                <p><?= $h($cta['text']) ?></p>
            </div>
            <a href="<?= $h(Locale::url($cta['button_url'])) ?>" class="sw-btn sw-btn--dark"><?= $h($cta['button_label']) ?></a>
        </div>
    </div>
</section>
