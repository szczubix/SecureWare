<?php

namespace SecureWare\Core;

/**
 * Male, recznie napisane ikony SVG (styl outline) - bez zaleznosci od CDN
 * czy zewnetrznych bibliotek ikon.
 */
class Icons
{
    private const MAP = [
        'shield-check'     => '<path d="M12 3l7 3v6c0 4.5-3 8-7 9-4-1-7-4.5-7-9V6l7-3z"/><path d="M9 12l2 2 4-4"/>',
        'shield'           => '<path d="M12 3l7 3v6c0 4.5-3 8-7 9-4-1-7-4.5-7-9V6l7-3z"/>',
        'cloud-upload'     => '<path d="M7 18a4 4 0 0 1-.5-7.97A5 5 0 0 1 16 8a4.5 4.5 0 0 1 1 8.9"/><path d="M12 12v7"/><path d="M9 15l3-3 3 3"/>',
        'map-pin'          => '<path d="M12 21s7-6.5 7-11a7 7 0 1 0-14 0c0 4.5 7 11 7 11z"/><circle cx="12" cy="10" r="2.5"/>',
        'lock'             => '<rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/>',
        'mail'             => '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M4 7l8 6 8-6"/>',
        'server'           => '<rect x="4" y="4" width="16" height="6" rx="1.5"/><rect x="4" y="14" width="16" height="6" rx="1.5"/><circle cx="8" cy="7" r=".8" fill="currentColor" stroke="none"/><circle cx="8" cy="17" r=".8" fill="currentColor" stroke="none"/>',
        'layers'           => '<path d="M12 3l9 5-9 5-9-5 9-5z"/><path d="M3 13l9 5 9-5"/>',
        'life-buoy'        => '<circle cx="12" cy="12" r="8.5"/><circle cx="12" cy="12" r="3.2"/><path d="M6 6l3.5 3.5M18 6l-3.5 3.5M6 18l3.5-3.5M18 18l-3.5-3.5"/>',
        'refresh-ccw'      => '<path d="M3 12a9 9 0 1 0 3-6.7"/><path d="M3 4v5h5"/>',
        'clipboard-check'  => '<rect x="6" y="4" width="12" height="17" rx="2"/><path d="M9 4V3a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v1"/><path d="M9 13l2 2 4-4"/>',
        'tool'             => '<path d="M14.7 6.3a4 4 0 0 1-5.4 5.4L4 17l3 3 5.3-5.3a4 4 0 0 1 5.4-5.4l-2.5 2.5-2-2 2.5-2.5z"/>',
        'activity'         => '<path d="M3 12h4l2 8 4-16 2 8h6"/>',
        'file-check'       => '<path d="M7 3h7l5 5v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z"/><path d="M14 3v5h5"/><path d="M9.5 14.5l1.7 1.7 3.3-3.4"/>',
        'arrow-right'      => '<path d="M4 12h16"/><path d="M14 6l6 6-6 6"/>',
        'check'            => '<path d="M4 12l5 5L20 6"/>',
        'menu'             => '<path d="M4 7h16M4 12h16M4 17h16"/>',
        'x'                => '<path d="M6 6l12 12M18 6L6 18"/>',
        'phone'            => '<path d="M6 3h3l2 5-2.5 2A12 12 0 0 0 14 15.5l2-2.5 5 2v3a2 2 0 0 1-2.2 2A17 17 0 0 1 4 5.2 2 2 0 0 1 6 3z"/>',
        'linkedin'         => '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M8 10v7M8 7.2v.1M12 17v-4.5a2 2 0 0 1 4 0V17"/>',
        'twitter'          => '<path d="M21 5.5a8 8 0 0 1-2.3.65 4 4 0 0 0 1.76-2.2 8 8 0 0 1-2.55 1A4 4 0 0 0 11 8.5c0 .3 0 .6.1.9A11.4 11.4 0 0 1 3 4.9a4 4 0 0 0 1.24 5.3A4 4 0 0 1 2.4 9.6v.05A4 4 0 0 0 5.6 13.5a4 4 0 0 1-1.8.07 4 4 0 0 0 3.7 2.75A8 8 0 0 1 2 18a11.3 11.3 0 0 0 6.1 1.8c7.3 0 11.3-6 11.3-11.3v-.5A8 8 0 0 0 21 5.5z"/>',
        'quote'            => '<path d="M7 7h4v5a4 4 0 0 1-4 4H6v-2h1a2 2 0 0 0 2-2H7V7z"/><path d="M15 7h4v5a4 4 0 0 1-4 4h-1v-2h1a2 2 0 0 0 2-2h-2V7z"/>',
        'chevron-down'     => '<path d="M6 9l6 6 6-6"/>',
    ];

    public static function svg(string $name, int $size = 24): string
    {
        $inner = self::MAP[$name] ?? self::MAP['shield'];
        return sprintf(
            '<svg xmlns="http://www.w3.org/2000/svg" width="%1$d" height="%1$d" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">%2$s</svg>',
            $size,
            $inner
        );
    }
}
