<?php
/** @var array $articles */
use SecureWare\Core\Auth;
use SecureWare\Core\Csrf;
?>
<div class="toolbar">
    <h1>Artykuly (blog)</h1>
    <?php if (Auth::can('articles.edit')): ?><a href="new" class="button">+ Nowy artykul</a><?php endif; ?>
</div>

<div class="admin-card">
    <div class="table-wrap">
    <table class="admin-table">
        <thead><tr><th>Tytul</th><th>Kategoria</th><th>Status</th><th>Data publikacji</th><th></th></tr></thead>
        <tbody>
        <?php foreach ($articles as $a): ?>
            <tr>
                <td><?= htmlspecialchars($a['title'], ENT_QUOTES, 'UTF-8') ?></td>
                <td><?= htmlspecialchars($a['category_name'] ?? '—', ENT_QUOTES, 'UTF-8') ?></td>
                <td><span class="badge badge--<?= $a['status'] ?>"><?= $a['status'] === 'published' ? 'Opublikowany' : 'Szkic' ?></span></td>
                <td><?= $a['published_at'] ? htmlspecialchars($a['published_at'], ENT_QUOTES, 'UTF-8') : '—' ?></td>
                <td class="actions">
                    <?php if (Auth::can('articles.edit')): ?><a href="<?= (int) $a['id'] ?>/edit">Edytuj</a><?php endif; ?>
                    <?php if (Auth::can('articles.delete')): ?>
                    <form method="post" action="<?= (int) $a['id'] ?>/delete" onsubmit="return confirm('Usunac artykul?');">
                        <?= Csrf::field() ?>
                        <button type="submit" class="link-button" style="color:#d92d20;">Usun</button>
                    </form>
                    <?php endif; ?>
                </td>
            </tr>
        <?php endforeach; ?>
        <?php if (!$articles): ?><tr><td colspan="5">Brak artykulow.</td></tr><?php endif; ?>
        </tbody>
    </table>
    </div>
</div>
