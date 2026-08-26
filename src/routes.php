<?php

/**
 * @var \SecureWare\Core\Router $router
 */

use SecureWare\Controllers\Admin\ArticleController;
use SecureWare\Controllers\Admin\AuthController;
use SecureWare\Controllers\Admin\DashboardController;
use SecureWare\Controllers\Admin\DiagramController;
use SecureWare\Controllers\Admin\HomeContentController;
use SecureWare\Controllers\Admin\LeadController;
use SecureWare\Controllers\Admin\SiteContentController;
use SecureWare\Controllers\Admin\LogController;
use SecureWare\Controllers\Admin\MediaController;
use SecureWare\Controllers\Admin\PageAdminController;
use SecureWare\Controllers\Admin\RoleController;
use SecureWare\Controllers\Admin\ServiceAdminController;
use SecureWare\Controllers\Admin\SettingsController;
use SecureWare\Controllers\Admin\UserController;
use SecureWare\Controllers\Site\BlogController;
use SecureWare\Controllers\Site\ContactController;
use SecureWare\Controllers\Site\HomeController;
use SecureWare\Controllers\Site\OfferController;
use SecureWare\Controllers\Site\PageController;
use SecureWare\Controllers\Site\SeoController;
use SecureWare\Core\Config;

// ---------------------------------------------------------------------
// Panel administracyjny (sciezka konfigurowalna przez ADMIN_PATH w .env)
// ---------------------------------------------------------------------
$a = '/' . Config::get('admin_path');

$router->get($a . '/login', [AuthController::class, 'showLogin']);
$router->post($a . '/login', [AuthController::class, 'login']);
$router->post($a . '/logout', [AuthController::class, 'logout']);

$router->get($a, [DashboardController::class, 'index']);

$router->get($a . '/articles', [ArticleController::class, 'index']);
$router->get($a . '/articles/new', [ArticleController::class, 'create']);
$router->post($a . '/articles', [ArticleController::class, 'store']);
$router->get($a . '/articles/{id}/edit', [ArticleController::class, 'edit']);
$router->post($a . '/articles/{id}', [ArticleController::class, 'update']);
$router->post($a . '/articles/{id}/delete', [ArticleController::class, 'destroy']);

$router->get($a . '/pages', [PageAdminController::class, 'index']);
$router->get($a . '/pages/new', [PageAdminController::class, 'create']);
$router->post($a . '/pages', [PageAdminController::class, 'store']);
$router->get($a . '/pages/{id}/edit', [PageAdminController::class, 'edit']);
$router->post($a . '/pages/{id}', [PageAdminController::class, 'update']);
$router->post($a . '/pages/{id}/delete', [PageAdminController::class, 'destroy']);

$router->get($a . '/services', [ServiceAdminController::class, 'index']);
$router->get($a . '/services/new', [ServiceAdminController::class, 'create']);
$router->post($a . '/services', [ServiceAdminController::class, 'store']);
$router->get($a . '/services/{id}/edit', [ServiceAdminController::class, 'edit']);
$router->post($a . '/services/{id}', [ServiceAdminController::class, 'update']);
$router->post($a . '/services/{id}/delete', [ServiceAdminController::class, 'destroy']);

$router->get($a . '/media', [MediaController::class, 'index']);
$router->get($a . '/media/list.json', [MediaController::class, 'listJson']);
$router->post($a . '/media/upload', [MediaController::class, 'upload']);
$router->post($a . '/media/upload.json', [MediaController::class, 'uploadJson']);
$router->post($a . '/media/{id}/delete', [MediaController::class, 'destroy']);

$router->get($a . '/diagrams', [DiagramController::class, 'index']);
$router->get($a . '/diagrams/list.json', [DiagramController::class, 'listJson']);
$router->get($a . '/diagrams/new', [DiagramController::class, 'create']);
$router->post($a . '/diagrams', [DiagramController::class, 'store']);
$router->get($a . '/diagrams/{id}/edit', [DiagramController::class, 'edit']);
$router->post($a . '/diagrams/{id}', [DiagramController::class, 'update']);
$router->post($a . '/diagrams/{id}/delete', [DiagramController::class, 'destroy']);

$router->get($a . '/users', [UserController::class, 'index']);
$router->get($a . '/users/new', [UserController::class, 'create']);
$router->post($a . '/users', [UserController::class, 'store']);
$router->get($a . '/users/{id}/edit', [UserController::class, 'edit']);
$router->post($a . '/users/{id}', [UserController::class, 'update']);
$router->post($a . '/users/{id}/delete', [UserController::class, 'destroy']);

$router->get($a . '/roles', [RoleController::class, 'index']);
$router->get($a . '/roles/new', [RoleController::class, 'create']);
$router->post($a . '/roles', [RoleController::class, 'store']);
$router->get($a . '/roles/{id}/edit', [RoleController::class, 'edit']);
$router->post($a . '/roles/{id}', [RoleController::class, 'update']);
$router->post($a . '/roles/{id}/delete', [RoleController::class, 'destroy']);

$router->get($a . '/settings/branding', [SettingsController::class, 'branding']);
$router->post($a . '/settings/branding', [SettingsController::class, 'saveBranding']);
$router->get($a . '/settings/integrations', [SettingsController::class, 'integrations']);
$router->post($a . '/settings/integrations', [SettingsController::class, 'saveIntegrations']);
$router->get($a . '/settings/homepage', [HomeContentController::class, 'edit']);
$router->post($a . '/settings/homepage', [HomeContentController::class, 'save']);
$router->get($a . '/settings/pages-content', [SiteContentController::class, 'edit']);
$router->post($a . '/settings/pages-content', [SiteContentController::class, 'save']);

$router->get($a . '/logs', [LogController::class, 'index']);

$router->get($a . '/leads', [LeadController::class, 'index']);
$router->post($a . '/leads/{id}/status', [LeadController::class, 'updateStatus']);

// ---------------------------------------------------------------------
// Strona publiczna
// ---------------------------------------------------------------------
$router->get('/', [HomeController::class, 'index']);

$router->get('/oferta', [OfferController::class, 'index']);
$router->get('/oferta/{slug}', [OfferController::class, 'show']);

$router->get('/blog', [BlogController::class, 'index']);
$router->get('/blog/{slug}', [BlogController::class, 'show']);

$router->get('/kontakt', [ContactController::class, 'show']);
$router->post('/kontakt', [ContactController::class, 'submit']);

$router->get('/sitemap.xml', [SeoController::class, 'sitemap']);
$router->get('/robots.txt', [SeoController::class, 'robots']);

// Katalog stron CMS - musi byc zarejestrowany jako ostatni (dopasowuje dowolny slug).
$router->get('/{slug}', [PageController::class, 'show']);
