<?php

namespace SecureWare\Core;

/**
 * Renderuje diagram (wezly/krawedzie zapisane w bazie przez kreator w
 * panelu admina) do tego samego znacznika SVG co reczne diagramy na
 * stronie glownej (klasy .sw-diagram/.node/.flow/.verified) - dzieki temu
 * automatycznie dziedziczy animacje (przeplyw, puls) z site.css, bez
 * potrzeby osobnego CSS na kazdy diagram.
 */
class DiagramRenderer
{
    public static function card(array $diagram): string
    {
        $svg = self::svg($diagram);

        $title = htmlspecialchars((string) ($diagram['title'] ?? ''), ENT_QUOTES, 'UTF-8');
        $badge = (string) ($diagram['badge'] ?? '');
        $foot  = (string) ($diagram['foot'] ?? '');

        $html = '<div class="sw-diagram-card">';
        if ($title !== '' || $badge !== '') {
            $html .= '<div class="sw-diagram-card__head">';
            if ($title !== '') {
                $html .= '<h3>' . $title . '</h3>';
            }
            if ($badge !== '') {
                $html .= '<span class="sw-diagram-card__live">' . htmlspecialchars($badge, ENT_QUOTES, 'UTF-8') . '</span>';
            }
            $html .= '</div>';
        }
        $html .= $svg;
        if ($foot !== '') {
            $html .= '<div class="sw-diagram-card__foot">' . htmlspecialchars($foot, ENT_QUOTES, 'UTF-8') . '</div>';
        }
        $html .= '</div>';

        return $html;
    }

    public static function svg(array $diagram): string
    {
        $w     = max(1, (int) ($diagram['canvas_width'] ?? 480));
        $h     = max(1, (int) ($diagram['canvas_height'] ?? 380));
        $nodes = $diagram['nodes'] ?? [];
        $edges = $diagram['edges'] ?? [];

        $byId = [];
        foreach ($nodes as $node) {
            if (!empty($node['id'])) {
                $byId[$node['id']] = $node;
            }
        }

        $out = '<svg class="sw-diagram" viewBox="0 0 ' . $w . ' ' . $h . '" xmlns="http://www.w3.org/2000/svg">';

        foreach ($edges as $edge) {
            $from = $byId[$edge['from'] ?? ''] ?? null;
            $to   = $byId[$edge['to'] ?? ''] ?? null;
            if (!$from || !$to) {
                continue;
            }
            $out .= self::edgePath($from, $to);
        }

        foreach ($nodes as $node) {
            $out .= self::nodeGroup($node);
        }

        $out .= '</svg>';

        return $out;
    }

    private static function edgePath(array $from, array $to): string
    {
        $x1 = self::n($from['x'] ?? 0) + self::n($from['w'] ?? 0) / 2;
        $y1 = self::n($from['y'] ?? 0) + self::n($from['h'] ?? 0);
        $x2 = self::n($to['x'] ?? 0) + self::n($to['w'] ?? 0) / 2;
        $y2 = self::n($to['y'] ?? 0);

        if (abs($x1 - $x2) < 0.5) {
            $d = "M{$x1},{$y1} L{$x2},{$y2}";
        } else {
            $mid = ($y1 + $y2) / 2;
            $d = "M{$x1},{$y1} C{$x1},{$mid} {$x2},{$mid} {$x2},{$y2}";
        }

        return '<path class="flow" d="' . $d . '"/>';
    }

    private static function nodeGroup(array $node): string
    {
        $x  = self::n($node['x'] ?? 0);
        $y  = self::n($node['y'] ?? 0);
        $nw = max(20, self::n($node['w'] ?? 160));
        $nh = max(20, self::n($node['h'] ?? 56));

        $style   = ($node['style'] ?? 'default') === 'primary' ? ' primary' : '';
        $icon    = trim((string) ($node['icon'] ?? ''));
        $title   = trim((string) ($node['title'] ?? ''));
        $sub     = trim((string) ($node['subtitle'] ?? ''));
        $verified = !empty($node['verified']);

        $out = '<g class="node' . $style . '">';
        $out .= '<rect x="' . $x . '" y="' . $y . '" width="' . $nw . '" height="' . $nh . '" rx="10"/>';

        $textX = $x + ($icon !== '' ? 50 : 16);
        if ($icon !== '') {
            $iconSize = 22;
            $out .= '<svg class="icon" x="' . ($x + 16) . '" y="' . ($y + $nh / 2 - $iconSize / 2) . '" width="' . $iconSize . '" height="' . $iconSize . '">' . Icons::svg($icon, $iconSize) . '</svg>';
        }

        if ($title !== '' && $sub !== '') {
            $out .= '<text x="' . $textX . '" y="' . ($y + $nh / 2 - 4) . '">' . htmlspecialchars($title, ENT_QUOTES, 'UTF-8') . '</text>';
            $out .= '<text x="' . $textX . '" y="' . ($y + $nh / 2 + 12) . '" class="sub">' . htmlspecialchars($sub, ENT_QUOTES, 'UTF-8') . '</text>';
        } elseif ($title !== '') {
            $out .= '<text x="' . $textX . '" y="' . ($y + $nh / 2 + 4) . '">' . htmlspecialchars($title, ENT_QUOTES, 'UTF-8') . '</text>';
        }

        if ($verified) {
            $out .= '<g class="verified" transform="translate(' . ($x + $nw - 14) . ',' . ($y + $nh - 12) . ')">';
            $out .= '<circle r="10"/><svg x="-6" y="-6" width="12" height="12">' . Icons::svg('check', 12) . '</svg>';
            $out .= '</g>';
        }

        $out .= '</g>';

        return $out;
    }

    private static function n(mixed $v): float
    {
        return round((float) $v, 1);
    }
}
