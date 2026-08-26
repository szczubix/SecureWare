<?php

namespace SecureWare\Models;

/**
 * Tresc marketingowa podstron innych niz strona glowna (oferta, blog,
 * kontakt, 404) - ten sam mechanizm co HomeContent: jeden blok JSON w
 * ustawieniach (klucz "site_page_content"), edytowalny w panelu admina.
 */
class SiteContent
{
    public static function defaults(): array
    {
        return [
            'offer' => [
                'eyebrow'           => 'Oferta',
                'heading_pre'       => 'Pełen zakres ochrony ',
                'heading_highlight' => 'danych',
                'heading_post'      => ' dla firm',
                'lead'              => '13 usług pokrywających cały cykl życia backupu — od wdrożenia, przez codzienne zarządzanie, po disaster recovery i testy odtwarzania.',
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

    public static function current(): array
    {
        $raw = Setting::get('site_page_content', '');
        $saved = $raw ? json_decode((string) $raw, true) : null;
        if (!is_array($saved)) {
            $saved = [];
        }

        return self::mergeDeep(self::defaults(), $saved);
    }

    public static function save(array $content): void
    {
        Setting::set('site_page_content', json_encode($content, JSON_UNESCAPED_UNICODE));
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
