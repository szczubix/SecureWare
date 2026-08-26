<?php
/** @var array $pages */
use SecureWare\Core\Auth;
use SecureWare\Core\Csrf;
?>
<div class="toolbar">
    <h1>Podstrony CMS</h1>
    <?php if (Auth::can('pages.edit')): ?><a href="new" class="button">+ Nowa podstrona</a><?php endif; ?>
</div>

<div class="admin-card">
    <div class="table-wrap">
    <table class="admin-table">
        <thead><tr><th>Tytuł</th><th>Adres</th><th>Status</th><th></th></tr></thead>
        <tbody>
        <?php foreach ($pages as $p): ?>
            <tr>
                <td><?= htmlspecialchars($p['title'], ENT_QUOTES, 'UTF-8') ?></td>
                <td>/<?= htmlspecialchars($p['slug'], ENT_QUOTES, 'UTF-8') ?></td>
                <td><span class="badge badge--<?= $p['status'] ?>"><?= $p['status'] === 'published' ? 'Opublikowana' : 'Szkic' ?></span></td>
                <td class="actions">
                    <?php if (Auth::can('pages.edit')): ?><a href="<?= (int) $p['id'] ?>/edit">Edytuj</a><?php endif; ?>
                    <?php if (Auth::can('pages.delete')): ?>
                    <form method="post" action="<?= (int) $p['id'] ?>/delete" onsubmit="return confirm('Usunąć podstronę?');">
                        <?= Csrf::field() ?>
                        <button type="submit" class="link-button" style="color:#d92d20;">Usuń</button>
                    </form>
                    <?php endif; ?>
                </td>
            </tr>
        <?php endforeach; ?>
        <?php if (!$pages): ?><tr><td colspan="4">Brak podstron.</td></tr><?php endif; ?>
        </tbody>
    </table>
    </div>
</div>
