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
use SecureWare\Models\SiteContent;

class SiteContentController
{
    public function edit(Request $request): void
    {
        Auth::requirePermission('settings.edit');

        echo View::render('admin/settings/pages-content', [
            'content' => SiteContent::current(),
            'saved'   => Session::flash('saved'),
        ], 'admin/layout');
    }

    public function save(Request $request): void
    {
        Auth::requirePermission('settings.edit');

        if (!Csrf::verify($request->input('_csrf'))) {
            Response::redirect($this->url());
        }

        $in = $request->all();
        $text = static fn (string $key, string $default = '') => (string) ($in[$key] ?? $default);

        $highlights = $this->rows($in, 'offer_highlight', ['icon', 'text']);

        $content = [
            'offer' => [
                'eyebrow'           => $text('offer_eyebrow'),
                'heading_pre'       => $text('offer_heading_pre'),
                'heading_highlight' => $text('offer_heading_highlight'),
                'heading_post'      => $text('offer_heading_post'),
                'lead'              => $text('offer_lead'),
                'highlights'        => $highlights,
                'empty_text'        => $text('offer_empty_text'),
                'cta_heading'       => $text('offer_cta_heading'),
                'cta_text'          => $text('offer_cta_text'),
                'cta_button_label'  => $text('offer_cta_button_label'),
            ],
            'blog' => [
                'eyebrow'           => $text('blog_eyebrow'),
                'heading_pre'       => $text('blog_heading_pre'),
                'heading_highlight' => $text('blog_heading_highlight'),
                'heading_post'      => $text('blog_heading_post'),
                'lead'              => $text('blog_lead'),
            ],
            'contact' => [
                'eyebrow'           => $text('contact_eyebrow'),
                'heading_pre'       => $text('contact_heading_pre'),
                'heading_highlight' => $text('contact_heading_highlight'),
                'heading_post'      => $text('contact_heading_post'),
                'lead'              => $text('contact_lead'),
                'info_heading'      => $text('contact_info_heading'),
                'info_text'         => $text('contact_info_text'),
                'success_message'   => $text('contact_success_message'),
                'submit_label'      => $text('contact_submit_label'),
            ],
            'not_found' => [
                'heading'       => $text('nf_heading'),
                'text'          => $text('nf_text'),
                'primary_label' => $text('nf_primary_label'),
            ],
        ];

        SiteContent::save($content);

        Logger::record('update', 'site_page_content');
        Session::flash('saved', '1');
        Response::redirect($this->url());
    }

    private function rows(array $in, string $prefix, array $fields): array
    {
        $columns = [];
        $count = 0;
        foreach ($fields as $field) {
            $values = (array) ($in[$prefix . '_' . $field] ?? []);
            $columns[$field] = $values;
            $count = max($count, count($values));
        }

        $rows = [];
        for ($i = 0; $i < $count; $i++) {
            $row = [];
            $hasContent = false;
            foreach ($fields as $field) {
                $value = (string) ($columns[$field][$i] ?? '');
                $row[$field] = $value;
                if (trim($value) !== '') {
                    $hasContent = true;
                }
            }
            if ($hasContent) {
                $rows[] = $row;
            }
        }

        return $rows;
    }

    private function url(): string
    {
        return '/' . Config::get('admin_path') . '/settings/pages-content';
    }
}
