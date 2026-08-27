<?php

/**
 * Domyślne podstrony CMS. Edytowalne później w panelu /cloudsecurepanel/pages.
 * Uwaga: slug "kontakt" jest obsługiwany przez dedykowany formularz
 * (ContactController), więc nie jest tu seedowany jako zwykła strona.
 */

return [
    [
        'title'            => 'O nas',
        'slug'             => 'o-nas',
        'meta_description' => 'SecureWare - zespół specjalistów od backupu, disaster recovery i ochrony danych dla firm.',
        'content'          => '<h2>Kim jesteśmy</h2><p>SecureWare to zespół specjalistów skupiony wyłącznie na jednym obszarze: ochronie danych. Zarządzany backup, backup jako usługa, disaster recovery i cykliczne testy odtwarzania - to wszystko, czym się zajmujemy, i robimy to dobrze.</p><h2>Jak pracujemy</h2><p>Nie sprzedajemy jednorazowego wdrożenia i znikamy. Każde środowisko, którym się opiekujemy, jest monitorowane 24/7, regularnie testowane i raportowane w sposób zrozumiały - również dla osób spoza IT.</p><h2>Dla kogo</h2><p>Pracujemy z firmami, dla których utrata danych oznacza realne straty finansowe i wizerunkowe - i które chcą mieć pewność, że w razie awarii dane wrócą, a nie tylko "prawdopodobnie wrócą".</p>',
    ],
    [
        'title'            => 'Bezpieczeństwo',
        'slug'             => 'bezpieczenstwo',
        'meta_description' => 'Jak SecureWare chroni Twoje kopie zapasowe - szyfrowanie, izolacja, kontrola dostępu, monitoring i reakcja na incydenty.',
        'content'          => '<h2>Bezpieczeństwo to nie dodatek do backupu - to jego fundament</h2><p>Kopia zapasowa, która sama nie jest zabezpieczona, nie chroni przed niczym - ransomware celuje dziś w backup równie często, co w dane produkcyjne. Dlatego każde środowisko, którym się opiekujemy, projektujemy z założeniem, że atakujący prędzej czy później spróbuje dostać się właśnie tam.</p><h2>Szyfrowanie</h2><p>Dane szyfrujemy zarówno w tranzycie, jak i w spoczynku. Kopie zapasowe trafiają do repozytorium kanałem szyfrowanym, a same repozytoria są szyfrowane niezależnie od tego, czy dane trafiają do naszej infrastruktury, czy pozostają u Ciebie.</p><h2>Izolacja i niezmienność (immutable)</h2><p>Krytyczne kopie przechowujemy w repozytoriach, których nie da się nadpisać ani usunąć w oknie retencji - nawet z przejętym kontem administratora. To zgodne z zasadą 3-2-1-1-0, którą stosujemy jako standard, nie wyjątek.</p><h2>Kontrola dostępu</h2><p>Dostęp do środowisk backupu ograniczamy do niezbędnego minimum (least privilege), wymagamy uwierzytelniania wieloskładnikowego (MFA) i oddzielamy uprawnienia do backupu od uprawnień administracyjnych w środowisku produkcyjnym klienta - żeby przejęcie jednego konta nie oznaczało utraty wszystkiego.</p><h2>Monitoring i wczesne wykrywanie</h2><p>Środowisko backupu monitorujemy 24/7, a tam gdzie klient tego potrzebuje, rozszerzamy to o <a href="/oferta/siem-as-a-service">SIEM as a Service</a> - zbieranie i korelację logów, które wykrywa podejrzaną aktywność, zanim dojdzie do zaszyfrowania danych.</p><h2>Testy i reakcja na incydenty</h2><p>Backup, którego nikt nie testował, to założenie, nie zabezpieczenie - dlatego regularnie wykonujemy rzeczywiste testy odtwarzania. Mamy też spisaną procedurę reakcji na incydent, żeby w razie ataku wiadomo było dokładnie, co robić, zamiast improwizować pod presją.</p><p>Masz pytania o to, jak wygląda to konkretnie w Twoim przypadku? <a href="/kontakt">Porozmawiajmy</a>.</p>',
    ],
    [
        'title'            => 'Polityka prywatności',
        'slug'             => 'polityka-prywatnosci',
        'meta_description' => 'Informacje o przetwarzaniu danych osobowych przez SecureWare.',
        'content'          => '<h2>Administrator danych</h2><p>Administratorem danych osobowych przetwarzanych w związku z korzystaniem z serwisu secureware.pl jest SecureWare. Dane kontaktowe administratora znajdują się w stopce strony oraz na podstronie Kontakt.</p><h2>Jakie dane przetwarzamy</h2><p>Przetwarzamy dane podane dobrowolnie w formularzu kontaktowym (imię, adres e-mail, numer telefonu, treść wiadomości) w celu udzielenia odpowiedzi na zapytanie oraz przygotowania oferty.</p><h2>Pliki cookies</h2><p>Serwis wykorzystuje pliki cookies w celach statystycznych (Google Analytics) oraz do zarządzania zgodami na przetwarzanie danych (CookieYes). Szczegółowe ustawienia zgód można zmienić w każdej chwili z poziomu banera cookies.</p><h2>Twoje prawa</h2><p>Przysługuje Ci prawo dostępu do danych, ich sprostowania, usunięcia oraz ograniczenia przetwarzania. W celu realizacji swoich praw skontaktuj się z nami poprzez formularz kontaktowy.</p><p><em>Ta treść jest szablonem i powinna zostać zweryfikowana przez prawnika przed publikacją produkcyjną.</em></p>',
    ],
    [
        'title'            => 'Regulamin',
        'slug'             => 'regulamin',
        'meta_description' => 'Regulamin korzystania z serwisu secureware.pl oraz świadczenia usług przez SecureWare.',
        'content'          => '<h2>Postanowienia ogólne</h2><p>Niniejszy regulamin określa zasady korzystania z serwisu internetowego secureware.pl oraz ogólne warunki świadczenia usług backupu, disaster recovery i usług pokrewnych przez SecureWare.</p><h2>Zakres usług</h2><p>Szczegółowy zakres, warunki i ceny poszczególnych usług (Managed Backup, Backup as a Service, Disaster Recovery i pozostałe) są każdorazowo określane w indywidualnej umowie lub ofercie handlowej.</p><h2>Reklamacje</h2><p>Reklamacje dotyczące świadczonych usług można zgłaszać za pośrednictwem formularza kontaktowego lub adresu e-mail wskazanego w stopce serwisu.</p><p><em>Ta treść jest szablonem i powinna zostać zweryfikowana przez prawnika przed publikacją produkcyjną.</em></p>',
    ],
];
