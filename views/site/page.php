<?php
/** @var array $page */
use SecureWare\Core\Lang;
use SecureWare\Core\Locale;
use SecureWare\Core\Toc;
use SecureWare\Models\Diagram;

$wide = $page['template'] === 'full-width';
$toc = Toc::extract($page['content']);
$hasToc = count($toc['items']) >= 2;
$body = Diagram::embedInto($toc['html']);
?>
<section class="sw-prose-header">
    <div class="sw-wrap" style="max-width:760px;">
        <div class="meta"><a href="<?= Locale::url('/') ?>"><?= Lang::t('breadcrumb.home') ?></a> / <?= htmlspecialchars($page['title'], ENT_QUOTES, 'UTF-8') ?></div>
        <h1><?= htmlspecialchars($page['title'], ENT_QUOTES, 'UTF-8') ?></h1>
    </div>
</section>

<?php if ($hasToc): ?>
    <div class="sw-wrap sw-toc-layout">
        <nav class="sw-toc" aria-label="<?= Lang::t('breadcrumb.toc_aria') ?>">
            <span class="sw-toc__label"><?= Lang::t('breadcrumb.toc_label') ?></span>
            <?php foreach ($toc['items'] as $item): ?>
                <a href="#<?= $item['id'] ?>"><?= htmlspecialchars($item['text'], ENT_QUOTES, 'UTF-8') ?></a>
            <?php endforeach; ?>
        </nav>
        <article class="sw-prose sw-prose--in-toc" <?= $wide ? 'style="max-width:1000px;"' : '' ?>>
            <?= $body ?>
        </article>
    </div>
<?php else: ?>
    <article class="sw-prose" <?= $wide ? 'style="max-width:1000px;"' : '' ?>>
        <?= $body ?>
    </article>
<?php endif; ?>
