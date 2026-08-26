<?php
/** @var array $article */
/** @var array $related */
use SecureWare\Core\Icons;
use SecureWare\Core\Lang;
use SecureWare\Core\Locale;
use SecureWare\Core\Str;
use SecureWare\Models\Diagram;
?>
<section class="sw-prose-header">
    <div class="sw-wrap" style="max-width:760px;">
        <div class="meta">
            <a href="<?= Locale::url('/blog') ?>"><?= Lang::t('blog.breadcrumb') ?></a>
            <?php if ($article['category_name']): ?> / <?= htmlspecialchars($article['category_name'], ENT_QUOTES, 'UTF-8') ?><?php endif; ?>
            · <?= htmlspecialchars(date('d.m.Y', strtotime($article['published_at'])), ENT_QUOTES, 'UTF-8') ?>
            <?php if ($article['author_name']): ?> · <?= htmlspecialchars($article['author_name'], ENT_QUOTES, 'UTF-8') ?><?php endif; ?>
        </div>
        <h1><?= htmlspecialchars($article['title'], ENT_QUOTES, 'UTF-8') ?></h1>
    </div>
</section>

<?php if ($article['featured_image_path']): ?>
<div class="sw-wrap" style="max-width:900px;margin-top:30px;">
    <img src="<?= htmlspecialchars($article['featured_image_path'], ENT_QUOTES, 'UTF-8') ?>" alt="" style="border-radius:14px;width:100%;">
</div>
<?php endif; ?>

<article class="sw-prose">
    <?= Diagram::embedInto($article['content']) ?>

    <?php if (!empty($article['tags'])): ?>
        <div style="margin-top:30px;display:flex;gap:8px;flex-wrap:wrap;">
            <?php foreach ($article['tags'] as $t): ?>
                <a href="<?= Locale::url('/blog') ?>?tag=<?= urlencode($t['slug']) ?>" style="padding:5px 12px;border:1px solid var(--sw-border);border-radius:999px;font-size:12.5px;">#<?= htmlspecialchars($t['name'], ENT_QUOTES, 'UTF-8') ?></a>
            <?php endforeach; ?>
        </div>
    <?php endif; ?>
</article>

<?php if ($related): ?>
<section class="sw-related">
    <div class="sw-wrap">
        <h2 style="font-size:22px;margin-bottom:20px;"><?= Lang::t('blog.see_also') ?></h2>
        <div class="sw-blog-grid reveal-stagger">
            <?php foreach ($related as $a): ?>
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
