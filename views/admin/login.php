<?php
/** @var string|null $error */
use SecureWare\Core\Csrf;
?><!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Logowanie · Panel SecureWare</title>
<link rel="stylesheet" href="/assets/css/admin.css">
</head>
<body class="admin admin-login-page">
    <form class="login-card" method="post" action="">
        <div class="login-card__brand">SecureWare<span>panel</span></div>
        <?php if (!empty($error)): ?>
            <p class="alert alert--error"><?= htmlspecialchars($error, ENT_QUOTES, 'UTF-8') ?></p>
        <?php endif; ?>
        <?= Csrf::field() ?>
        <label>E-mail
            <input type="email" name="email" required autofocus>
        </label>
        <label>Haslo
            <input type="password" name="password" required>
        </label>
        <button type="submit">Zaloguj sie</button>
    </form>
</body>
</html>
