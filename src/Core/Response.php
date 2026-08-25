<?php

namespace SecureWare\Core;

class Response
{
    public static function redirect(string $to): never
    {
        header('Location: ' . $to);
        exit;
    }

    public static function notFound(): never
    {
        http_response_code(404);
        echo View::render('site/404', [
            'metaTitle'       => 'Strona nie znaleziona — SecureWare',
            'metaDescription' => '',
        ], 'site/layout');
        exit;
    }

    public static function json(array $data, int $status = 200): never
    {
        http_response_code($status);
        header('Content-Type: application/json; charset=utf-8');
        echo json_encode($data, JSON_UNESCAPED_UNICODE);
        exit;
    }
}
