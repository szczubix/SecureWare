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
use SecureWare\Models\HomeContent;

class HomeContentController
{
    public function edit(Request $request): void
    {
        Auth::requirePermission('settings.edit');

        $lang = $request->input('lang') === 'en' ? 'en' : 'pl';

        echo View::render('admin/settings/homepage', [
            'content' => HomeContent::current($lang),
            'saved'   => Session::flash('saved'),
            'lang'    => $lang,
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

        $specs = $this->rows($in, 'hero_spec', ['count', 'suffix', 'value', 'label']);
        $stats = $this->rows($in, 'stats', ['count', 'suffix', 'value', 'label']);
        $tabs  = $this->rows($in, 'platform_tab', ['icon', 'title', 'subtitle', 'panel_title', 'panel_text', 'bullets']);
        $ruleItems = $this->rows($in, 'rule_item', ['icon', 'num', 'label', 'text']);
        $whyItems  = $this->rows($in, 'why_item', ['title', 'text']);
        $stepItems = $this->rows($in, 'steps_item', ['title', 'text']);
        $faqItems  = $this->rows($in, 'faq', ['question', 'answer']);

        foreach ([&$specs, &$stats] as &$list) {
            foreach ($list as &$item) {
                $item['count'] = ($item['count'] ?? '') === '' ? null : (int) $item['count'];
            }
            unset($item);
        }
        unset($list);

        $content = [
            'hero' => [
                'eyebrow'             => $text('hero_eyebrow'),
                'headline_pre'        => $text('hero_headline_pre'),
                'headline_highlight'  => $text('hero_headline_highlight'),
                'headline_post'       => $text('hero_headline_post'),
                'lead'                => $text('hero_lead'),
                'cta_primary_label'   => $text('hero_cta_primary_label'),
                'cta_primary_url'     => $text('hero_cta_primary_url'),
                'cta_secondary_label' => $text('hero_cta_secondary_label'),
                'cta_secondary_url'   => $text('hero_cta_secondary_url'),
                'specs'               => $specs,
                'diagram_title'       => $text('hero_diagram_title'),
                'diagram_badge'       => $text('hero_diagram_badge'),
                'diagram_foot'        => $text('hero_diagram_foot'),
            ],
            'offer' => [
                'eyebrow'   => $text('offer_eyebrow'),
                'heading'   => $text('offer_heading'),
                'intro'     => $text('offer_intro'),
                'cta_label' => $text('offer_cta_label'),
            ],
            'stack' => [
                'eyebrow' => $text('stack_eyebrow'),
                'items'   => $text('stack_items'),
            ],
            'stats' => ['items' => $stats],
            'platform' => [
                'eyebrow' => $text('platform_eyebrow'),
                'heading' => $text('platform_heading'),
                'intro'   => $text('platform_intro'),
                'tabs'    => $tabs,
            ],
            'rule' => [
                'eyebrow' => $text('rule_eyebrow'),
                'heading' => $text('rule_heading'),
                'intro'   => $text('rule_intro'),
                'items'   => $ruleItems,
            ],
            'ransomware' => [
                'eyebrow'         => $text('ransomware_eyebrow'),
                'heading'         => $text('ransomware_heading'),
                'intro'           => $text('ransomware_intro'),
                'protected_label' => $text('ransomware_protected_label'),
            ],
            'scenario' => [
                'eyebrow'         => $text('scenario_eyebrow'),
                'heading'         => $text('scenario_heading'),
                'intro'           => $text('scenario_intro'),
                'threat_badge'    => $text('scenario_threat_badge'),
                'threat_lines'    => $text('scenario_threat_lines'),
                'threat_amount'   => (int) $text('scenario_threat_amount', '0'),
                'threat_suffix'   => $text('scenario_threat_suffix'),
                'threat_deadline' => $text('scenario_threat_deadline'),
                'safe_badge'      => $text('scenario_safe_badge'),
                'safe_intro'      => $text('scenario_safe_intro'),
                'safe_checklist'  => $text('scenario_safe_checklist'),
                'safe_result'     => $text('scenario_safe_result'),
            ],
            'why' => [
                'eyebrow'    => $text('why_eyebrow'),
                'heading'    => $text('why_heading'),
                'intro'      => $text('why_intro'),
                'link_label' => $text('why_link_label'),
                'items'      => $whyItems,
            ],
            'certs' => [
                'eyebrow' => $text('certs_eyebrow'),
                'items'   => $text('certs_items'),
            ],
            'steps' => [
                'eyebrow' => $text('steps_eyebrow'),
                'heading' => $text('steps_heading'),
                'intro'   => $text('steps_intro'),
                'items'   => $stepItems,
            ],
            'blog' => [
                'eyebrow' => $text('blog_eyebrow'),
                'heading' => $text('blog_heading'),
            ],
            'faq' => [
                'eyebrow' => $text('faq_eyebrow'),
                'heading' => $text('faq_heading'),
                'items'   => $faqItems,
            ],
            'cta' => [
                'heading'      => $text('cta_heading'),
                'text'         => $text('cta_text'),
                'button_label' => $text('cta_button_label'),
                'button_url'   => $text('cta_button_url'),
            ],
        ];

        $lang = $request->input('lang') === 'en' ? 'en' : 'pl';
        HomeContent::save($content, $lang);

        Logger::record('update', 'home_content' . ($lang === 'en' ? '_en' : ''));
        Session::flash('saved', '1');
        Response::redirect($this->url() . ($lang === 'en' ? '?lang=en' : ''));
    }

    /**
     * Zbiera rownolegle tablice pol formularza (prefix_field[]) w liste
     * wierszy, pomijajac wiersze calkowicie puste (uzywane m.in. przez FAQ,
     * gdzie liczba pozycji jest zmienna).
     */
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
        return '/' . Config::get('admin_path') . '/settings/homepage';
    }
}
