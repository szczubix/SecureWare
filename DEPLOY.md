# Wdrozenie na DirectAdmin

Aplikacja to zwykly PHP 8.1+ / MySQL, bez Composera i bez kroku budowania -
wystarczy skopiowac pliki na serwer.

## 1. PHP i baza danych

1. W DirectAdmin ustaw wersje PHP na **8.1 lub nowsza** (Domain Setup /
   PHP Selector).
2. W sekcji **MySQL Management** utworz baze danych i uzytkownika z pelnymi
   uprawnieniami do tej bazy. Zapisz: nazwe bazy, uzytkownika, haslo, host
   (zwykle `localhost`).
3. Zaimportuj schemat przez **phpMyAdmin**: wybierz baze -> zakladka
   *Importuj* -> wskaz plik `database/schema.sql`.

## 2. Katalog publiczny (document root)

Kod dzieli sie na katalog publiczny (`/public`) i katalogi poza nim
(`/src`, `/config`, `/database`, `/storage`, `/views`) - te drugie **nie
powinny byc dostepne z przegladarki** (zawieraja m.in. dane dostepowe do
bazy w `.env`).

**Preferowana opcja:** w DirectAdmin, w *Domain Setup*, ustaw katalog
publiczny (document root) domeny na `public_html/public` (czyli podkatalog
`public` wewnatrz repozytorium wgranego do `public_html`). Wszystko poza
`public/` zostaje wtedy automatycznie poza zasiegiem HTTP.

**Jesli DirectAdmin nie pozwala zmienic document root** (np. na hostingu
współdzielonym bez tej opcji): wgraj cala zawartosc repozytorium do
`public_html`. Katalogi `src/`, `config/`, `database/`, `storage/`, `views/`
maja wlasne pliki `.htaccess` z `Deny from all` / `Require all denied`, wiec
pozostaja zablokowane nawet w tym scenariuszu - upewnij sie tylko, ze
serwer uzywa Apache z wlaczonym `mod_rewrite` i honoruje `.htaccess`
(`AllowOverride All`).

## 3. Pliki srodowiskowe

1. Skopiuj `.env.example` do `.env` (w katalogu glownym repozytorium, obok
   `public/`, nie wewnatrz niego).
2. Uzupelnij dane bazy (`DB_*`), `APP_URL` (pelny adres, np.
   `https://secureware.pl`), `MAIL_TO` (adres, na ktory maja przychodzic
   powiadomienia o nowych zapytaniach z formularza kontaktowego).
3. `ADMIN_PATH` okresla adres panelu administracyjnego (domyslnie
   `cloudsecurepanel`, czyli `/cloudsecurepanel`). Mozesz go zmienic na
   dowolny, trudny do odgadniecia ciag.
4. Jesli domena ma juz aktywny certyfikat SSL (zalecane, np. darmowy
   Let's Encrypt z poziomu DirectAdmin), zostaw `SESSION_SECURE=true`.
   Jesli tymczasowo dzialasz bez HTTPS, ustaw `SESSION_SECURE=false` -
   inaczej logowanie do panelu nie zadziala (ciasteczko sesji wymaga HTTPS).

## 4. Uprawnienia do zapisu

Serwer PHP musi miec prawo zapisu do:

- `public/uploads/` (biblioteka mediow)
- `storage/uploads/`, `storage/logs/`

Zwykle wystarczaja standardowe uprawnienia `755`/`775` nadawane przez
DirectAdmin; jesli upload plikow zwraca blad zapisu, ustaw `775` na tych
katalogach z poziomu File Managera.

## 5. Dane poczatkowe (role, admin, tresci)

Uruchom skrypt seedujacy **raz**, po imporcie schematu:

```bash
php database/seed.php
```

- Jesli masz dostep SSH do serwera DirectAdmin - uruchom komende bezposrednio
  na serwerze, w katalogu repozytorium.
- Jesli nie masz SSH, poproś dzial hostingu o jednorazowe uruchomienie tego
  polecenia (to zwykly skrypt PHP CLI, nie wymaga zadnych dodatkowych
  uprawnien poza dostepem do bazy skonfigurowanej w `.env`).

Skrypt wypisze w konsoli wygenerowany adres e-mail i haslo pierwszego konta
administratora panelu - **zmien to haslo od razu po pierwszym zalogowaniu**
(Uzytkownicy -> edytuj wlasne konto). Skrypt jest bezpieczny do
wielokrotnego uruchamiania - nie nadpisze istniejacych danych ani nie
utworzy drugiego konta administratora.

Domyslne dane logowania mozna tez wymusic recznie przed pierwszym
uruchomieniem, ustawiajac zmienne srodowiskowe `SEED_ADMIN_EMAIL` i
`SEED_ADMIN_PASSWORD` w powloce przed wywolaniem skryptu.

## 6. Pierwsze logowanie i konfiguracja

1. Wejdz na `https://secureware.pl/<ADMIN_PATH>/login` i zaloguj sie danymi
   z kroku 5.
2. W **Ustawienia -> Branding** uzupelnij nazwe, logo, kolory, dane
   kontaktowe i menu.
3. W **Ustawienia -> Integracje** wklej:
   - klucze **Cloudflare Turnstile** (formularz kontaktowy),
   - **Google Analytics 4** Measurement ID,
   - caly tag `<script>` z **cookieyes.com** (baner zgod na cookies).
4. Utworz dodatkowych uzytkownikow panelu w **Uzytkownicy**, przypisujac im
   role z zakladki **Role i uprawnienia** (Administrator / Redaktor /
   Sprzedaz - lub wlasne, zdefiniowane recznie).

## 7. Kolejne aktualizacje

Kazda kolejna aktualizacja to po prostu podmiana plikow (np. `git pull` na
serwerze, jesli masz tam repozytorium, albo ponowny upload przez FTP/File
Manager). Nie ma kroku budowania ani `composer install` - zadna dodatkowa
czynnosc po stronie serwera nie jest wymagana, chyba ze aktualizacja
wprowadza zmiany w `database/schema.sql` (wowczas doimportuj tylko nowe
zapytania recznie przez phpMyAdmin).
