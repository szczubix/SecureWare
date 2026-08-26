<?php
/** @var array $stats */
use SecureWare\Core\Auth;
use SecureWare\Core\Config;

$adminUrl = '/' . Config::get('admin_path');
?>
<div class="admin-header">
    <h1>Pulpit</h1>
    <p>Witaj, <?= htmlspecialchars(Auth::user()['name'], ENT_QUOTES, 'UTF-8') ?>.</p>
</div>

<div class="stat-grid">
    <div class="stat-card">
        <span class="stat-card__value"><?= $stats['articles'] ?></span>
        <span class="stat-card__label">Artykuły na blogu</span>
    </div>
    <div class="stat-card">
        <span class="stat-card__value"><?= $stats['pages'] ?></span>
        <span class="stat-card__label">Podstrony CMS</span>
    </div>
    <div class="stat-card">
        <span class="stat-card__value"><?= $stats['services'] ?></span>
        <span class="stat-card__label">Usługi w ofercie</span>
    </div>
    <div class="stat-card stat-card--highlight">
        <span class="stat-card__value"><?= $stats['leads_new'] ?></span>
        <span class="stat-card__label">Nowe zapytania</span>
    </div>
</div>

<div class="admin-card">
    <h2>Skróty</h2>
    <div class="quick-links">
        <?php if (Auth::can('articles.edit')): ?><a href="<?= $adminUrl ?>/articles/new" class="button">+ Nowy artykuł</a><?php endif; ?>
        <?php if (Auth::can('services.edit')): ?><a href="<?= $adminUrl ?>/services/new" class="button">+ Nowa usługa</a><?php endif; ?>
        <?php if (Auth::can('pages.edit')): ?><a href="<?= $adminUrl ?>/pages/new" class="button">+ Nowa podstrona</a><?php endif; ?>
        <?php if (Auth::can('leads.view')): ?><a href="<?= $adminUrl ?>/leads" class="button button--ghost">Zobacz zapytania</a><?php endif; ?>
    </div>
</div>
