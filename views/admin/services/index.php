<?php
/** @var array $services */
use SecureWare\Core\Auth;
use SecureWare\Core\Csrf;
?>
<div class="toolbar">
    <h1>Oferta (usługi)</h1>
    <?php if (Auth::can('services.edit')): ?><a href="new" class="button">+ Nowa usługa</a><?php endif; ?>
</div>

<div class="admin-card">
    <div class="table-wrap">
    <table class="admin-table">
        <thead><tr><th>#</th><th>Nazwa</th><th>Adres</th><th>Status</th><th></th></tr></thead>
        <tbody>
        <?php foreach ($services as $s): ?>
            <tr>
                <td><?= (int) $s['position'] ?></td>
                <td><?= htmlspecialchars($s['name'], ENT_QUOTES, 'UTF-8') ?></td>
                <td>/oferta/<?= htmlspecialchars($s['slug'], ENT_QUOTES, 'UTF-8') ?></td>
                <td><span class="badge badge--<?= $s['status'] ?>"><?= $s['status'] === 'published' ? 'Opublikowana' : 'Szkic' ?></span></td>
                <td class="actions">
                    <?php if (Auth::can('services.edit')): ?><a href="<?= (int) $s['id'] ?>/edit">Edytuj</a><?php endif; ?>
                    <?php if (Auth::can('services.delete')): ?>
                    <form method="post" action="<?= (int) $s['id'] ?>/delete" onsubmit="return confirm('Usunąć usługę?');">
                        <?= Csrf::field() ?>
                        <button type="submit" class="link-button" style="color:#d92d20;">Usuń</button>
                    </form>
                    <?php endif; ?>
                </td>
            </tr>
        <?php endforeach; ?>
        <?php if (!$services): ?><tr><td colspan="5">Brak usług.</td></tr><?php endif; ?>
        </tbody>
    </table>
    </div>
</div>
