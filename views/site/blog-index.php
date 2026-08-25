<?php
/** @var array $articles */
/** @var int $total */
/** @var int $page */
/** @var int $perPage */
/** @var array $categories */
/** @var string|null $activeCategory */
use SecureWare\Core\Str;

$totalPages = max(1, (int) ceil($total / $perPage));
?>
<section class="sw-hero" style="padding:64px 0;">
    <div class="sw-wrap">
        <span class="sw-hero__eyebrow sw-anim-in sw-delay-1">Blog</span>
        <h1 class="sw-anim-in sw-delay-2" style="font-size:36px;">Backup, ransomware i <span>disaster recovery</span> po ludzku</h1>
        <p class="lead sw-anim-in sw-delay-3">Praktyczna wiedza o ochronie danych - bez marketingowego zargonu.</p>
    </div>
</section>

<section class="sw-section">
    <div class="sw-wrap">
        <?php if ($categories): ?>
        <div class="sw-filters">
            <a href="/blog" class="<?= !$activeCategory ? 'active' : '' ?>">Wszystkie</a>
            <?php foreach ($categories as $c): ?>
                <a href="/blog?kategoria=<?= urlencode($c['slug']) ?>" class="<?= $activeCategory === $c['slug'] ? 'active' : '' ?>"><?= htmlspecialchars($c['name'], ENT_QUOTES, 'UTF-8') ?></a>
            <?php endforeach; ?>
        </div>
        <?php endif; ?>

        <div class="sw-blog-grid reveal-stagger">
            <?php foreach ($articles as $a): ?>
                <a class="sw-blog-card" href="/blog/<?= htmlspecialchars($a['slug'], ENT_QUOTES, 'UTF-8') ?>">
                    <div class="sw-blog-card__img"><?php if ($a['featured_image_path']): ?><img src="<?= htmlspecialchars($a['featured_image_path'], ENT_QUOTES, 'UTF-8') ?>" alt=""><?php endif; ?></div>
                    <div class="sw-blog-card__body">
                        <span class="meta"><?= htmlspecialchars($a['category_name'] ?? 'Blog', ENT_QUOTES, 'UTF-8') ?></span>
                        <h3><?= htmlspecialchars($a['title'], ENT_QUOTES, 'UTF-8') ?></h3>
                        <p><?= htmlspecialchars(Str::excerpt($a['excerpt'] ?: $a['content'], 100), ENT_QUOTES, 'UTF-8') ?></p>
                    </div>
                </a>
            <?php endforeach; ?>
            <?php if (!$articles): ?><p>Brak wpisow w tej kategorii.</p><?php endif; ?>
        </div>

        <?php if ($totalPages > 1): ?>
        <div class="pagination" style="margin-top:36px;display:flex;gap:8px;">
            <?php for ($p = 1; $p <= $totalPages; $p++): ?>
                <a href="?page=<?= $p ?><?= $activeCategory ? '&kategoria=' . urlencode($activeCategory) : '' ?>"
                   style="padding:8px 14px;border:1px solid var(--sw-border);border-radius:8px;<?= $p === $page ? 'background:var(--sw-ink);color:#fff;' : '' ?>">
                    <?= $p ?>
                </a>
            <?php endfor; ?>
        </div>
        <?php endif; ?>
    </div>
</section>
