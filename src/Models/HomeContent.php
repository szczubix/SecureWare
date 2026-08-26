<?php

namespace SecureWare\Models;

/**
 * Cala tresc strony glownej (poza ofertami/artykulami, ktore maja wlasny
 * CMS) trzymana jako jeden blok JSON w ustawieniach (klucz "home_content",
 * lub "home_content_en" dla wersji angielskiej), edytowalny w panelu admina
 * bez zmian w kodzie. defaults() to oryginalna tresc strony - uzywana jako
 * wartosci domyslne i jako "wypelniacz" dla pol, ktorych administrator
 * jeszcze nie zapisal (osobno dla kazdego jezyka).
 */
class HomeContent
{
    public static function defaults(string $locale = 'pl'): array
    {
        return $locale === 'en' ? self::defaultsEn() : self::defaultsPl();
    }

    private static function defaultsPl(): array
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
            'stack' => [
                'eyebrow' => 'Integrujemy się z Twoim środowiskiem',
                'items'   => "Veeam\nProxmox Backup Server\nMicrosoft 365\nVMware\nHyper-V",
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
            'certs' => [
                'eyebrow' => 'Kompetencje potwierdzone certyfikatami',
                'items'   => "Certified Ethical Hacker (CEH)\ncPanel/WHM Certified Professional\nLFCS - Linux Foundation Certified System Administrator\nITIL Foundation",
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

    private static function defaultsEn(): array
    {
        return [
            'hero' => [
                'eyebrow'            => 'Backup & Disaster Recovery',
                'headline_pre'       => 'Backup that ',
                'headline_highlight' => 'works',
                'headline_post'      => ' when you need it most',
                'lead'               => 'Managed backup, ransomware protection, and disaster recovery for companies that cannot afford to lose data. We monitor, test, and report — 24/7.',
                'cta_primary_label'   => 'Book a free consultation',
                'cta_primary_url'     => '/kontakt',
                'cta_secondary_label' => 'See our services',
                'cta_secondary_url'   => '/oferta',
                'specs' => [
                    ['count' => 7, 'suffix' => ' years', 'value' => '', 'label' => 'Of experience in backup'],
                    ['count' => null, 'suffix' => '', 'value' => '3-2-1-1-0', 'label' => 'Data protection rule'],
                    ['count' => null, 'suffix' => '', 'value' => 'Immutable', 'label' => 'Copies resistant to ransomware'],
                    ['count' => null, 'suffix' => '', 'value' => '24/7', 'label' => 'Monitoring and response'],
                ],
                'diagram_title' => 'The 3-2-1-1-0 rule in practice',
                'diagram_badge' => 'Monitored 24/7',
                'diagram_foot'  => '0 errors — every copy is tested and verified',
            ],
            'offer' => [
                'eyebrow'  => 'Our services',
                'heading'  => 'Full-scope data protection',
                'intro'    => 'From managing your existing backup to disaster recovery and recurring restore tests.',
                'cta_label' => 'See the full range (13 services)',
            ],
            'stack' => [
                'eyebrow' => 'Integrates with the environment you already run',
                'items'   => "Veeam\nProxmox Backup Server\nMicrosoft 365\nVMware\nHyper-V",
            ],
            'stats' => [
                'items' => [
                    ['count' => 7, 'suffix' => ' years', 'value' => '', 'label' => 'Of experience in backup'],
                    ['count' => null, 'suffix' => '', 'value' => '24/7', 'label' => 'Backup environment monitoring'],
                    ['count' => null, 'suffix' => '', 'value' => '< 1h', 'label' => 'Target incident response time'],
                    ['count' => 100, 'suffix' => '%', 'value' => '', 'label' => 'Tested, not assumed'],
                ],
            ],
            'platform' => [
                'eyebrow' => 'How we work',
                'heading' => 'Three pillars of full data protection',
                'intro'   => 'Backup, disaster recovery, and monitoring — the foundation of every deployment, from the first backup to full disaster recovery.',
                'tabs' => [
                    [
                        'icon' => 'cloud-upload', 'title' => 'Backup & protection', 'subtitle' => 'Immutable copies, 3-2-1-1-0 compliant',
                        'panel_title' => 'Backup that survives an attack',
                        'panel_text'  => 'Copies in an immutable repository, compliant with the 3-2-1-1-0 rule - data stays recoverable even after an administrator account is compromised.',
                        'bullets' => "Daily, automatic backups with no involvement from your IT team\nSupport for the tools you already have (e.g. Veeam, Proxmox Backup Server)\nImmutable repositories resistant to ransomware",
                    ],
                    [
                        'icon' => 'life-buoy', 'title' => 'Disaster Recovery', 'subtitle' => 'RTO/RPO procedures and targets',
                        'panel_title' => 'Disaster recovery that is planned, not improvised',
                        'panel_text'  => 'We agree on realistic RTO/RPO targets with you and build procedures so that, in the event of an outage, everyone knows exactly what to do - step by step.',
                        'bullets' => "Defined recovery time and recovery point objectives (RTO/RPO)\nStandby infrastructure ready for a fast failover\nA written incident procedure instead of relying on memory",
                    ],
                    [
                        'icon' => 'activity', 'title' => 'Monitoring & compliance', 'subtitle' => '24/7 oversight and reporting',
                        'panel_title' => 'Oversight that never sleeps',
                        'panel_text'  => 'Your backup environment is monitored around the clock - we react before a failed backup turns into data loss.',
                        'bullets' => "24/7 monitoring of backup jobs and repositories\nRegular, real restore tests with a report\nRetention policies aligned with compliance requirements",
                    ],
                ],
            ],
            'rule' => [
                'eyebrow' => 'Industry standard',
                'heading' => 'The 3-2-1-1-0 rule',
                'intro'   => 'An extension of the classic 3-2-1 rule to 3-2-1-1-0, adding ransomware protection and mandatory, regular verification of backups. Click an item to see the details.',
                'items' => [
                    ['icon' => 'layers', 'num' => '3', 'label' => 'Copies of data', 'text' => 'Always at least three copies: production data plus two backup copies. Even if one fails, the others let you recover the data.'],
                    ['icon' => 'server', 'num' => '2', 'label' => 'Types of media', 'text' => 'Copies stored on two different types of media (e.g. local storage and the cloud) - a failure of one media type doesn\'t invalidate all copies at once.'],
                    ['icon' => 'cloud-upload', 'num' => '1', 'label' => 'Off-site copy', 'text' => 'At least one copy kept off-site. Protects data against events that could destroy your entire local infrastructure - fire, flooding, theft of equipment.'],
                    ['icon' => 'lock', 'num' => '1', 'label' => 'Offline / immutable', 'text' => 'An additional copy isolated from the network or immutable - resistant to ransomware, which specifically targets backup systems to cut off the path to recovery.'],
                    ['icon' => 'shield-check', 'num' => '0', 'label' => 'Errors in backups', 'text' => 'Copies are regularly tested and verified through real data restores - zero surprises the moment a backup actually needs to be used.'],
                ],
            ],
            'ransomware' => [
                'eyebrow'         => 'Why 3-2-1-1-0 works',
                'heading'         => 'Ransomware eats what it can — but not the immutable copy',
                'intro'           => 'Encrypting production data and a regular backup copy is a standard attack scenario. The immutable copy stays untouched, because by definition it cannot be modified or deleted — not even with a compromised administrator account.',
                'protected_label' => 'Protected — cannot be modified',
            ],
            'scenario' => [
                'eyebrow' => 'Two attack scenarios',
                'heading' => 'Ransom, or restored data in a few hours',
                'intro'   => 'The same incident, two completely different mornings - depending on whether an immutable copy even exists.',
                'threat_badge'    => 'Without an immutable copy',
                'threat_lines'    => "Your data has been encrypted.\nSo have your backups.\nPay to regain access:",
                'threat_amount'   => 1000000,
                'threat_suffix'   => ' PLN',
                'threat_deadline' => 'Deadline: 48 hours, then the price goes up.',
                'safe_badge'     => 'With a SecureWare immutable copy',
                'safe_intro'     => 'Attack detected. Production data encrypted.',
                'safe_checklist' => "Immutable copy: intact\nData restore: in progress\nRansom: not paid",
                'safe_result'    => 'Restored from the immutable copy. Zero ransom paid.',
            ],
            'why' => [
                'eyebrow'    => 'Why SecureWare',
                'heading'    => 'Backup you can trust',
                'intro'      => 'We don\'t sell licenses and disappear after deployment — we manage your backup as if it were our own.',
                'link_label' => 'Let\'s talk about your environment',
                'items' => [
                    ['title' => 'Ransomware protection', 'text' => 'Immutable copies and segmented backup infrastructure.'],
                    ['title' => 'Real tests', 'text' => 'We don\'t just check a job\'s status - we actually restore the data.'],
                    ['title' => '24/7 oversight', 'text' => 'We react before a problem becomes an outage.'],
                    ['title' => 'Clear reports', 'text' => 'Reports that make sense even outside of IT.'],
                ],
            ],
            'certs' => [
                'eyebrow' => 'Skills backed by certification',
                'items'   => "Certified Ethical Hacker (CEH)\ncPanel/WHM Certified Professional\nLFCS - Linux Foundation Certified System Administrator\nITIL Foundation",
            ],
            'steps' => [
                'eyebrow' => 'How it works',
                'heading' => 'Deployment, step by step',
                'intro'   => 'No months-long projects - from the first conversation to working data protection.',
                'items' => [
                    ['title' => 'Audit & consultation', 'text' => 'We analyze your current environment, RTO/RPO requirements, and budget to propose a solution that fits the scale of your company.'],
                    ['title' => 'Deployment', 'text' => 'We configure backup, repositories, and retention policies - for a new environment or on top of the tools you already have.'],
                    ['title' => 'Monitoring & testing', 'text' => 'We monitor the environment 24/7 and regularly test real data restores - with a report after every test.'],
                ],
            ],
            'blog' => [
                'eyebrow' => 'From the blog',
                'heading' => 'Latest articles',
            ],
            'faq' => [
                'eyebrow' => 'Questions',
                'heading' => 'Frequently asked questions',
                'items' => [
                    ['question' => 'What\'s the difference between backup and disaster recovery?', 'answer' => 'Backup lets you recover data. Disaster recovery lets you recover your business operations - it covers procedures, standby infrastructure, and defined RTO/RPO targets that tell you how fast, and with how much data loss, your systems will be back up.'],
                    ['question' => 'Can I keep my current backup software?', 'answer' => 'Yes. Under Managed Backup, we take over oversight of the environment you already have (e.g. Veeam, Proxmox Backup Server). Migrating to a new platform is optional, not a condition of working with us.'],
                    ['question' => 'How long does deployment take?', 'answer' => 'It depends on the scale of the environment - a simple Backup as a Service can be up and running in a few days, while a full deployment with disaster recovery and restore testing usually takes a few weeks.'],
                    ['question' => 'What happens in a ransomware attack?', 'answer' => 'Copies in an immutable repository stay intact even after an administrator account is compromised, letting you restore data without paying a ransom. We respond under the disaster recovery procedure we agreed with you in advance.'],
                    ['question' => 'Do you offer a free consultation?', 'answer' => 'Yes - the first call and an initial review of your current backup environment are free. Book it through the contact form.'],
                ],
            ],
            'cta' => [
                'heading'      => 'Not sure your backup would actually work?',
                'text'         => 'Order a free audit of your current data protection environment.',
                'button_label' => 'Order an audit',
                'button_url'   => '/kontakt',
            ],
        ];
    }

    public static function current(string $locale = 'pl'): array
    {
        $key = $locale === 'en' ? 'home_content_en' : 'home_content';
        $raw = Setting::get($key, '');
        $saved = $raw ? json_decode((string) $raw, true) : null;
        if (!is_array($saved)) {
            $saved = [];
        }

        return self::mergeDeep(self::defaults($locale), $saved);
    }

    public static function save(array $content, string $locale = 'pl'): void
    {
        $key = $locale === 'en' ? 'home_content_en' : 'home_content';
        Setting::set($key, json_encode($content, JSON_UNESCAPED_UNICODE));
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
