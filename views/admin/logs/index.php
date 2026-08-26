<?php
/** @var array $logs */
/** @var int $total */
/** @var int $page */
/** @var int $perPage */
$totalPages = max(1, (int) ceil($total / $perPage));

$actionLabels = [
    'login' => 'Logowanie', 'logout' => 'Wylogowanie',
    'create' => 'Utworzono', 'update' => 'Zaktualizowano', 'delete' => 'Usunięto',
    'upload' => 'Wgrano plik',
];
?>
<div class="toolbar">
    <h1>Logi aktywności</h1>
</div>

<div class="admin-card">
    <div class="table-wrap">
    <table class="admin-table">
        <thead><tr><th>Data</th><th>Użytkownik</th><th>Akcja</th><th>Obiekt</th><th>IP</th></tr></thead>
        <tbody>
        <?php foreach ($logs as $l): ?>
            <tr>
                <td><?= htmlspecialchars($l['created_at'], ENT_QUOTES, 'UTF-8') ?></td>
                <td><?= htmlspecialchars($l['user_name'] ?? 'system', ENT_QUOTES, 'UTF-8') ?></td>
                <td><?= htmlspecialchars($actionLabels[$l['action']] ?? $l['action'], ENT_QUOTES, 'UTF-8') ?></td>
                <td><?= htmlspecialchars($l['entity_type'], ENT_QUOTES, 'UTF-8') ?><?= $l['entity_id'] ? ' #' . (int) $l['entity_id'] : '' ?></td>
                <td><?= htmlspecialchars($l['ip'], ENT_QUOTES, 'UTF-8') ?></td>
            </tr>
        <?php endforeach; ?>
        <?php if (!$logs): ?><tr><td colspan="5">Brak wpisów.</td></tr><?php endif; ?>
        </tbody>
    </table>
    </div>

    <?php if ($totalPages > 1): ?>
    <div class="pagination">
        <?php for ($p = 1; $p <= $totalPages; $p++): ?>
            <?php if ($p === $page): ?><span class="current"><?= $p ?></span>
            <?php else: ?><a href="?page=<?= $p ?>"><?= $p ?></a><?php endif; ?>
        <?php endfor; ?>
    </div>
    <?php endif; ?>
</div>
