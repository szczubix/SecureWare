<?php
/** @var array $diagrams */
use SecureWare\Core\Auth;
use SecureWare\Core\Csrf;
?>
<div class="toolbar">
    <h1>Kreator diagramów</h1>
    <?php if (Auth::can('diagrams.edit')): ?><a href="diagrams/new" class="button">+ Nowy diagram</a><?php endif; ?>
</div>
<p class="admin-hint" style="margin:-8px 0 20px;color:#6b7686;">Zbuduj animowany diagram przepływu (węzły + strzałki) i wstaw go w treści artykułu lub strony przyciskiem "Diagram" w edytorze.</p>

<div class="admin-card">
    <div class="table-wrap">
    <table class="admin-table">
        <thead><tr><th>Nazwa</th><th>Slug (do wstawienia)</th><th>Węzły</th><th>Zaktualizowano</th><th></th></tr></thead>
        <tbody>
        <?php foreach ($diagrams as $d): ?>
            <tr>
                <td><?= htmlspecialchars($d['name'], ENT_QUOTES, 'UTF-8') ?></td>
                <td><code><?= htmlspecialchars($d['slug'], ENT_QUOTES, 'UTF-8') ?></code></td>
                <td><?= count($d['nodes']) ?></td>
                <td><?= htmlspecialchars($d['updated_at'], ENT_QUOTES, 'UTF-8') ?></td>
                <td class="actions">
                    <?php if (Auth::can('diagrams.edit')): ?><a href="diagrams/<?= (int) $d['id'] ?>/edit">Edytuj</a><?php endif; ?>
                    <?php if (Auth::can('diagrams.delete')): ?>
                    <form method="post" action="diagrams/<?= (int) $d['id'] ?>/delete" onsubmit="return confirm('Usunąć diagram? Zniknie z miejsc, gdzie jest wstawiony.');">
                        <?= Csrf::field() ?>
                        <button type="submit" class="link-button" style="color:#d92d20;">Usuń</button>
                    </form>
                    <?php endif; ?>
                </td>
            </tr>
        <?php endforeach; ?>
        <?php if (!$diagrams): ?><tr><td colspan="5">Brak diagramów - utwórz pierwszy.</td></tr><?php endif; ?>
        </tbody>
    </table>
    </div>
</div>
