# SecureWare.pl

Strona firmowa i panel administracyjny SecureWare (Managed Backup, Backup as
a Service, Disaster Recovery i pozostale uslugi ochrony danych). Wlasna
aplikacja PHP 8.1+ / MySQL - bez WordPressa, bez Composera, bez kroku
budowania - gotowa do wgrania na hosting DirectAdmin.

## Struktura

Uklad jest plaski celowo - caly folder trafia bezposrednio do katalogu
domeny na DirectAdmin (np. `public_html/` albo `public_html/secureware.pl/`,
zaleznie jak hosting przypisuje domeny), bez potrzeby zmiany document root
na podfolder.

```
index.php   front controller (punkt wejscia)
.htaccess   przekierowanie ruchu do index.php + blokada .env/.sql/.log
assets/     CSS, JS, ikony (publicznie dostepne)
uploads/    pliki wgrywane przez biblioteke mediow (publicznie dostepne)
src/        kod aplikacji (Core, Controllers, Models)
views/      widoki PHP (site/ - strona publiczna, admin/ - panel)
config/     config.php (odczytuje .env)
database/   schema.sql + seed.php + przykladowe dane
```

`src/`, `config/`, `database/` i `views/` maja wlasne pliki `.htaccess`
(`Require all denied`), wiec mimo ze fizycznie leza w tym samym katalogu co
strona, nie sa dostepne bezposrednio przez przegladarke - dziala to na
standardowym Apache/LiteSpeed z wlaczonym `.htaccess` (domyslne na
DirectAdmin). To samo dotyczy pliku `.env` (blokowany osobna regula w
glownym `.htaccess`).

Panel administracyjny (CMS, RBAC, branding, logi aktywnosci, leady) jest
dostepny pod adresem skonfigurowanym w `.env` jako `ADMIN_PATH` - domyslnie
`/cloudsecurepanel`.

## Uruchomienie lokalne

Wymagania: PHP 8.1+ z rozszerzeniami `pdo_mysql`, `curl`, `fileinfo`, oraz
serwer MySQL/MariaDB.

```bash
cp .env.example .env       # uzupelnij dane bazy danych
mysql -u root -p secureware < database/schema.sql
php database/seed.php      # utworzy role, konto admina i przykladowa tresc
php -S localhost:8080
```

Otworz `http://localhost:8080` (strona publiczna) oraz
`http://localhost:8080/cloudsecurepanel/login` (panel administracyjny) -
dane logowania administratora zostana wypisane w konsoli po uruchomieniu
`seed.php`.

## Wdrozenie produkcyjne

Pelna instrukcja krok po kroku pod DirectAdmin: zobacz [DEPLOY.md](DEPLOY.md).

## Funkcje

- Publiczna strona: strona glowna, oferta (13 uslug), blog z kategoriami i
  tagami, dowolne podstrony CMS, formularz kontaktowy zabezpieczony
  Cloudflare Turnstile, `sitemap.xml` / `robots.txt`.
- Panel `/cloudsecurepanel`: logowanie z blokada po nieudanych probach,
  role i uprawnienia (RBAC) definiowane w bazie, CMS artykulow/podstron/
  uslug z polami niestandardowymi (custom fields), biblioteka mediow,
  zarzadzanie uzytkownikami, ustawienia brandingu (logo, kolory, menu,
  dane kontaktowe), integracje (Turnstile, Google Analytics, CookieYes),
  log aktywnosci administratorow, skrzynka zapytan (leadow) z formularza.
