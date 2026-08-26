<?php
/** @var array $articles */
/** @var int $total */
/** @var int $page */
/** @var int $perPage */
/** @var array $categories */
/** @var string|null $activeCategory */
/** @var array $content */
use SecureWare\Core\Icons;
use SecureWare\Core\Lang;
use SecureWare\Core\Locale;
use SecureWare\Core\Str;

$totalPages = max(1, (int) ceil($total / $perPage));
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
    <div class="sw-wrap">
        <?php if ($categories): ?>
        <div class="sw-filters">
            <a href="<?= Locale::url('/blog') ?>" class="<?= !$activeCategory ? 'active' : '' ?>"><?= Lang::t('blog.all_categories') ?></a>
            <?php foreach ($categories as $c): ?>
                <a href="<?= Locale::url('/blog') ?>?kategoria=<?= urlencode($c['slug']) ?>" class="<?= $activeCategory === $c['slug'] ? 'active' : '' ?>"><?= htmlspecialchars($c['name'], ENT_QUOTES, 'UTF-8') ?></a>
            <?php endforeach; ?>
        </div>
        <?php endif; ?>

        <div class="sw-blog-grid reveal-stagger">
            <?php foreach ($articles as $i => $a): ?>
                <a class="sw-blog-card<?= ($i === 0 && $page === 1) ? ' sw-blog-card--featured' : '' ?>" href="<?= Locale::url('/blog/' . $a['slug']) ?>">
                    <div class="sw-blog-card__img<?= $a['featured_image_path'] ? '' : ' sw-blog-card__img--empty' ?>"><?php if ($a['featured_image_path']): ?><img src="<?= htmlspecialchars($a['featured_image_path'], ENT_QUOTES, 'UTF-8') ?>" alt=""><?php else: ?><span class="sw-blog-card__ph"><?= Icons::svg(Str::fallbackIcon($a['slug']), 34) ?></span><?php endif; ?></div>
                    <div class="sw-blog-card__body">
                        <span class="meta"><?= htmlspecialchars($a['category_name'] ?? 'Blog', ENT_QUOTES, 'UTF-8') ?></span>
                        <h3><?= htmlspecialchars($a['title'], ENT_QUOTES, 'UTF-8') ?></h3>
                        <p><?= htmlspecialchars(Str::excerpt($a['excerpt'] ?: $a['content'], 100), ENT_QUOTES, 'UTF-8') ?></p>
                    </div>
                </a>
            <?php endforeach; ?>
            <?php if (!$articles): ?><p><?= Lang::t('blog.no_posts') ?></p><?php endif; ?>
        </div>

        <?php if ($totalPages > 1): ?>
        <div class="sw-pagination">
            <?php for ($p = 1; $p <= $totalPages; $p++): ?>
                <a href="?page=<?= $p ?><?= $activeCategory ? '&kategoria=' . urlencode($activeCategory) : '' ?>" class="<?= $p === $page ? 'active' : '' ?>">
                    <?= $p ?>
                </a>
            <?php endfor; ?>
        </div>
        <?php endif; ?>
    </div>
</section>
