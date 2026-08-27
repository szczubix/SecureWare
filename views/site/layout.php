<?php
/** @var string $content */
/** @var string|null $metaTitle */
/** @var string|null $metaDescription */
/** @var string|null $ogImage */
use SecureWare\Core\Config;
use SecureWare\Core\Icons;
use SecureWare\Core\Lang;
use SecureWare\Core\Locale;
use SecureWare\Models\Media;
use SecureWare\Models\Service;
use SecureWare\Models\Setting;

$ogImage = $ogImage ?? null;

$settings     = Setting::all();
$navServices  = Service::published(Locale::current());
$siteName   = $settings['site_name'] ?? 'SecureWare';
$tagline    = Locale::isDefault() ? ($settings['site_tagline'] ?? '') : ($settings['site_tagline_en'] ?? $settings['site_tagline'] ?? '');

// Fallback tlumaczenie etykiet menu, gdy administrator nie skonfigurowal
// jeszcze osobnego menu EN (nav_menu_en) - tlumaczy znane adresy, resztę
// zostawia w oryginalnym jezyku zamiast pokazac puste menu.
$navLabelFallback = [
    '/oferta' => 'Offer', '/blog' => 'Resources', '/o-nas' => 'About us', '/kontakt' => 'Contact',
    '/polityka-prywatnosci' => 'Privacy policy', '/regulamin' => 'Terms of service',
    '/bezpieczenstwo' => 'Security',
];
$navMenu = json_decode($settings['nav_menu'] ?? '[]', true) ?: [];
if (!Locale::isDefault()) {
    $navMenuEn = json_decode($settings['nav_menu_en'] ?? '[]', true) ?: [];
    $navMenu = $navMenuEn ?: array_map(
        static fn (array $item) => ['label' => $navLabelFallback[$item['url']] ?? $item['label'], 'url' => $item['url']],
        $navMenu
    );
}
$logoId     = $settings['logo_media_id'] ?? '';
$logoMedia  = $logoId ? Media::find((int) $logoId) : null;
$logoPath   = $logoMedia['path'] ?? null;
// og:image/twitter:image must be a raster image - most crawlers (LinkedIn,
// Facebook) don't render SVG, so an SVG logo isn't usable as a fallback here.
$logoRasterPath = ($logoMedia && $logoMedia['mime'] !== 'image/svg+xml') ? $logoPath : null;
$faviconId  = $settings['favicon_media_id'] ?? '';
$faviconPath = $faviconId ? (Media::find((int) $faviconId)['path'] ?? null) : null;

$pageTitle = $metaTitle ?? $siteName;
$pageDesc  = $metaDescription ?? $tagline;
$gaId      = $settings['ga_measurement_id'] ?? '';
$cookieYes = $settings['cookieyes_script'] ?? '';

$baseUrl     = rtrim((string) (Config::get('app')['url'] ?? 'http://localhost'), '/');
$currentPath = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH) ?: '/';
$canonicalUrl = $baseUrl . $currentPath;

// Sciezka bez prefiksu jezyka (do budowania alternate/hreflang i przelacznika PL/EN).
$unprefixedPath = ($currentPath === '/en' || str_starts_with($currentPath, '/en/'))
    ? ('/' . ltrim(substr($currentPath, 3), '/'))
    : $currentPath;
