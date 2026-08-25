<?php
/** @var array $roles */
use SecureWare\Core\Auth;
use SecureWare\Core\Csrf;
use SecureWare\Core\Session;

$error = Session::flash('error');
?>
<div class="toolbar">
    <h1>Role i uprawnienia</h1>
    <?php if (Auth::can('roles.edit')): ?><a href="new" class="button">+ Nowa rola</a><?php endif; ?>
</div>

<?php if ($error): ?><p class="alert alert--error"><?= htmlspecialchars($error, ENT_QUOTES, 'UTF-8') ?></p><?php endif; ?>

<div class="admin-card">
    <div class="table-wrap">
    <table class="admin-table">
        <thead><tr><th>Nazwa</th><th>Identyfikator</th><th></th></tr></thead>
        <tbody>
        <?php foreach ($roles as $r): ?>
            <tr>
                <td><?= htmlspecialchars($r['name'], ENT_QUOTES, 'UTF-8') ?></td>
                <td><?= htmlspecialchars($r['slug'], ENT_QUOTES, 'UTF-8') ?></td>
                <td class="actions">
                    <?php if (Auth::can('roles.edit')): ?><a href="<?= (int) $r['id'] ?>/edit">Edytuj</a><?php endif; ?>
                    <?php if (Auth::can('roles.delete')): ?>
                    <form method="post" action="<?= (int) $r['id'] ?>/delete" onsubmit="return confirm('Usunac role?');">
                        <?= Csrf::field() ?>
                        <button type="submit" class="link-button" style="color:#d92d20;">Usun</button>
                    </form>
                    <?php endif; ?>
                </td>
            </tr>
        <?php endforeach; ?>
        </tbody>
    </table>
    </div>
</div>
