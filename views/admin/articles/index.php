<?php
/** @var array $articles */
use SecureWare\Core\Auth;
use SecureWare\Core\Csrf;
?>
<div class="toolbar">
    <h1>Artykuły (blog)</h1>
    <?php if (Auth::can('articles.edit')): ?><a href="new" class="button">+ Nowy artykuł</a><?php endif; ?>
</div>

<div class="admin-card">
    <div class="table-wrap">
    <table class="admin-table">
        <thead><tr><th>Tytuł</th><th>Kategoria</th><th>Status</th><th>Data publikacji</th><th></th></tr></thead>
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
                    <form method="post" action="<?= (int) $a['id'] ?>/delete" onsubmit="return confirm('Usunąć artykuł?');">
                        <?= Csrf::field() ?>
                        <button type="submit" class="link-button" style="color:#d92d20;">Usuń</button>
                    </form>
                    <?php endif; ?>
                </td>
            </tr>
        <?php endforeach; ?>
        <?php if (!$articles): ?><tr><td colspan="5">Brak artykułów.</td></tr><?php endif; ?>
        </tbody>
    </table>
    </div>
</div>