$ogImageUrl  = $ogImage ?? $logoRasterPath;
if ($ogImageUrl && !preg_match('#^https?://#', $ogImageUrl)) {
    $ogImageUrl = $baseUrl . $ogImageUrl;
}
?><!DOCTYPE html>
<html lang="<?= Locale::current() ?>">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title><?= htmlspecialchars($pageTitle, ENT_QUOTES, 'UTF-8') ?></title>
<meta name="description" content="<?= htmlspecialchars($pageDesc, ENT_QUOTES, 'UTF-8') ?>">
<link rel="canonical" href="<?= htmlspecialchars($canonicalUrl, ENT_QUOTES, 'UTF-8') ?>">
<link rel="alternate" hreflang="pl" href="<?= htmlspecialchars($baseUrl . $unprefixedPath, ENT_QUOTES, 'UTF-8') ?>">
<link rel="alternate" hreflang="en" href="<?= htmlspecialchars($baseUrl . Locale::urlIn('en', $unprefixedPath), ENT_QUOTES, 'UTF-8') ?>">
<link rel="alternate" hreflang="x-default" href="<?= htmlspecialchars($baseUrl . $unprefixedPath, ENT_QUOTES, 'UTF-8') ?>">
<meta property="og:title" content="<?= htmlspecialchars($pageTitle, ENT_QUOTES, 'UTF-8') ?>">
<meta property="og:description" content="<?= htmlspecialchars($pageDesc, ENT_QUOTES, 'UTF-8') ?>">
<meta property="og:type" content="<?= $ogImage ? 'article' : 'website' ?>">
<meta property="og:url" content="<?= htmlspecialchars($canonicalUrl, ENT_QUOTES, 'UTF-8') ?>">
<?php if ($ogImageUrl): ?><meta property="og:image" content="<?= htmlspecialchars($ogImageUrl, ENT_QUOTES, 'UTF-8') ?>"><?php endif; ?>
<meta property="og:site_name" content="<?= htmlspecialchars($siteName, ENT_QUOTES, 'UTF-8') ?>">
<meta name="twitter:card" content="<?= $ogImageUrl ? 'summary_large_image' : 'summary' ?>">
<meta name="twitter:title" content="<?= htmlspecialchars($pageTitle, ENT_QUOTES, 'UTF-8') ?>">
<meta name="twitter:description" content="<?= htmlspecialchars($pageDesc, ENT_QUOTES, 'UTF-8') ?>">
<?php if ($ogImageUrl): ?><meta name="twitter:image" content="<?= htmlspecialchars($ogImageUrl, ENT_QUOTES, 'UTF-8') ?>"><?php endif; ?>
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
        <a href="<?= Locale::url('/') ?>" class="sw-logo">
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
                        <a href="<?= Locale::url('/oferta') ?>"><?= htmlspecialchars($item['label'], ENT_QUOTES, 'UTF-8') ?> <?= Icons::svg('chevron-down', 14) ?></a>
                        <div class="sw-mega">
                            <div class="sw-mega__grid">
                                <?php foreach ($navServices as $s): ?>
                                    <a class="sw-mega__item" href="<?= Locale::url('/oferta/' . $s['slug']) ?>">
                                        <span class="icon"><?= Icons::svg($s['icon'], 16) ?></span>
                                        <span><?= htmlspecialchars($s['name'], ENT_QUOTES, 'UTF-8') ?></span>
                                    </a>
                                <?php endforeach; ?>
                            </div>
                            <a class="sw-mega__all" href="<?= Locale::url('/oferta') ?>"><?= Lang::t('nav.see_full_offer') ?> <?= Icons::svg('arrow-right', 14) ?></a>
                        </div>
                    </div>
                <?php elseif ($item['url'] === '/blog'): ?>
                    <div class="sw-nav__item">
                        <a href="<?= Locale::url('/blog') ?>"><?= htmlspecialchars($item['label'], ENT_QUOTES, 'UTF-8') ?> <?= Icons::svg('chevron-down', 14) ?></a>
                        <div class="sw-mega sw-mega--simple">
                            <a class="sw-mega__item" href="<?= Locale::url('/blog') ?>">
                                <span class="icon"><?= Icons::svg('file-check', 16) ?></span>
                                <span><?= Lang::t('nav.resources_blog') ?></span>
                            </a>
                            <a class="sw-mega__item" href="<?= Locale::url('/kalkulator-kosztu-przestoju') ?>">
                                <span class="icon"><?= Icons::svg('activity', 16) ?></span>
                                <span><?= Lang::t('nav.resources_calculator') ?></span>
                            </a>
                            <a class="sw-mega__item" href="<?= Locale::url('/bezpieczenstwo') ?>">
                                <span class="icon"><?= Icons::svg('lock', 16) ?></span>
                                <span><?= Lang::t('nav.resources_security') ?></span>
                            </a>
                        </div>
                    </div>
                <?php else: ?>
                    <a href="<?= Locale::url($item['url']) ?>"><?= htmlspecialchars($item['label'], ENT_QUOTES, 'UTF-8') ?></a>
                <?php endif; ?>
            <?php endforeach; ?>
        </nav>
        <div class="sw-header__actions">
            <a href="<?= htmlspecialchars($baseUrl . Locale::urlIn(Locale::isDefault() ? 'en' : 'pl', $unprefixedPath), ENT_QUOTES, 'UTF-8') ?>" class="sw-lang-switch" hreflang="<?= Locale::isDefault() ? 'en' : 'pl' ?>"><?= Lang::t('lang.switch_to') ?></a>
            <a href="<?= Locale::url('/kontakt') ?>" class="sw-btn sw-btn--primary"><?= Lang::t('nav.book_call') ?></a>
            <button class="sw-nav-toggle" id="sw-nav-toggle" aria-label="<?= Lang::t('nav.menu_aria') ?>"><?= Icons::svg('menu', 22) ?></button>
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
            <h4><?= Lang::t('footer.nav_heading') ?></h4>
            <?php foreach ($navMenu as $item): if ($item['url'] === '/blog') continue; ?>
                <a href="<?= Locale::url($item['url']) ?>"><?= htmlspecialchars($item['label'], ENT_QUOTES, 'UTF-8') ?></a>
            <?php endforeach; ?>
        </div>
        <div>
            <h4><?= Lang::t('footer.resources_heading') ?></h4>
            <a href="<?= Locale::url('/blog') ?>"><?= Lang::t('nav.resources_blog') ?></a>
            <a href="<?= Locale::url('/bezpieczenstwo') ?>"><?= Lang::t('nav.resources_security') ?></a>
            <a href="<?= Locale::url('/kalkulator-kosztu-przestoju') ?>"><?= Lang::t('nav.resources_calculator') ?></a>
        </div>
        <div>
            <h4><?= Lang::t('footer.legal_heading') ?></h4>
            <a href="<?= Locale::url('/polityka-prywatnosci') ?>"><?= Lang::t('footer.privacy') ?></a>
            <a href="<?= Locale::url('/regulamin') ?>"><?= Lang::t('footer.terms') ?></a>
        </div>
        <div>
            <h4><?= Lang::t('footer.contact_heading') ?></h4>
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
