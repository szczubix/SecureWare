<?php
/** @var array $users */
use SecureWare\Core\Auth;
use SecureWare\Core\Csrf;
?>
<div class="toolbar">
    <h1>Użytkownicy</h1>
    <?php if (Auth::can('users.edit')): ?><a href="new" class="button">+ Nowy użytkownik</a><?php endif; ?>
</div>

<div class="admin-card">
    <div class="table-wrap">
    <table class="admin-table">
        <thead><tr><th>Imię i nazwisko</th><th>E-mail</th><th>Rola</th><th>Status</th><th>Ostatnie logowanie</th><th></th></tr></thead>
        <tbody>
        <?php foreach ($users as $u): ?>
            <tr>
                <td><?= htmlspecialchars($u['name'], ENT_QUOTES, 'UTF-8') ?></td>
                <td><?= htmlspecialchars($u['email'], ENT_QUOTES, 'UTF-8') ?></td>
                <td><?= htmlspecialchars($u['role_name'], ENT_QUOTES, 'UTF-8') ?></td>
                <td><span class="badge badge--<?= $u['status'] ?>"><?= $u['status'] === 'active' ? 'Aktywny' : 'Zablokowany' ?></span></td>
                <td><?= $u['last_login_at'] ? htmlspecialchars($u['last_login_at'], ENT_QUOTES, 'UTF-8') : '—' ?></td>
                <td class="actions">
                    <?php if (Auth::can('users.edit')): ?><a href="<?= (int) $u['id'] ?>/edit">Edytuj</a><?php endif; ?>
                    <?php if (Auth::can('users.delete') && (int) $u['id'] !== Auth::id()): ?>
                    <form method="post" action="<?= (int) $u['id'] ?>/delete" onsubmit="return confirm('Usunąć użytkownika?');">
                        <?= Csrf::field() ?>
                        <button type="submit" class="link-button" style="color:#d92d20;">Usuń</button>
                    </form>
                    <?php endif; ?>
                </td>
            </tr>
        <?php endforeach; ?>
        </tbody>
    </table>
    </div>
</div>
