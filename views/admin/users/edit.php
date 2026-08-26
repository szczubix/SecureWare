<?php
/** @var array|null $editUser */
/** @var array $roles */
/** @var string|null $error */
use SecureWare\Core\Config;
use SecureWare\Core\Csrf;

$adminUrl = '/' . Config::get('admin_path');
$isEdit   = $editUser !== null;
$action   = $isEdit ? $adminUrl . '/users/' . $editUser['id'] : $adminUrl . '/users';
?>
<div class="toolbar">
    <h1><?= $isEdit ? 'Edytuj użytkownika' : 'Nowy użytkownik' ?></h1>
    <a href="<?= $adminUrl ?>/users" class="button button--ghost">← Wróć do listy</a>
</div>

<?php if ($error): ?><p class="alert alert--error"><?= htmlspecialchars($error, ENT_QUOTES, 'UTF-8') ?></p><?php endif; ?>

<div class="admin-card">
    <form method="post" action="<?= $action ?>" class="form-grid">
        <?= Csrf::field() ?>

        <div class="field">
            <label>Imię i nazwisko</label>
            <input type="text" name="name" required value="<?= htmlspecialchars($editUser['name'] ?? '', ENT_QUOTES, 'UTF-8') ?>">
        </div>

        <div class="field">
            <label>E-mail</label>
            <input type="email" name="email" required value="<?= htmlspecialchars($editUser['email'] ?? '', ENT_QUOTES, 'UTF-8') ?>">
        </div>

        <div class="field">
            <label>Hasło <?= $isEdit ? '(zostaw puste, aby nie zmieniać)' : '' ?></label>
            <input type="password" name="password" <?= $isEdit ? '' : 'required' ?>>
        </div>

        <div class="form-row">
            <div class="field">
                <label>Rola</label>
                <select name="role_id" required>
                    <?php foreach ($roles as $r): ?>
                        <option value="<?= (int) $r['id'] ?>" <?= (isset($editUser['role_id']) && (int) $editUser['role_id'] === (int) $r['id']) ? 'selected' : '' ?>>
                            <?= htmlspecialchars($r['name'], ENT_QUOTES, 'UTF-8') ?>
                        </option>
                    <?php endforeach; ?>
                </select>
            </div>
            <div class="field">
                <label>Status</label>
                <select name="status">
                    <option value="active" <?= (($editUser['status'] ?? 'active') === 'active') ? 'selected' : '' ?>>Aktywny</option>
                    <option value="disabled" <?= (($editUser['status'] ?? '') === 'disabled') ? 'selected' : '' ?>>Zablokowany</option>
                </select>
            </div>
        </div>

        <div class="form-actions">
            <button type="submit" class="button">Zapisz</button>
            <a href="<?= $adminUrl ?>/users" class="button button--ghost">Anuluj</a>
        </div>
    </form>
</div>
