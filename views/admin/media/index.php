<?php
/** @var array $media */
/** @var string|null $error */
use SecureWare\Core\Auth;
use SecureWare\Core\Csrf;
?>
<div class="toolbar">
    <h1>Biblioteka mediow</h1>
</div>

<?php if ($error): ?><p class="alert alert--error"><?= htmlspecialchars($error, ENT_QUOTES, 'UTF-8') ?></p><?php endif; ?>

<?php if (Auth::can('media.upload')): ?>
<div class="admin-card">
    <h2>Wgraj plik</h2>
    <form method="post" action="upload" enctype="multipart/form-data" class="field-check" style="gap:12px;">
        <?= Csrf::field() ?>
        <input type="file" name="file" required accept=".jpg,.jpeg,.png,.webp,.gif,.pdf">
        <button type="submit" class="button">Wgraj</button>
    </form>
    <p class="hint">Dozwolone: JPG, PNG, WEBP, GIF, PDF. Limit 8 MB.</p>
</div>
<?php endif; ?>

<div class="media-grid">
    <?php foreach ($media as $m): ?>
        <div class="media-item">
            <?php if (str_starts_with($m['mime'], 'image/')): ?>
                <img src="<?= htmlspecialchars($m['path'], ENT_QUOTES, 'UTF-8') ?>" alt="">
            <?php else: ?>
                <div style="height:100px;display:flex;align-items:center;justify-content:center;background:#f2f4f7;font-size:12px;color:#667085;">PDF</div>
            <?php endif; ?>
            <div class="media-item__meta">
                <span title="<?= htmlspecialchars($m['filename'], ENT_QUOTES, 'UTF-8') ?>"><?= htmlspecialchars(mb_strimwidth($m['filename'], 0, 16, '…'), ENT_QUOTES, 'UTF-8') ?></span>
                <?php if (Auth::can('media.delete')): ?>
                <form method="post" action="<?= (int) $m['id'] ?>/delete" onsubmit="return confirm('Usunac ten plik?');">
                    <?= Csrf::field() ?>
                    <button type="submit" class="link-button" style="color:#d92d20;">Usun</button>
                </form>
                <?php endif; ?>
            </div>
        </div>
    <?php endforeach; ?>
    <?php if (!$media): ?><p>Brak plikow w bibliotece.</p><?php endif; ?>
</div>
