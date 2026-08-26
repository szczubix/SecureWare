<?php

namespace SecureWare\Models;

/**
 * Cala tresc strony glownej (poza ofertami/artykulami, ktore maja wlasny
 * CMS) trzymana jako jeden blok JSON w ustawieniach (klucz "home_content"),
 * edytowalny w panelu admina bez zmian w kodzie. defaults() to oryginalna
 * tresc strony - uzywana jako wartosci domyslne i jako "wypelniacz" dla
 * pol, ktorych administrator jeszcze nie zapisal.
 */
class HomeContent
{
    public static function defaults(): array
    {
        return [
            'hero' => [
                'eyebrow'            => 'Backup & Disaster Recovery',
                'headline_pre'       => 'Backup, który ',
                'headline_highlight' => 'działa',
                'headline_post'      => ', gdy najbardziej go potrzebujesz',
                'lead'               => 'Zarządzany backup, ochrona przed ransomware i disaster recovery dla firm, które nie mogą sobie pozwolić na utratę danych. Monitorujemy, testujemy i raportujemy — 24/7.',
                'cta_primary_label'   => 'Umów bezpłatną konsultację',
                'cta_primary_url'     => '/kontakt',
                'cta_secondary_label' => 'Zobacz ofertę',
                'cta_secondary_url'   => '/oferta',
                'specs' => [
                    ['count' => 7, 'suffix' => ' lat', 'value' => '', 'label' => 'Doświadczenia w branży backupu'],
                    ['count' => null, 'suffix' => '', 'value' => '3-2-1-1-0', 'label' => 'Zasada ochrony danych'],
                    ['count' => null, 'suffix' => '', 'value' => 'Immutable', 'label' => 'Kopie odporne na ransomware'],
                    ['count' => null, 'suffix' => '', 'value' => '24/7', 'label' => 'Monitoring i reakcja'],
                ],
                'diagram_title' => 'Zasada 3-2-1-1-0 w praktyce',
                'diagram_badge' => 'Monitorowane 24/7',
                'diagram_foot'  => '0 błędów — każda kopia jest testowana i weryfikowana',
            ],
            'offer' => [
                'eyebrow'  => 'Nasza oferta',
                'heading'  => 'Pełen zakres ochrony danych',
                'intro'    => 'Od zarządzania istniejącym backupem po disaster recovery i cykliczne testy odtwarzania.',
                'cta_label' => 'Zobacz pełną ofertę (13 usług)',
            ],
            'stats' => [
                'items' => [
                    ['count' => 7, 'suffix' => ' lat', 'value' => '', 'label' => 'Doświadczenia w branży backupu'],
                    ['count' => null, 'suffix' => '', 'value' => '24/7', 'label' => 'Monitoring środowisk backupu'],
                    ['count' => null, 'suffix' => '', 'value' => '< 1h', 'label' => 'Docelowy czas reakcji na incydent'],
                    ['count' => 100, 'suffix' => '%', 'value' => '', 'label' => 'Testowane, nie zakładane'],
                ],
            ],
            'platform' => [
                'eyebrow' => 'Jak działamy',
                'heading' => 'Trzy filary pełnej ochrony danych',
                'intro'   => 'Backup, disaster recovery i monitoring — na tym opieramy każde wdrożenie, od pierwszej kopii po pełne disaster recovery.',
                'tabs' => [
                    [
                        'icon' => 'cloud-upload', 'title' => 'Backup i ochrona', 'subtitle' => 'Kopie niezmienne, zgodne z 3-2-1-1-0',
                        'panel_title' => 'Backup, który przetrwa atak',
                        'panel_text'  => 'Kopie w repozytorium niezmiennym (immutable), zgodne z zasadą 3-2-1-1-0 - dane pozostają odzyskiwalne nawet po przejęciu konta administratora.',
                        'bullets' => "Codzienne, automatyczne kopie bez ingerencji Twojego zespołu IT\nWsparcie dla narzędzi, które już masz (np. Veeam, Proxmox Backup Server)\nRepozytoria immutable odporne na ransomware",
                    ],
                    [
                        'icon' => 'life-buoy', 'title' => 'Disaster Recovery', 'subtitle' => 'Procedury i cele RTO/RPO',
                        'panel_title' => 'Disaster Recovery zaplanowany, nie improwizowany',
                        'panel_text'  => 'Ustalamy z Tobą realne cele RTO/RPO i budujemy procedury, dzięki którym w razie awarii wiadomo dokładnie, co robić - krok po kroku.',
                        'bullets' => "Zdefiniowane cele czasu i punktu przywrócenia (RTO/RPO)\nInfrastruktura zapasowa gotowa do szybkiego przełączenia\nSpisana procedura awaryjna zamiast działania na pamięć",
                    ],
                    [
                        'icon' => 'activity', 'title' => 'Monitoring i zgodność', 'subtitle' => 'Nadzór 24/7 i raporty',
                        'panel_title' => 'Nadzór, który nie śpi',
                        'panel_text'  => 'Środowisko backupu jest monitorowane całodobowo - reagujemy, zanim niepowodzenie kopii stanie się utratą danych.',
                        'bullets' => "Monitoring zadań backupu i repozytoriów 24/7\nRegularne, realne testy odtwarzania z raportem\nPolityki retencji zgodne z wymaganiami compliance",
                    ],
                ],
            ],
            'rule' => [
                'eyebrow' => 'Standard branżowy',
                'heading' => 'Zasada 3-2-1-1-0',
                'intro'   => 'Rozszerzenie klasycznej zasady 3-2-1 do 3-2-1-1-0, o ochronę przed ransomware i obowiązek regularnej weryfikacji kopii. Kliknij element, żeby zobaczyć szczegóły.',
                'items' => [
                    ['icon' => 'layers', 'num' => '3', 'label' => 'Kopie danych', 'text' => 'Zawsze co najmniej trzy kopie: dane produkcyjne oraz dwie kopie zapasowe. Nawet jeśli jedna zawiedzie, pozostałe pozwalają odzyskać dane.'],
                    ['icon' => 'server', 'num' => '2', 'label' => 'Rodzaje nośników', 'text' => 'Kopie przechowywane na dwóch różnych typach nośników (np. lokalny storage i chmura) - awaria jednego typu nośnika nie unieważnia wszystkich kopii naraz.'],
                    ['icon' => 'cloud-upload', 'num' => '1', 'label' => 'Kopia offsite', 'text' => 'Co najmniej jedna kopia poza siedzibą firmy. Chroni dane przed zdarzeniami, które mogą zniszczyć całą lokalną infrastrukturę - pożarem, zalaniem, kradzieżą sprzętu.'],
                    ['icon' => 'lock', 'num' => '1', 'label' => 'Offline / immutable', 'text' => 'Dodatkowa kopia odizolowana od sieci lub niezmienna (immutable) - odporna na ransomware, który celuje właśnie w systemy backupu, żeby odciąć drogę do odzyskania danych.'],
                    ['icon' => 'shield-check', 'num' => '0', 'label' => 'Błędów w kopiach', 'text' => 'Kopie regularnie testowane i weryfikowane przez realne odtwarzanie danych - zero niespodzianek w momencie, w którym backup trzeba faktycznie użyć.'],
                ],
            ],
            'ransomware' => [
                'eyebrow'         => 'Dlaczego 3-2-1-1-0 działa',
                'heading'         => 'Ransomware zjada, co może — ale nie kopię immutable',
                'intro'           => 'Zaszyfrowanie danych produkcyjnych i zwykłej kopii zapasowej to standardowy scenariusz ataku. Kopia niezmienna (immutable) zostaje nietknięta, bo z definicji nie da się jej zmodyfikować ani usunąć — nawet z przejętym kontem administratora.',
                'protected_label' => 'Chronione — nie do zmodyfikowania',
            ],
            'scenario' => [
                'eyebrow' => 'Dwa scenariusze ataku',
                'heading' => 'Okup albo przywrócenie danych - w kilka godzin',
                'intro'   => 'To samo zdarzenie, dwa zupełnie różne poranki - w zależności od tego, czy kopia immutable w ogóle istnieje.',
                'threat_badge'    => 'Bez kopii immutable',
                'threat_lines'    => "Twoje dane zostały zaszyfrowane.\nKopie zapasowe również.\nZapłać, aby odzyskać dostęp:",
                'threat_amount'   => 1000000,
                'threat_suffix'   => ' zł',
                'threat_deadline' => 'Termin: 48 godzin, potem cena rośnie.',
                'safe_badge'     => 'Z kopią immutable SecureWare',
                'safe_intro'     => 'Atak wykryty. Dane produkcyjne zaszyfrowane.',
                'safe_checklist' => "Kopia immutable: nienaruszona\nPrzywracanie danych: rozpoczęte\nOkup: nie zapłacony",
                'safe_result'    => 'Przywrócono z kopii immutable. Zero złotych okupu.',
            ],
            'why' => [
                'eyebrow'    => 'Dlaczego SecureWare',
                'heading'    => 'Backup, któremu można zaufać',
                'intro'      => 'Nie sprzedajemy licencji i nie znikamy po wdrożeniu — zarządzamy Twoim backupem tak, jakby był naszym własnym.',
                'link_label' => 'Porozmawiajmy o Twoim środowisku',
                'items' => [
                    ['title' => 'Ochrona przed ransomware', 'text' => 'Kopie niezmienne i segmentacja infrastruktury backupu.'],
                    ['title' => 'Rzeczywiste testy', 'text' => 'Nie sprawdzamy tylko statusu zadania - realnie odtwarzamy dane.'],
                    ['title' => 'Nadzór 24/7', 'text' => 'Reagujemy, zanim problem stanie się awarią.'],
                    ['title' => 'Jasne raporty', 'text' => 'Zrozumiałe raporty również dla osób spoza IT.'],
                ],
            ],
            'steps' => [
                'eyebrow' => 'Jak to działa',
                'heading' => 'Wdrożenie krok po kroku',
                'intro'   => 'Bez wielomiesięcznych projektów - od pierwszej rozmowy do działającej ochrony danych.',
                'items' => [
                    ['title' => 'Audyt i konsultacja', 'text' => 'Analizujemy obecne środowisko, wymagania RTO/RPO i budżet, aby zaproponować rozwiązanie dopasowane do skali firmy.'],
                    ['title' => 'Wdrożenie', 'text' => 'Konfigurujemy backup, repozytoria i polityki retencji - dla nowego środowiska lub w oparciu o narzędzia, które już posiadasz.'],
                    ['title' => 'Monitoring i testy', 'text' => 'Nadzorujemy środowisko 24/7 i regularnie testujemy rzeczywiste odtwarzanie danych - z raportem po każdym teście.'],
                ],
            ],
            'blog' => [
                'eyebrow' => 'Z bloga',
                'heading' => 'Najnowsze artykuły',
            ],
            'faq' => [
                'eyebrow' => 'Pytania',
                'heading' => 'Najczęściej zadawane pytania',
                'items' => [
                    ['question' => 'Czym różni się backup od disaster recovery?', 'answer' => 'Backup pozwala odzyskać dane. Disaster recovery pozwala odzyskać działanie firmy - obejmuje procedury, infrastrukturę zapasową oraz zdefiniowane cele RTO/RPO, dzięki którym wiadomo, jak szybko i z jaką stratą danych systemy wrócą do pracy.'],
                    ['question' => 'Czy mogę zachować obecne oprogramowanie do backupu?', 'answer' => 'Tak. W ramach Managed Backup przejmujemy nadzór nad środowiskiem, które już masz (np. Veeam, Proxmox Backup Server). Migracja na nową platformę jest opcjonalna, nie warunkiem współpracy.'],
                    ['question' => 'Ile trwa wdrożenie?', 'answer' => 'Zależy od skali środowiska - prosty Backup as a Service można uruchomić w ciągu kilku dni, pełne wdrożenie z disaster recovery i testami odtwarzania zwykle zajmuje kilka tygodni.'],
                    ['question' => 'Co dzieje się w razie ataku ransomware?', 'answer' => 'Kopie w repozytorium niezmiennym (immutable) pozostają nienaruszone nawet po przejęciu konta administratora, co pozwala odtworzyć dane bez płacenia okupu. Reagujemy w ramach procedury disaster recovery ustalonej wcześniej z Tobą.'],
                    ['question' => 'Czy oferujecie bezpłatną konsultację?', 'answer' => 'Tak - pierwsza rozmowa i wstępny przegląd obecnego środowiska backupu są bezpłatne. Umów ją przez formularz kontaktowy.'],
                ],
            ],
            'cta' => [
                'heading'      => 'Nie wiesz, czy Twój backup naprawdę zadziała?',
                'text'         => 'Zamów bezpłatny audyt obecnego środowiska ochrony danych.',
                'button_label' => 'Zamów audyt',
                'button_url'   => '/kontakt',
            ],
        ];
    }

    public static function current(): array
    {
        $raw = Setting::get('home_content', '');
        $saved = $raw ? json_decode((string) $raw, true) : null;
        if (!is_array($saved)) {
            $saved = [];
        }

        return self::mergeDeep(self::defaults(), $saved);
    }

    public static function save(array $content): void
    {
        Setting::set('home_content', json_encode($content, JSON_UNESCAPED_UNICODE));
    }

    /**
     * Nakłada zapisane wartości na domyślne, rekurencyjnie - dzięki temu
     * brakujące pola (np. dodane w nowej wersji kodu) zawsze mają sensowną
     * wartość domyślną, a listy (specs/items/tabs...) są całkowicie
     * podmieniane zapisaną wersją, jeśli administrator ją zapisał.
     */
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
