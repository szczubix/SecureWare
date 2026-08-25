<?php

declare(strict_types=1);

define('ROOT_PATH', dirname(__DIR__));
define('VIEWS_PATH', ROOT_PATH . '/views');

spl_autoload_register(function (string $class): void {
    $prefix = 'SecureWare\\';
    if (!str_starts_with($class, $prefix)) {
        return;
    }

    $relative = substr($class, strlen($prefix));
    $path = ROOT_PATH . '/src/' . str_replace('\\', '/', $relative) . '.php';

    if (is_file($path)) {
        require $path;
    }
});

use SecureWare\Core\Config;
use SecureWare\Core\Request;
use SecureWare\Core\Router;
use SecureWare\Core\Session;

Config::load(require ROOT_PATH . '/config/config.php');

if (Config::get('app')['debug']) {
    ini_set('display_errors', '1');
    error_reporting(E_ALL);
} else {
    ini_set('display_errors', '0');
}

date_default_timezone_set('Europe/Warsaw');

Session::start();

$router = new Router();
require ROOT_PATH . '/src/routes.php';

$router->dispatch(new Request());
