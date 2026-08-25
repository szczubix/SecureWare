<?php

namespace SecureWare\Core;

class View
{
    public static function render(string $template, array $data = [], ?string $layout = null): string
    {
        $content = self::renderFile($template, $data);

        if ($layout !== null) {
            $content = self::renderFile($layout, array_merge($data, ['content' => $content]));
        }

        return $content;
    }

    private static function renderFile(string $template, array $data): string
    {
        $path = VIEWS_PATH . '/' . $template . '.php';
        if (!is_file($path)) {
            throw new \RuntimeException("Widok nie istnieje: {$template}");
        }

        extract($data, EXTR_SKIP);
        ob_start();
        require $path;
        return ob_get_clean();
    }

    public static function e(?string $value): string
    {
        return htmlspecialchars((string) $value, ENT_QUOTES, 'UTF-8');
    }
}
