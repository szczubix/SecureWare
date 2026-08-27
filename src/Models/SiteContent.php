<?php

namespace SecureWare\Models;

/**
 * Tresc marketingowa podstron innych niz strona glowna (oferta, blog,
 * kontakt, 404) - ten sam mechanizm co HomeContent: jeden blok JSON w
 * ustawieniach (klucz "site_page_content" lub "site_page_content_en"),
 * edytowalny w panelu admina.
 */
class SiteContent
{
    public static function defaults(string $locale = 'pl'): array
    {
        return $locale === 'en' ? self::defaultsEn() : self::defaultsPl();
    }

    private static function defaultsPl(): array
    {
        return [
            'offer' => [
                'eyebrow'           => 'Oferta',
                'heading_pre'       => 'Pełen zakres ochrony ',
                'heading_highlight' => 'danych',
                'heading_post'      => ' dla firm',
                'lead'              => '14 usług pokrywających cały cykl życia backupu — od wdrożenia, przez codzienne zarządzanie, po disaster recovery i testy odtwarzania.',
                'highlights' => [
                    ['icon' => 'shield-check', 'text' => 'Kopie niezmienne (immutable)'],
                    ['icon' => 'refresh-ccw', 'text' => 'Realne testy odtwarzania'],
                    ['icon' => 'activity', 'text' => 'Monitoring 24/7'],
                    ['icon' => 'file-check', 'text' => 'Jasne raporty SLA'],
                ],
                'empty_text'       => 'Oferta jest aktualnie aktualizowana.',
                'cta_heading'      => 'Nie wiesz, która usługa jest dla Ciebie?',
                'cta_text'         => 'Porozmawiajmy — dobierzemy rozwiązanie do skali i budżetu Twojej firmy.',
                'cta_button_label' => 'Skontaktuj się',
            ],
            'blog' => [
                'eyebrow'           => 'Blog',
                'heading_pre'       => 'Backup, ransomware i ',
                'heading_highlight' => 'disaster recovery',
                'heading_post'      => ' po ludzku',
                'lead'              => 'Praktyczna wiedza o ochronie danych - bez marketingowego żargonu.',
            ],
            'contact' => [
                'eyebrow'           => 'Kontakt',
                'heading_pre'       => 'Porozmawiajmy o ',
                'heading_highlight' => 'ochronie Twoich danych',
                'heading_post'      => '',
                'lead'              => 'Wypełnij formularz - odpowiadamy zazwyczaj w ciągu jednego dnia roboczego.',
                'info_heading'      => 'Dane kontaktowe',
                'info_text'         => 'Chętnie odpowiemy na pytania dotyczące backupu, disaster recovery lub audytu obecnego środowiska.',
                'success_message'   => 'Dziękujemy! Twoja wiadomość została wysłana - odpowiemy najszybciej jak to możliwe.',
                'submit_label'      => 'Wyślij wiadomość',
            ],
            'not_found' => [
                'heading'       => '404',
                'text'          => 'Nie znaleziono szukanej strony — możliwe, że została przeniesiona albo usunięta.',
                'primary_label' => 'Wróć na stronę główną',
            ],
        ];
    }

    private static function defaultsEn(): array
    {
        return [
            'offer' => [
                'eyebrow'           => 'Services',
                'heading_pre'       => 'Full-scope data ',
                'heading_highlight' => 'protection',
                'heading_post'      => ' for businesses',
                'lead'              => '14 services covering the entire backup lifecycle — from deployment, through day-to-day management, to disaster recovery and restore testing.',
                'highlights' => [
                    ['icon' => 'shield-check', 'text' => 'Immutable copies'],
                    ['icon' => 'refresh-ccw', 'text' => 'Real restore tests'],
                    ['icon' => 'activity', 'text' => '24/7 monitoring'],
                    ['icon' => 'file-check', 'text' => 'Clear SLA reports'],
                ],
                'empty_text'       => 'Our service list is currently being updated.',
                'cta_heading'      => 'Not sure which service fits you?',
                'cta_text'         => 'Let\'s talk — we\'ll match a solution to your company\'s scale and budget.',
                'cta_button_label' => 'Get in touch',
            ],
            'blog' => [
                'eyebrow'           => 'Blog',
                'heading_pre'       => 'Backup, ransomware, and ',
                'heading_highlight' => 'disaster recovery',
                'heading_post'      => ' in plain terms',
                'lead'              => 'Practical knowledge about data protection - no marketing jargon.',
            ],
            'contact' => [
                'eyebrow'           => 'Contact',
                'heading_pre'       => 'Let\'s talk about ',
                'heading_highlight' => 'protecting your data',
                'heading_post'      => '',
                'lead'              => 'Fill in the form - we usually reply within one business day.',
                'info_heading'      => 'Contact details',
                'info_text'         => 'We\'re happy to answer questions about backup, disaster recovery, or an audit of your current environment.',
                'success_message'   => 'Thank you! Your message has been sent - we\'ll get back to you as soon as possible.',
                'submit_label'      => 'Send message',
            ],
            'not_found' => [
                'heading'       => '404',
                'text'          => 'The page you were looking for could not be found — it may have been moved or removed.',
                'primary_label' => 'Back to homepage',
            ],
        ];
    }

    public static function current(string $locale = 'pl'): array
    {
        $key = $locale === 'en' ? 'site_page_content_en' : 'site_page_content';
        $raw = Setting::get($key, '');
        $saved = $raw ? json_decode((string) $raw, true) : null;
        if (!is_array($saved)) {
            $saved = [];
        }

        return self::mergeDeep(self::defaults($locale), $saved);
    }

    public static function save(array $content, string $locale = 'pl'): void
    {
        $key = $locale === 'en' ? 'site_page_content_en' : 'site_page_content';
        Setting::set($key, json_encode($content, JSON_UNESCAPED_UNICODE));
    }

    private static function mergeDeep(array $defaults, array $saved): array
    {
        foreach ($saved as $key => $value) {
            if (is_array($value) && isset($defaults[$key]) && is_array($defaults[$key]) && !array_is_list($value)) {
                $defaults[$key] = self::mergeDeep($defaults[$key], $value);
            } else {
                $defaults[$key] = $value;
            }
        }

        return $defaults;
    }
}
