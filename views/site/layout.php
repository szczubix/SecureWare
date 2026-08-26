<?php
/** @var string $content */
/** @var string|null $metaTitle */
/** @var string|null $metaDescription */
use SecureWare\Core\Config;
use SecureWare\Core\Icons;
use SecureWare\Models\Media;
use SecureWare\Models\Service;
use SecureWare\Models\Setting;

$settings     = Setting::all();
$navServices  = Service::published();
$siteName   = $settings['site_name'] ?? 'SecureWare';
$tagline    = $settings['site_tagline'] ?? '';
$navMenu    = json_decode($settings['nav_menu'] ?? '[]', true) ?: [];
$logoId     = $settings['logo_media_id'] ?? '';
$logoPath   = $logoId ? (Media::find((int) $logoId)['path'] ?? null) : null;
$faviconId  = $settings['favicon_media_id'] ?? '';
$faviconPath = $faviconId ? (Media::find((int) $faviconId)['path'] ?? null) : null;

$pageTitle = $metaTitle ?? $siteName;
$pageDesc  = $metaDescription ?? $tagline;
$gaId      = $settings['ga_measurement_id'] ?? '';
$cookieYes = $settings['cookieyes_script'] ?? '';
?><!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title><?= htmlspecialchars($pageTitle, ENT_QUOTES, 'UTF-8') ?></title>
<meta name="description" content="<?= htmlspecialchars($pageDesc, ENT_QUOTES, 'UTF-8') ?>">
<meta property="og:title" content="<?= htmlspecialchars($pageTitle, ENT_QUOTES, 'UTF-8') ?>">
<meta property="og:description" content="<?= htmlspecialchars($pageDesc, ENT_QUOTES, 'UTF-8') ?>">
<meta property="og:type" content="website">
<?php if ($faviconPath): ?>
<link rel="icon" href="<?= htmlspecialchars($faviconPath, ENT_QUOTES, 'UTF-8') ?>">
<?php else: ?>
<link rel="icon" href="/assets/img/favicon.svg" type="image/svg+xml">
<?php endif; ?>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:ital,wght@0,400;0,500;0,600;0,700;1,600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/css/site.css?v=<?= @filemtime(ROOT_PATH . '/assets/css/site.css') ?: '1' ?>">
<style>:root{--sw-primary:<?= htmlspecialchars($settings['color_primary'] ?? '#0b5fff', ENT_QUOTES, 'UTF-8') ?>;--sw-dark:<?= htmlspecialchars($settings['color_dark'] ?? '#0a0f1e', ENT_QUOTES, 'UTF-8') ?>;}</style>
<?php if ($cookieYes): ?>
<?= $cookieYes ?>
<?php endif; ?>
<?php if ($gaId): ?>
<script async src="https://www.googletagmanager.com/gtag/js?id=<?= urlencode($gaId) ?>"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', '<?= htmlspecialchars($gaId, ENT_QUOTES, 'UTF-8') ?>');
</script>
<?php endif; ?>
</head>
<body>
<header class="sw-header">
    <div class="sw-wrap sw-header__inner">
        <a href="/" class="sw-logo">
            <?php if ($logoPath): ?>
                <img src="<?= htmlspecialchars($logoPath, ENT_QUOTES, 'UTF-8') ?>" alt="<?= htmlspecialchars($siteName, ENT_QUOTES, 'UTF-8') ?>">
            <?php else: ?>
                <?= Icons::svg('shield-check', 26) ?> <span><?= htmlspecialchars($siteName, ENT_QUOTES, 'UTF-8') ?></span>
            <?php endif; ?>
        </a>
        <nav class="sw-nav" id="sw-nav">
            <?php foreach ($navMenu as $item): ?>
                <?php if ($item['url'] === '/oferta' && $navServices): ?>
                    <div class="sw-nav__item">
                        <a href="/oferta"><?= htmlspecialchars($item['label'], ENT_QUOTES, 'UTF-8') ?> <?= Icons::svg('chevron-down', 14) ?></a>
                        <div class="sw-mega">
                            <div class="sw-mega__grid">
                                <?php foreach ($navServices as $s): ?>
                                    <a class="sw-mega__item" href="/oferta/<?= htmlspecialchars($s['slug'], ENT_QUOTES, 'UTF-8') ?>">
                                        <span class="icon"><?= Icons::svg($s['icon'], 16) ?></span>
                                        <span><?= htmlspecialchars($s['name'], ENT_QUOTES, 'UTF-8') ?></span>
                                    </a>
                                <?php endforeach; ?>
                            </div>
                            <a class="sw-mega__all" href="/oferta">Zobacz pełną ofertę <?= Icons::svg('arrow-right', 14) ?></a>
                        </div>
                    </div>
                <?php else: ?>
                    <a href="<?= htmlspecialchars($item['url'], ENT_QUOTES, 'UTF-8') ?>"><?= htmlspecialchars($item['label'], ENT_QUOTES, 'UTF-8') ?></a>
                <?php endif; ?>
            <?php endforeach; ?>
        </nav>
        <div class="sw-header__actions">
            <a href="/kontakt" class="sw-btn sw-btn--primary">Umów rozmowę</a>
            <button class="sw-nav-toggle" id="sw-nav-toggle" aria-label="Menu"><?= Icons::svg('menu', 22) ?></button>
        </div>
    </div>
