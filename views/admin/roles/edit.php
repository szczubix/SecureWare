<?php
/** @var array|null $role */
/** @var array $permissions */
/** @var array $assignedIds */
/** @var string|null $error */
use SecureWare\Core\Config;
use SecureWare\Core\Csrf;

$adminUrl = '/' . Config::get('admin_path');
$isEdit   = $role !== null;
$action   = $isEdit ? $adminUrl . '/roles/' . $role['id'] : $adminUrl . '/roles';
?>
<div class="toolbar">
    <h1><?= $isEdit ? 'Edytuj rolę' : 'Nowa rola' ?></h1>
    <a href="<?= $adminUrl ?>/roles" class="button button--ghost">← Wróć do listy</a>
</div>

<?php if ($error): ?><p class="alert alert--error"><?= htmlspecialchars($error, ENT_QUOTES, 'UTF-8') ?></p><?php endif; ?>

<div class="admin-card">
    <form method="post" action="<?= $action ?>" class="form-grid form-grid--wide">
        <?= Csrf::field() ?>

        <div class="form-row">
            <div class="field">
                <label>Nazwa roli</label>
                <input type="text" name="name" required value="<?= htmlspecialchars($role['name'] ?? '', ENT_QUOTES, 'UTF-8') ?>">
            </div>
            <div class="field">
                <label>Identyfikator (slug)</label>
                <input type="text" name="slug" placeholder="generowany automatycznie" value="<?= htmlspecialchars($role['slug'] ?? '', ENT_QUOTES, 'UTF-8') ?>">
            </div>
        </div>

        <div class="field">
            <label>Uprawnienia</label>
            <div class="perm-grid">
                <?php foreach ($permissions as $p): ?>
                    <label>
                        <input type="checkbox" name="permissions[]" value="<?= (int) $p['id'] ?>"
                            <?= in_array((int) $p['id'], $assignedIds, true) ? 'checked' : '' ?>>
                        <?= htmlspecialchars($p['label'], ENT_QUOTES, 'UTF-8') ?>
                    </label>
                <?php endforeach; ?>
            </div>
        </div>

        <div class="form-actions">
            <button type="submit" class="button">Zapisz</button>
            <a href="<?= $adminUrl ?>/roles" class="button button--ghost">Anuluj</a>
        </div>
    </form>
</div>
