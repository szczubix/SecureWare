<?php

/**
 * Domyslna tresc 13 uslug SecureWare (Oferta). Edytowalna pozniej w panelu
 * /cloudsecurepanel/services.
 */

return [
    [
        'name'              => 'Managed Backup',
        'slug'              => 'managed-backup',
        'icon'              => 'shield-check',
        'short_description' => 'Przejmujemy pelne zarzadzanie Twoim istniejacym srodowiskiem backupu - Veeam, Proxmox Backup Server i inne - abys nie musial go pilnowac sam.',
        'content'           => '<p>Masz juz wdrozony backup, ale brakuje Ci czasu albo kompetencji, zeby go na biezaco nadzorowac? Managed Backup to przejecie przez nas codziennej opieki nad Twoim istniejacym srodowiskiem - niezaleznie czy dziala na Veeam, Proxmox Backup Server, czy innym rozwiazaniu.</p><ul><li>Codzienna weryfikacja zadan backupowych i repozytoriow</li><li>Reagowanie na bledy i alarmy zanim staną sie problemem</li><li>Optymalizacja polityk retencji i wydajnosci</li><li>Comiesieczny raport stanu ochrony danych</li></ul><p>Efekt: backup, ktory po prostu dziala, a Ty dostajesz jasny raport zamiast stresu.</p>',
    ],
    [
        'name'              => 'Backup as a Service',
        'slug'              => 'backup-as-a-service',
        'icon'              => 'cloud-upload',
        'short_description' => 'Instalujemy agenta w Twoim srodowisku, a kopie zapasowe trafiaja bezpiecznie do naszej infrastruktury - bez inwestycji we wlasny sprzet.',
        'content'           => '<p>Backup as a Service (BaaS) to najszybsza droga do profesjonalnej ochrony danych bez budowania wlasnej infrastruktury backupowej. Wdrazamy lekkiego agenta w Twoim srodowisku, a dane trafiaja szyfrowanym kanalem do naszej infrastruktury.</p><ul><li>Zero inwestycji w sprzet i licencje po stronie klienta</li><li>Skalowanie pojemnosci w miare potrzeb</li><li>Szyfrowanie danych w tranzycie i w spoczynku</li><li>Rozliczenie w modelu abonamentowym</li></ul><p>Idealne rozwiazanie dla firm, ktore chca miec backup "od reki", bez wielomiesiecznych wdrozen.</p>',
    ],
    [
        'name'              => 'Off-site Backup',
        'slug'              => 'off-site-backup',
        'icon'              => 'map-pin',
        'short_description' => 'Druga kopia bezpieczenstwa przechowywana fizycznie poza siedziba klienta - ochrona przed pozarem, kradzieza i awaria lokalnej infrastruktury.',
        'content'           => '<p>Zasada 3-2-1 mowi jasno: co najmniej jedna kopia danych powinna znajdowac sie poza siedziba firmy. Off-site Backup zapewnia dokladnie to - Twoje dane sa replikowane do niezaleznej lokalizacji, calkowicie odseparowanej od Twojej serwerowni.</p><ul><li>Ochrona przed pozarem, zalaniem, kradzieza sprzetu</li><li>Niezalezna lokalizacja geograficzna</li><li>Automatyczna, cykliczna replikacja</li><li>Mozliwosc szybkiego odtworzenia z lokalizacji zapasowej</li></ul>',
    ],
    [
        'name'              => 'Immutable Backup',
        'slug'              => 'immutable-backup',
        'icon'              => 'lock',
        'short_description' => 'Repozytorium kopii zapasowych zabezpieczone przed modyfikacja i usunieciem - realna ochrona przed ransomware, nawet gdy atakujacy przejmie konto administratora.',
        'content'           => '<p>Wspolczesny ransomware celuje rowniez w kopie zapasowe. Immutable Backup przechowuje dane w repozytorium, ktorego nie da sie nadpisac ani usunac przez okreslony czas - nawet z uprawnieniami administratora.</p><ul><li>Niezmiennosc danych (immutability) w oknie retencji</li><li>Ochrona przed atakami typu ransomware i insider threat</li><li>Zgodnosc z wymogami audytowymi i compliance</li><li>Wspolpraca z Veeam, PBS i innymi platformami backupu</li></ul><p>To ostatnia linia obrony, gdy wszystkie inne zabezpieczenia zawioda.</p>',
    ],
    [
        'name'              => 'Microsoft 365 Backup',
        'slug'              => 'microsoft-365-backup',
        'icon'              => 'mail',
        'short_description' => 'Kopie zapasowe Exchange Online, OneDrive, SharePoint i Teams - bo Microsoft odpowiada za dostepnosc uslugi, nie za odzyskanie Twoich danych.',
        'content'           => '<p>Wiele firm zaklada, ze dane w Microsoft 365 sa "bezpieczne w chmurze". Tymczasem Microsoft odpowiada za dostepnosc infrastruktury, a nie za przypadkowe usuniecie danych, blad uzytkownika czy atak na skrzynke pocztowa.</p><ul><li>Backup Exchange Online (poczta, kalendarze, kontakty)</li><li>Backup OneDrive i SharePoint</li><li>Backup zespolow i kanalow Microsoft Teams</li><li>Szybkie odtwarzanie pojedynczych elementow lub calych skrzynek</li></ul>',
    ],
    [
        'name'              => 'Server Backup',
        'slug'              => 'server-backup',
        'icon'              => 'server',
        'short_description' => 'Kopie zapasowe serwerow fizycznych Windows i Linux - pelne obrazy systemu oraz backup na poziomie plikow i aplikacji.',
        'content'           => '<p>Zapewniamy kompleksowa ochrone serwerow fizycznych dzialajacych pod Windows Server i systemami Linux - od pelnych obrazow systemu (bare-metal) po backup na poziomie plikow i aplikacji (bazy danych, kontrolery domeny, serwery pocztowe).</p><ul><li>Backup pelnego systemu (bare-metal restore)</li><li>Backup aplikacyjny z uwzglednieniem spojnosci danych (VSS)</li><li>Wsparcie dla Windows Server i glownych dystrybucji Linux</li><li>Elastyczne harmonogramy i polityki retencji</li></ul>',
    ],
    [
        'name'              => 'Virtualization Backup',
        'slug'              => 'virtualization-backup',
        'icon'              => 'layers',
        'short_description' => 'Backup srodowisk zwirtualizowanych - VMware vSphere, Microsoft Hyper-V oraz Proxmox VE - bez agentow instalowanych w kazdej maszynie.',
        'content'           => '<p>Srodowiska zwirtualizowane wymagaja innego podejscia do backupu niz pojedyncze serwery. Zapewniamy backup na poziomie hypervisora dla VMware vSphere, Microsoft Hyper-V oraz Proxmox VE, bez koniecznosci instalowania agenta w kazdej maszynie wirtualnej.</p><ul><li>Backup na poziomie hypervisora (image-based)</li><li>Wsparcie dla VMware, Hyper-V i Proxmox VE</li><li>Szybkie odtwarzanie calych maszyn wirtualnych</li><li>Minimalne obciazenie srodowiska produkcyjnego</li></ul>',
    ],
    [
        'name'              => 'Disaster Recovery',
        'slug'              => 'disaster-recovery',
        'icon'              => 'life-buoy',
        'short_description' => 'Procedury i infrastruktura odtworzeniowa na wypadek powaznej awarii - od planu DR po gotowe srodowisko zapasowe, ktore mozna uruchomic w minuty.',
        'content'           => '<p>Backup to nie to samo co Disaster Recovery. Backup pozwala odzyskac dane - DR pozwala odzyskac dzialanie firmy. Projektujemy i utrzymujemy procedury oraz infrastruktore odtworzeniowa dopasowana do Twoich celow RTO i RPO.</p><ul><li>Opracowanie planu Disaster Recovery (DRP)</li><li>Srodowisko zapasowe gotowe do szybkiego uruchomienia</li><li>Definiowanie i monitorowanie RTO/RPO</li><li>Regularne testy scenariuszy awaryjnych</li></ul>',
    ],
    [
        'name'              => 'Restore Testing',
        'slug'              => 'restore-testing',
        'icon'              => 'refresh-ccw',
        'short_description' => 'Cykliczne, rzeczywiste testy odtwarzania danych - bo kopia zapasowa, ktorej nigdy nie sprawdzono, to tylko zalozenie, nie zabezpieczenie.',
        'content'           => '<p>Najczestszym powodem, dla ktorego backup zawodzi w krytycznym momencie, jest brak testow odtwarzania. Regularnie wykonujemy rzeczywiste testy przywracania danych - nie tylko sprawdzenie statusu zadania backupu.</p><ul><li>Harmonogram cyklicznych testow odtwarzania</li><li>Testy w izolowanym srodowisku (sandbox)</li><li>Raport z kazdego testu wraz z rekomendacjami</li><li>Weryfikacja spojnosci i kompletnosci danych</li></ul>',
    ],
    [
        'name'              => 'Backup Audit',
        'slug'              => 'backup-audit',
        'icon'              => 'clipboard-check',
        'short_description' => 'Niezalezna analiza obecnego srodowiska backupu klienta - identyfikujemy luki, ryzyka i rekomendujemy konkretne poprawki.',
        'content'           => '<p>Zanim zaczniesz cokolwiek zmieniac, warto wiedziec, gdzie faktycznie stoisz. Backup Audit to niezalezny przeglad Twojego obecnego srodowiska ochrony danych - konfiguracji, polityk retencji, pokrycia i realnej odpornosci na awarie.</p><ul><li>Przeglad konfiguracji i polityk backupu</li><li>Identyfikacja luk w pokryciu (systemy bez ochrony)</li><li>Ocena zgodnosci z zasada 3-2-1</li><li>Raport z priorytetowymi rekomendacjami</li></ul>',
    ],
    [
        'name'              => 'Backup Implementation',
        'slug'              => 'backup-implementation',
        'icon'              => 'tool',
        'short_description' => 'Projektujemy i wdrazamy srodowisko backupu od zera - od doboru architektury po pelne uruchomienie i przekazanie dokumentacji.',
        'content'           => '<p>Gdy w firmie nie ma jeszcze uporzadkowanego backupu albo obecne rozwiazanie wymaga wymiany, projektujemy i wdrazamy srodowisko od podstaw - dopasowane do skali, budzetu i wymagan bezpieczenstwa.</p><ul><li>Analiza potrzeb i dobor architektury backupu</li><li>Wdrozenie i konfiguracja wybranej platformy</li><li>Migracja z istniejacego rozwiazania (jesli dotyczy)</li><li>Dokumentacja powdrozeniowa i szkolenie zespolu</li></ul>',
    ],
    [
        'name'              => 'Monitoring 24/7',
        'slug'              => 'monitoring-24-7',
        'icon'              => 'activity',
        'short_description' => 'Calodobowy nadzor nad zadaniami backupu, repozytoriami i pojemnoscia - alarmy trafiaja do nas, zanim staną sie Twoim problemem.',
        'content'           => '<p>Backup, ktory nikt nie monitoruje, prędzej czy pozniej zawiedzie w cichy sposob - jedno nieudane zadanie, ktore nikt nie zauwazy, moze kosztowac utrate danych. Nasz zespol monitoruje Twoje srodowisko backupu 24 godziny na dobe, 7 dni w tygodniu.</p><ul><li>Calodobowy monitoring zadan backupowych</li><li>Alarmy o bledach i przekroczeniach pojemnosci repozytoriow</li><li>Proaktywna reakcja na incydenty</li><li>Panel statusu dostepny dla klienta</li></ul>',
    ],
    [
        'name'              => 'Retention & Compliance',
        'slug'              => 'retention-compliance',
        'icon'              => 'file-check',
        'short_description' => 'Polityki retencji danych, raportowanie i dokumentacja zgodna z wymogami audytowymi oraz regulacjami branzowymi.',
        'content'           => '<p>Wlasciwa retencja danych to nie tylko kwestia techniczna, ale rowniez zgodnosci z regulacjami i wymogami audytowymi. Pomagamy zaprojektowac i utrzymac polityki retencji, ktore spelniaja wymagania prawne i branzowe.</p><ul><li>Projektowanie polityk retencji dopasowanych do wymagan</li><li>Raportowanie zgodnosci na potrzeby audytow</li><li>Dokumentacja procesow ochrony danych</li><li>Wsparcie przy audytach zewnetrznych</li></ul>',
    ],
];