</header>

<main><?= $content ?></main>

<footer class="sw-footer">
    <div class="sw-wrap sw-footer__grid">
        <div>
            <div class="sw-logo sw-logo--footer"><?= Icons::svg('shield-check', 22) ?> <span><?= htmlspecialchars($siteName, ENT_QUOTES, 'UTF-8') ?></span></div>
            <p><?= htmlspecialchars($tagline, ENT_QUOTES, 'UTF-8') ?></p>
            <div class="sw-social">
                <?php if (!empty($settings['social_linkedin'])): ?><a href="<?= htmlspecialchars($settings['social_linkedin'], ENT_QUOTES, 'UTF-8') ?>" aria-label="LinkedIn"><?= Icons::svg('linkedin', 18) ?></a><?php endif; ?>
                <?php if (!empty($settings['social_twitter'])): ?><a href="<?= htmlspecialchars($settings['social_twitter'], ENT_QUOTES, 'UTF-8') ?>" aria-label="X / Twitter"><?= Icons::svg('twitter', 18) ?></a><?php endif; ?>
            </div>
        </div>
        <div>
            <h4>Nawigacja</h4>
            <?php foreach ($navMenu as $item): ?>
                <a href="<?= htmlspecialchars($item['url'], ENT_QUOTES, 'UTF-8') ?>"><?= htmlspecialchars($item['label'], ENT_QUOTES, 'UTF-8') ?></a>
            <?php endforeach; ?>
        </div>
        <div>
            <h4>Prawne</h4>
            <a href="/polityka-prywatnosci">Polityka prywatności</a>
            <a href="/regulamin">Regulamin</a>
        </div>
        <div>
            <h4>Kontakt</h4>
            <?php if (!empty($settings['contact_email'])): ?><a href="mailto:<?= htmlspecialchars($settings['contact_email'], ENT_QUOTES, 'UTF-8') ?>"><?= htmlspecialchars($settings['contact_email'], ENT_QUOTES, 'UTF-8') ?></a><?php endif; ?>
            <?php if (!empty($settings['contact_phone'])): ?><a href="tel:<?= htmlspecialchars(preg_replace('/\s+/', '', $settings['contact_phone']), ENT_QUOTES, 'UTF-8') ?>"><?= htmlspecialchars($settings['contact_phone'], ENT_QUOTES, 'UTF-8') ?></a><?php endif; ?>
            <?php if (!empty($settings['contact_address'])): ?><span><?= htmlspecialchars($settings['contact_address'], ENT_QUOTES, 'UTF-8') ?></span><?php endif; ?>
        </div>
    </div>
    <div class="sw-wrap sw-footer__bottom">
        <?= htmlspecialchars($settings['footer_text'] ?? '', ENT_QUOTES, 'UTF-8') ?>
    </div>
</footer>

<script>
document.getElementById('sw-nav-toggle').addEventListener('click', function () {
    document.getElementById('sw-nav').classList.toggle('is-open');
});
</script>
<script src="/assets/js/animations.js?v=<?= @filemtime(ROOT_PATH . '/assets/js/animations.js') ?: '1' ?>"></script>
</body>
</html>
