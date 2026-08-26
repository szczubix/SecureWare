<?php
/** @var array $leads */
use SecureWare\Core\Auth;
use SecureWare\Core\Csrf;

$statusLabels = ['new' => 'Nowe', 'contacted' => 'Skontaktowano', 'closed' => 'Zamknięte'];
?>
<div class="toolbar">
    <h1>Zapytania (leady)</h1>
</div>

<div class="admin-card">
    <div class="table-wrap">
    <table class="admin-table">
        <thead><tr><th>Data</th><th>Imię</th><th>Firma</th><th>Kontakt</th><th>Wiadomość</th><th>Źródło</th><th>Status</th></tr></thead>
        <tbody>
        <?php foreach ($leads as $l): ?>
            <tr>
                <td><?= htmlspecialchars($l['created_at'], ENT_QUOTES, 'UTF-8') ?></td>
                <td><?= htmlspecialchars($l['name'], ENT_QUOTES, 'UTF-8') ?></td>
                <td><?= htmlspecialchars($l['company'] ?? '', ENT_QUOTES, 'UTF-8') ?: '—' ?></td>
                <td><?= htmlspecialchars($l['email'], ENT_QUOTES, 'UTF-8') ?><?= $l['phone'] ? '<br>' . htmlspecialchars($l['phone'], ENT_QUOTES, 'UTF-8') : '' ?></td>
                <td style="max-width:280px;"><?= nl2br(htmlspecialchars(mb_strimwidth($l['message'], 0, 200, '…'), ENT_QUOTES, 'UTF-8')) ?></td>
                <td><?= htmlspecialchars($l['source_page'] ?? '', ENT_QUOTES, 'UTF-8') ?></td>
                <td>
                    <?php if (Auth::can('leads.edit')): ?>
                    <form method="post" action="<?= (int) $l['id'] ?>/status">
                        <?= Csrf::field() ?>
                        <select name="status" onchange="this.form.submit()">
                            <?php foreach ($statusLabels as $val => $label): ?>
                                <option value="<?= $val ?>" <?= $l['status'] === $val ? 'selected' : '' ?>><?= $label ?></option>
                            <?php endforeach; ?>
                        </select>
                    </form>
                    <?php else: ?>
                        <span class="badge badge--<?= $l['status'] === 'new' ? 'new' : ($l['status'] === 'closed' ? 'closed' : 'draft') ?>"><?= $statusLabels[$l['status']] ?></span>
                    <?php endif; ?>
                </td>
            </tr>
        <?php endforeach; ?>
        <?php if (!$leads): ?><tr><td colspan="7">Brak zapytań.</td></tr><?php endif; ?>
        </tbody>
    </table>
    </div>
</div>
