<?php

namespace SecureWare\Controllers\Admin;

use SecureWare\Core\Auth;
use SecureWare\Core\Config;
use SecureWare\Core\Csrf;
use SecureWare\Core\Logger;
use SecureWare\Core\Request;
use SecureWare\Core\Response;
use SecureWare\Core\Session;
use SecureWare\Core\View;
use SecureWare\Models\Media;
use SecureWare\Models\Setting;

class SettingsController
{
    public function branding(Request $request): void
    {
        Auth::requirePermission('settings.edit');

        echo View::render('admin/settings/branding', [
            'settings' => Setting::all(),
            'media'    => Media::all(),
            'saved'    => Session::flash('saved'),
        ], 'admin/layout');
    }

    public function saveBranding(Request $request): void
    {
        Auth::requirePermission('settings.edit');

        if (!Csrf::verify($request->input('_csrf'))) {
            Response::redirect($this->url('branding'));
        }

        $navMenu   = $this->navMenuFromRequest($request, 'nav_label', 'nav_url');
        $navMenuEn = $this->navMenuFromRequest($request, 'nav_label_en', 'nav_url_en');

        Setting::setMany([
            'site_name'       => (string) $request->input('site_name', 'SecureWare'),
            'site_tagline'    => (string) $request->input('site_tagline', ''),
            'site_tagline_en' => (string) $request->input('site_tagline_en', ''),
            'contact_email'   => (string) $request->input('contact_email', ''),
            'contact_phone'   => (string) $request->input('contact_phone', ''),
            'contact_address' => (string) $request->input('contact_address', ''),
            'color_primary'   => (string) $request->input('color_primary', '#0b5fff'),
            'color_dark'      => (string) $request->input('color_dark', '#0a0f1e'),
            'footer_text'     => (string) $request->input('footer_text', ''),
            'footer_text_en'  => (string) $request->input('footer_text_en', ''),
            'social_linkedin' => (string) $request->input('social_linkedin', ''),
            'social_twitter'  => (string) $request->input('social_twitter', ''),
            'logo_media_id'   => (string) $request->input('logo_media_id', ''),
            'favicon_media_id'=> (string) $request->input('favicon_media_id', ''),
            'nav_menu'        => json_encode($navMenu, JSON_UNESCAPED_UNICODE),
            'nav_menu_en'     => json_encode($navMenuEn, JSON_UNESCAPED_UNICODE),
        ]);

        Logger::record('update', 'settings_branding');
        Session::flash('saved', '1');
        Response::redirect($this->url('branding'));
    }

    public function integrations(Request $request): void
    {
        Auth::requirePermission('settings.edit');

        echo View::render('admin/settings/integrations', [
            'settings' => Setting::all(),
            'saved'    => Session::flash('saved'),
        ], 'admin/layout');
    }

    public function saveIntegrations(Request $request): void
    {
        Auth::requirePermission('settings.edit');

        if (!Csrf::verify($request->input('_csrf'))) {
            Response::redirect($this->url('integrations'));
        }

        Setting::setMany([
            'turnstile_site_key' => (string) $request->input('turnstile_site_key', ''),
            'turnstile_secret'   => (string) $request->input('turnstile_secret', ''),
            'ga_measurement_id'  => (string) $request->input('ga_measurement_id', ''),
            'cookieyes_script'   => (string) $request->input('cookieyes_script', ''),
            'mail_from_address'  => (string) $request->input('mail_from_address', ''),
        ]);

        Logger::record('update', 'settings_integrations');
        Session::flash('saved', '1');
        Response::redirect($this->url('integrations'));
    }

    private function navMenuFromRequest(Request $request, string $labelField, string $urlField): array
    {
        $labels = (array) ($request->all()[$labelField] ?? []);
        $urls   = (array) ($request->all()[$urlField] ?? []);
        $menu   = [];
        foreach ($labels as $i => $label) {
            $label = trim((string) $label);
            $url   = trim((string) ($urls[$i] ?? ''));
            if ($label === '' || $url === '') {
                continue;
            }
            $menu[] = ['label' => $label, 'url' => $url];
        }

        return $menu;
    }

    private function url(string $tab): string
    {
        return '/' . Config::get('admin_path') . '/settings/' . $tab;
    }
}
