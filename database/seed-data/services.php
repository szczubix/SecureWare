<?php

/**
 * Domyślna treść 13 usług SecureWare (Oferta). Edytowalna później w panelu
 * /cloudsecurepanel/services.
 */

return [
    [
        'name'              => 'Managed Backup',
        'slug'              => 'managed-backup',
        'icon'              => 'shield-check',
        'short_description' => 'Przejmujemy pełne zarządzanie Twoim istniejącym środowiskiem backupu - Veeam, Proxmox Backup Server i inne - abyś nie musiał go pilnować sam.',
        'content'           => '<p>Masz już wdrożony backup, ale brakuje Ci czasu albo kompetencji, żeby go na bieżąco nadzorować? Managed Backup to przejęcie przez nas codziennej opieki nad Twoim istniejącym środowiskiem - niezależnie czy działa na Veeam, Proxmox Backup Server, czy innym rozwiązaniu.</p><ul><li>Codzienna weryfikacja zadań backupowych i repozytoriów</li><li>Reagowanie na błędy i alarmy, zanim staną się problemem</li><li>Optymalizacja polityk retencji i wydajności</li><li>Comiesięczny raport stanu ochrony danych</li></ul><p>Efekt: backup, który po prostu działa, a Ty dostajesz jasny raport zamiast stresu.</p>',
    ],
    [
        'name'              => 'Backup as a Service',
        'slug'              => 'backup-as-a-service',
        'icon'              => 'cloud-upload',
        'short_description' => 'Instalujemy agenta w Twoim środowisku, a kopie zapasowe trafiają bezpiecznie do naszej infrastruktury - bez inwestycji we własny sprzęt.',
        'content'           => '<p>Backup as a Service (BaaS) to najszybsza droga do profesjonalnej ochrony danych bez budowania własnej infrastruktury backupowej. Wdrażamy lekkiego agenta w Twoim środowisku, a dane trafiają szyfrowanym kanałem do naszej infrastruktury.</p><ul><li>Zero inwestycji w sprzęt i licencje po stronie klienta</li><li>Skalowanie pojemności w miarę potrzeb</li><li>Szyfrowanie danych w tranzycie i w spoczynku</li><li>Rozliczenie w modelu abonamentowym</li></ul><p>Idealne rozwiązanie dla firm, które chcą mieć backup "od ręki", bez wielomiesięcznych wdrożeń.</p>',
    ],
    [
        'name'              => 'Off-site Backup',
        'slug'              => 'off-site-backup',
        'icon'              => 'map-pin',
        'short_description' => 'Druga kopia bezpieczeństwa przechowywana fizycznie poza siedzibą klienta - ochrona przed pożarem, kradzieżą i awarią lokalnej infrastruktury.',
        'content'           => '<p>Zasada 3-2-1 mówi jasno: co najmniej jedna kopia danych powinna znajdować się poza siedzibą firmy. Off-site Backup zapewnia dokładnie to - Twoje dane są replikowane do niezależnej lokalizacji, całkowicie odseparowanej od Twojej serwerowni.</p><ul><li>Ochrona przed pożarem, zalaniem, kradzieżą sprzętu</li><li>Niezależna lokalizacja geograficzna</li><li>Automatyczna, cykliczna replikacja</li><li>Możliwość szybkiego odtworzenia z lokalizacji zapasowej</li></ul>',
    ],
    [
        'name'              => 'Immutable Backup',
        'slug'              => 'immutable-backup',
        'icon'              => 'lock',
        'short_description' => 'Repozytorium kopii zapasowych zabezpieczone przed modyfikacją i usunięciem - realna ochrona przed ransomware, nawet gdy atakujący przejmie konto administratora.',
        'content'           => '<p>Współczesny ransomware celuje również w kopie zapasowe. Immutable Backup przechowuje dane w repozytorium, którego nie da się nadpisać ani usunąć przez określony czas - nawet z uprawnieniami administratora.</p><ul><li>Niezmienność danych (immutability) w oknie retencji</li><li>Ochrona przed atakami typu ransomware i insider threat</li><li>Zgodność z wymogami audytowymi i compliance</li><li>Współpraca z Veeam, PBS i innymi platformami backupu</li></ul><p>To ostatnia linia obrony, gdy wszystkie inne zabezpieczenia zawiodą.</p>',
    ],
    [
        'name'              => 'Microsoft 365 Backup',
        'slug'              => 'microsoft-365-backup',
        'icon'              => 'mail',
        'short_description' => 'Kopie zapasowe Exchange Online, OneDrive, SharePoint i Teams - bo Microsoft odpowiada za dostępność usługi, nie za odzyskanie Twoich danych.',
        'content'           => '<p>Wiele firm zakłada, że dane w Microsoft 365 są "bezpieczne w chmurze". Tymczasem Microsoft odpowiada za dostępność infrastruktury, a nie za przypadkowe usunięcie danych, błąd użytkownika czy atak na skrzynkę pocztową.</p><ul><li>Backup Exchange Online (poczta, kalendarze, kontakty)</li><li>Backup OneDrive i SharePoint</li><li>Backup zespołów i kanałów Microsoft Teams</li><li>Szybkie odtwarzanie pojedynczych elementów lub całych skrzynek</li></ul>',
    ],
    [
        'name'              => 'Server Backup',
        'slug'              => 'server-backup',
        'icon'              => 'server',
        'short_description' => 'Kopie zapasowe serwerów fizycznych Windows i Linux - pełne obrazy systemu oraz backup na poziomie plików i aplikacji.',
        'content'           => '<p>Zapewniamy kompleksową ochronę serwerów fizycznych działających pod Windows Server i systemami Linux - od pełnych obrazów systemu (bare-metal) po backup na poziomie plików i aplikacji (bazy danych, kontrolery domeny, serwery pocztowe).</p><ul><li>Backup pełnego systemu (bare-metal restore)</li><li>Backup aplikacyjny z uwzględnieniem spójności danych (VSS)</li><li>Wsparcie dla Windows Server i głównych dystrybucji Linux</li><li>Elastyczne harmonogramy i polityki retencji</li></ul>',
    ],
    [
        'name'              => 'Virtualization Backup',
        'slug'              => 'virtualization-backup',
        'icon'              => 'layers',
        'short_description' => 'Backup środowisk zwirtualizowanych - VMware vSphere, Microsoft Hyper-V oraz Proxmox VE - bez agentów instalowanych w każdej maszynie.',
        'content'           => '<p>Środowiska zwirtualizowane wymagają innego podejścia do backupu niż pojedyncze serwery. Zapewniamy backup na poziomie hypervisora dla VMware vSphere, Microsoft Hyper-V oraz Proxmox VE, bez konieczności instalowania agenta w każdej maszynie wirtualnej.</p><ul><li>Backup na poziomie hypervisora (image-based)</li><li>Wsparcie dla VMware, Hyper-V i Proxmox VE</li><li>Szybkie odtwarzanie całych maszyn wirtualnych</li><li>Minimalne obciążenie środowiska produkcyjnego</li></ul>',
    ],
    [
        'name'              => 'Disaster Recovery',
        'slug'              => 'disaster-recovery',
        'icon'              => 'life-buoy',
        'short_description' => 'Procedury i infrastruktura odtworzeniowa na wypadek poważnej awarii - od planu DR po gotowe środowisko zapasowe, które można uruchomić w minuty.',
        'content'           => '<p>Backup to nie to samo co Disaster Recovery. Backup pozwala odzyskać dane - DR pozwala odzyskać działanie firmy. Projektujemy i utrzymujemy procedury oraz infrastrukturę odtworzeniową dopasowaną do Twoich celów RTO i RPO.</p><ul><li>Opracowanie planu Disaster Recovery (DRP)</li><li>Środowisko zapasowe gotowe do szybkiego uruchomienia</li><li>Definiowanie i monitorowanie RTO/RPO</li><li>Regularne testy scenariuszy awaryjnych</li></ul>',
    ],
    [
        'name'              => 'Restore Testing',
        'slug'              => 'restore-testing',
        'icon'              => 'refresh-ccw',
        'short_description' => 'Cykliczne, rzeczywiste testy odtwarzania danych - bo kopia zapasowa, której nigdy nie sprawdzono, to tylko założenie, nie zabezpieczenie.',
        'content'           => '<p>Najczęstszym powodem, dla którego backup zawodzi w krytycznym momencie, jest brak testów odtwarzania. Regularnie wykonujemy rzeczywiste testy przywracania danych - nie tylko sprawdzenie statusu zadania backupu.</p><ul><li>Harmonogram cyklicznych testów odtwarzania</li><li>Testy w izolowanym środowisku (sandbox)</li><li>Raport z każdego testu wraz z rekomendacjami</li><li>Weryfikacja spójności i kompletności danych</li></ul>',
    ],
    [
        'name'              => 'Backup Audit',
        'slug'              => 'backup-audit',
        'icon'              => 'clipboard-check',
        'short_description' => 'Niezależna analiza obecnego środowiska backupu klienta - identyfikujemy luki, ryzyka i rekomendujemy konkretne poprawki.',
        'content'           => '<p>Zanim zaczniesz cokolwiek zmieniać, warto wiedzieć, gdzie faktycznie stoisz. Backup Audit to niezależny przegląd Twojego obecnego środowiska ochrony danych - konfiguracji, polityk retencji, pokrycia i realnej odporności na awarie.</p><ul><li>Przegląd konfiguracji i polityk backupu</li><li>Identyfikacja luk w pokryciu (systemy bez ochrony)</li><li>Ocena zgodności z zasadą 3-2-1</li><li>Raport z priorytetowymi rekomendacjami</li></ul>',
    ],
    [
        'name'              => 'Backup Implementation',
        'slug'              => 'backup-implementation',
        'icon'              => 'tool',
        'short_description' => 'Projektujemy i wdrażamy środowisko backupu od zera - od doboru architektury po pełne uruchomienie i przekazanie dokumentacji.',
        'content'           => '<p>Gdy w firmie nie ma jeszcze uporządkowanego backupu albo obecne rozwiązanie wymaga wymiany, projektujemy i wdrażamy środowisko od podstaw - dopasowane do skali, budżetu i wymagań bezpieczeństwa.</p><ul><li>Analiza potrzeb i dobór architektury backupu</li><li>Wdrożenie i konfiguracja wybranej platformy</li><li>Migracja z istniejącego rozwiązania (jeśli dotyczy)</li><li>Dokumentacja powdrożeniowa i szkolenie zespołu</li></ul>',
    ],
    [
        'name'              => 'Monitoring 24/7',
        'slug'              => 'monitoring-24-7',
        'icon'              => 'activity',
        'short_description' => 'Całodobowy nadzór nad zadaniami backupu, repozytoriami i pojemnością - alarmy trafiają do nas, zanim staną się Twoim problemem.',
        'content'           => '<p>Backup, którego nikt nie monitoruje, prędzej czy później zawiedzie w cichy sposób - jedno nieudane zadanie, którego nikt nie zauważy, może kosztować utratę danych. Nasz zespół monitoruje Twoje środowisko backupu 24 godziny na dobę, 7 dni w tygodniu.</p><ul><li>Całodobowy monitoring zadań backupowych</li><li>Alarmy o błędach i przekroczeniach pojemności repozytoriów</li><li>Proaktywna reakcja na incydenty</li><li>Panel statusu dostępny dla klienta</li></ul>',
    ],
    [
        'name'              => 'Retention & Compliance',
        'slug'              => 'retention-compliance',
        'icon'              => 'file-check',
        'short_description' => 'Polityki retencji danych, raportowanie i dokumentacja zgodna z wymogami audytowymi oraz regulacjami branżowymi.',
        'content'           => '<p>Właściwa retencja danych to nie tylko kwestia techniczna, ale również zgodności z regulacjami i wymogami audytowymi. Pomagamy zaprojektować i utrzymać polityki retencji, które spełniają wymagania prawne i branżowe.</p><ul><li>Projektowanie polityk retencji dopasowanych do wymagań</li><li>Raportowanie zgodności na potrzeby audytów</li><li>Dokumentacja procesów ochrony danych</li><li>Wsparcie przy audytach zewnętrznych</li></ul>',
    ],
    [
        'name'              => 'SIEM as a Service',
        'slug'              => 'siem-as-a-service',
        'icon'              => 'bug',
        'short_description' => 'Zbieramy i analizujemy logi z Twojej infrastruktury backupu i kluczowych systemów, żeby wykryć próbę ataku, zanim dojdzie do zaszyfrowania danych.',
        'content'           => '<p>Backup to ostatnia linia obrony - ale im wcześniej wykryjesz atak, tym mniej szkód wyrządzi, zanim w ogóle dojdzie do backupu. SIEM as a Service to zarządzana usługa zbierania i korelacji logów z Twojej infrastruktury (w tym środowiska backupu), która wykrywa podejrzaną aktywność - próby dostępu do repozytoriów, nietypowe wzorce logowania, oznaki ruchu bocznego (lateral movement) - i alarmuje Twój zespół, zanim atak się rozwinie.</p><ul><li>Zbieranie i korelacja logów z serwerów, backupu i kluczowych systemów</li><li>Reguły detekcji dopasowane do wzorców ataków na infrastrukturę backupu</li><li>Alarmowanie zespołu przy wykryciu podejrzanej aktywności</li><li>Miesięczny raport zdarzeń i rekomendacji</li></ul><p>Nie zastępujemy Twojego działu bezpieczeństwa - wzmacniamy widoczność tam, gdzie najczęściej atakuje ransomware: w warstwie backupu.</p>',
    ],
];
