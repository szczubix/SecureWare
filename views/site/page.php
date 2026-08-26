<?php
/** @var array $page */
use SecureWare\Models\Diagram;
$wide = $page['template'] === 'full-width';
?>
<section class="sw-prose-header">
    <div class="sw-wrap" style="max-width:760px;">
        <h1><?= htmlspecialchars($page['title'], ENT_QUOTES, 'UTF-8') ?></h1>
    </div>
</section>

<article class="sw-prose" <?= $wide ? 'style="max-width:1000px;"' : '' ?>>
    <?= Diagram::embedInto($page['content']) ?>
</article>
