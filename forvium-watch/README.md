# Forvium Watch — Support Access

Bezpieczny dostęp serwisowy: operator Forvium może otworzyć panel klienta w jego
kontekście, w trybie **READ_ONLY**, za zgodą klienta, bez znajomości hasła i bez
przejmowania sesji użytkownika.

```
forvium-watch/
├── compose.yaml        całe środowisko lokalne: gateway, API (2 repliki), worker, oba frontendy,
│                       PostgreSQL, migracje, Mailpit
├── backend/            wspólny backend FastAPI (api.forvium.com)
│   ├── forvium/
│   │   ├── identity/          Identity & Access – konta, sesje, MFA (TOTP + WebAuthn), limity prób
│   │   ├── organizations/     Organizations & RBAC – Permission, role, dane organizacji
│   │   ├── platform_admin/    Platform Administration – role operatorów, użytkownicy, zgłoszenia
│   │   ├── support_tickets/   Support Tickets – zgłoszenia, do których przypinany jest dostęp
│   │   ├── audit/             Audit Log – zdarzenia, middleware API, eksport, łańcuch skrótów
│   │   ├── notifications/     Notification Engine – powiadomienia w aplikacji + wysyłka e-mail
│   │   ├── support_access/    prośby, zgody (też stałe), sesje, przedłużenia, nagrania, Break Glass
│   │   ├── security/          wykrywanie anomalii i alerty, sanityzacja zrzutów widoku
│   │   ├── core/crypto.py     szyfrowanie danych w spoczynku (AES-256-GCM, klucze z KMS)
│   │   ├── jobs.py, worker.py zadania w tle i ich heartbeat (osobny kontener `worker`)
│   │   ├── monitoring.py      X-Request-ID, log dostępu, metryki Prometheus
│   │   └── access.py          jedno miejsce uwierzytelniania i autoryzacji (RBAC + RLS)
│   ├── migrations/            Alembic: 0001 schemat (+ trigger audytu), 0002 RLS i uprawnienia,
│   │                          0003 szyfrowanie, WebAuthn, dwie osoby, przedłużenia, alerty, nagrania,
│   │                          0004 heartbeat zadań w tle
│   └── tests/
├── deploy/             role PostgreSQL, gateway (routing po hoście, limity zapytań),
│                       monitoring (Prometheus, reguły alertów, Alertmanager, Grafana)
└── frontend/
    ├── admin/          admin.forvium.com – użytkownicy, prośby, nadzór, alerty, audyt, Break Glass, klucze
    └── app/            app.forvium.com – zgody, ustawienia, podgląd na żywo, nagrania, baner wsparcia
```

## Szybki start

```bash
cd forvium-watch
docker compose up --build
```

| Usługa | Adres |
|---|---|
| app (klient) | http://app.localhost:8080 |
| admin (operatorzy) | http://admin.localhost:8080 |
| API | http://api.localhost:8080 (dokumentacja: `/docs`) |
| Mailpit (wysłane e-maile) | http://localhost:8025 |

Przeglądarki rozwiązują `*.localhost` na 127.0.0.1 bez zmian w `/etc/hosts`.

### Kontenery

| Kontener | Rola | Sieci |
|---|---|---|
| `gateway` | nginx: jedyne wejście (port 8080), routing po nazwie hosta, limity zapytań na logowanie i API, `X-Request-ID`, blokada `/metrics` z zewnątrz, nieznany host → zamknięcie połączenia | edge |
| `app`, `admin` | statyczne frontendy (nginx, CSP bez inline) z wbudowanym adresem API | edge |
| `api` | FastAPI, bezstanowe, 2 repliki, **bez** zadań w tle (`RUN_BACKGROUND_JOBS=false`) | edge, backend |
| `worker` | zadania w tle: wygaszanie sesji, wysyłka e-maili, wykrywanie anomalii, eksport audytu; healthcheck `python -m forvium.worker --check` sprawdza heartbeat w `job_runs` | backend |
| `migrate` | jednorazowo: migracje jako właściciel schematu + dane demo | backend |
| `db` | PostgreSQL 16 z RLS i osobnymi rolami | backend |
| `mailpit` | przechwytuje wysłane e-maile | backend |

Baza, worker i API nie publikują portów: z zewnątrz dostępny jest tylko `gateway` (i lokalnie UI Mailpit).
Logi API i workera są w formacie JSON (`FORVIUM_LOG_FORMAT=json`).

Kontener `migrate` uruchamia migracje jako właściciel schematu i ładuje dane demo.
Hasło wszystkich kont to `Forvium-demo-2026!`, a sekrety TOTP do zeskanowania lub wpisania
w aplikacji uwierzytelniającej są w `docker compose logs migrate`.

| Konto | Rola |
|---|---|
| `alice@acme.example` | właścicielka organizacji Acme (zatwierdza dostęp) |
| `dorota@acme.example` | administratorka Acme (druga osoba przy zatwierdzaniu przez dwie osoby) |
| `bob@acme.example` | członek Acme (użytkownik referencyjny) |
| `carol@beta.example` | właścicielka organizacji Beta |
| `ola@forvium.com` | Support L2 (prośby, Break Glass) |
| `piotr@forvium.com` | Support L1 (bez CVE) |
| `marta@forvium.com` | kierownik supportu (nadzór sesji, audyt) |
| `ewa@forvium.com`, `tomasz@forvium.com` | oficerowie bezpieczeństwa (zatwierdzanie i przegląd Break Glass) |

Break Glass jest domyślnie wyłączony. Żeby go włączyć lokalnie, uruchom
`FORVIUM_BREAK_GLASS_ENABLED=true docker compose up`.

## Monitoring

* **Identyfikator zadania**: gateway nadaje `X-Request-ID`, API go przyjmuje (albo generuje),
  zwraca w odpowiedzi i dołącza do każdej linii logu.
* **Logi JSON** (`FORVIUM_LOG_FORMAT=json`): log dostępu `forvium.access` z metodą, szablonem
  trasy (bez identyfikatorów i query stringa), kodem, czasem i `request_id`; logi workera
  z wynikiem każdego zadania.
* **`/metrics`** (Prometheus): ruch i czasy odpowiedzi per trasa, stan zadań w tle
  (`forvium_job_stale`, `forvium_job_last_success_age_seconds`, liczba przebiegów i błędów),
  aktywne sesje wsparcia, czekające prośby, otwarte alerty, kolejka e-mail. Gateway zwraca
  na `/metrics` 404; dodatkowo można wymagać `FORVIUM_METRICS_TOKEN`.
* **Stan zadań w tle**: zakładka *Alerty* w panelu admin (`GET /api/admin/security/jobs`)
  pokazuje ostatni udany przebieg i oznacza zatrzymane zadania; healthcheck kontenera
  `worker` robi to samo.
* **Profil `monitoring`**: `docker compose --profile monitoring up` dodaje Prometheus
  (http://localhost:9090), Alertmanager i Grafanę (http://localhost:3000, `admin` /
  `local-grafana`) z gotowym dashboardem. Reguły w `deploy/monitoring/alerts.yml`:
  zatrzymane zadanie w tle, niedostępna replika API, błędy 5xx, alerty bezpieczeństwa
  o wysokiej wadze, niewysyłane e-maile. Lokalnie Alertmanager wysyła alerty e-mailem
  do Mailpit (`security@forvium.local`).

## Logowanie operatora

Hasło + drugi składnik: kod TOTP albo **klucz bezpieczeństwa (WebAuthn)**. Przy kluczu
panel najpierw wysyła e-mail i hasło do `POST /api/admin/auth/login/webauthn/options`
(błędne hasło liczy się do limitu prób, a lista kluczy nie wycieka bez hasła), a potem
asercję do `POST /api/admin/auth/login`. Wyzwanie logowania jest jednorazowe i ma osobny
cel (`login`) - asercja z ponownej weryfikacji go nie zastąpi. Przy
`FORVIUM_OPERATOR_LOGIN_WEBAUTHN_ONLY=true` operator, który ma klucz, nie zaloguje się już
kodem TOTP. W audycie `identity.login.operator` ma `second_factor`: `webauthn` albo `totp`.

## Przepływ

1. **Prośba** (`admin`): operator wybiera organizację i użytkownika referencyjnego, podaje
   powód, numer otwartego zgłoszenia tej organizacji, czas (1–15 min) i zakres. Wymagana jest
   **ponowna weryfikacja MFA**. Każdy kod TOTP jest jednorazowy.
2. **Zgoda** (`app`): właściciel lub administrator organizacji zatwierdza prośbę (może
   zawęzić zakres i jednostki oraz ustawić ważność) albo ją odrzuca. Prośba mieszcząca się
   w **zgodzie stałej** klienta jest zatwierdzana automatycznie. Operator nie zatwierdzi
   własnej prośby, a żadne konto Forvium nie może zatwierdzać zgód.
3. **Sesja** (`admin` → `app`): start wymaga ponownie MFA. Backend tworzy osobny rekord
   `SupportSession` i jednorazowy kod startowy ważny 60 s. Panel otwiera
   `app…/support-launch.html#code=…` w nowej karcie (`noopener`), a strona wymienia kod na
   token `fws_…`, trzymany tylko w `sessionStorage` tej karty.
4. **Każde żądanie** z tokenem `fws_` przechodzi pełną walidację: sesja, czas, zgoda (także
   stała), prośba, operator i jego rola, użytkownik referencyjny, organizacja, zgłoszenie.
   Na PostgreSQL transakcja jest dodatkowo ograniczona przez RLS do organizacji sesji.
5. **Zakończenie** może nastąpić z kilku stron:
   * operator: „Zakończ dostęp” na banerze albo zakończenie w panelu admin,
   * kierownik supportu: wymuszone zakończenie w zakładce „Nadzór sesji”,
   * klient: zakończenie sesji albo cofnięcie zgody,
   * automatycznie: po upływie czasu albo po zamknięciu zgłoszenia.

   Klient zawsze dostaje podsumowanie: czas, oglądane widoki i zablokowane próby.

## Model bezpieczeństwa

* **Brak osobnego systemu uprawnień.** Sesja wsparcia przechodzi przez tę samą zależność
  `require_org_permission(Permission.X)` co klient:

  ```
  uprawnienia roli użytkownika referencyjnego
  ∩ zakresy z zgody klienta  ∩ zakresy dopuszczone dla roli operatora
  ∩ SUPPORT_READ_ONLY_PERMISSIONS  − SUPPORT_FORBIDDEN_PERMISSIONS
  ```

  Twarda lista zakazów obejmuje: ustawienia, role i członkostwa, usunięcie organizacji,
  eksport, płatności, subskrypcję, SMTP, webhooki, sekrety, tokeny API i zatwierdzanie zgód.
* **READ_ONLY na dwóch poziomach.** Token `fws_` może wysyłać tylko żądania odczytu
  (GET/HEAD/OPTIONS). Jedyny wyjątek to zakończenie własnej sesji. Niezależnie od tego
  działa RBAC.
* **Izolacja sesji.** Są trzy rozłączne typy tokenów (`fwu_`, `fwo_`, `fws_`), każdy
  weryfikowany we własnej tabeli i przechowywany wyłącznie jako skrót SHA-256. Sesja
  wsparcia nie dotyka sesji klienta ani operatora.
* **Izolacja organizacji.** Działa w aplikacji (dostęp tylko do organizacji z sesji,
  opcjonalnie do wybranych jednostek) i w bazie (**Row-Level Security**, migracja `0002`).
  Gdy transakcja ma ustawione `forvium.support_org`, tabele z danymi organizacji pokazują
  i przyjmują tylko jej wiersze, więc nawet błąd w kodzie nie ujawni innej organizacji.
* **Role bazy** (`deploy/postgres/roles.sql`):
  * `forvium_migrator` jest właścicielem schematu i służy tylko do migracji;
  * `forvium_app` to konto API bez superusera (więc RLS działa); na tabelach audytu ma
    wyłącznie `SELECT` i `INSERT`.

  Dodatkowo trigger odrzuca `UPDATE` i `DELETE` na `audit_events` dla każdego.
* **Limity prób.** Blokada 429 na 15 min po:
  * 5 nieudanych logowaniach na konto albo 20 na IP,
  * 5 nieudanych kodach MFA przy ponownej weryfikacji,
  * 10 złych kodach startowych z jednego IP,
  * 30 nieprawidłowych tokenach wsparcia z jednego IP.

  Każda blokada trafia do audytu (`security.lockout`, `security.throttled`). Klucze
  liczników są przechowywane jako skróty, bez e-maili i adresów IP.
* **Spójność.** `commit` następuje przed wysłaniem odpowiedzi (`Depends(get_db, scope="function")`),
  więc klient nie może zobaczyć potwierdzenia zmiany, której jeszcze nie ma w bazie.
* **Frontendy** działają pod ścisłym CSP: bez skryptów i stylów inline, z `frame-ancestors 'none'`.
  Dochodzą do tego `nosniff`, `no-referrer` i `COOP`.

## Zgoda stała

Klient (`Dostęp serwisowy` → `Zgody stałe`, potwierdzenie kodem MFA) z góry określa:
* zakres i jednostki,
* maksymalny czas sesji (do 15 min),
* role supportu, które mogą z niej korzystać,
* ważność (do 365 dni).

Prośba mieszcząca się w tych granicach jest zatwierdzana automatycznie (`basis=standing`).
Zgoda z niej wynikająca jest ważna 4 h, a klient i tak dostaje powiadomienie. Cofnięcie
zgody stałej natychmiast cofa wszystkie wynikające z niej zgody i kończy ich sesje.

## Szyfrowanie danych w spoczynku

Sekrety TOTP, sekrety i konfiguracja SMTP/webhooków organizacji oraz nagrania sesji są w
bazie szyfrowane (AES-256-GCM, `core/crypto.py`). Każdy szyfrogram jest związany z kolumną
(AAD) i oznaczony identyfikatorem klucza, co pozwala rotować klucze bez przestojów.

* **Źródło kluczy:** HashiCorp Vault Transit (`FORVIUM_DATA_KEYS_WRAPPED`, `FORVIUM_VAULT_*`).
  Klucze danych są odszyfrowywane w Vault przy starcie i trzymane tylko w pamięci. Alternatywnie
  `FORVIUM_DATA_KEYS` (np. z menedżera sekretów). Bez klucza API **nie wystartuje**.
* **Rotacja:** dodaj nowy klucz, ustaw go jako `FORVIUM_DATA_KEY_ID`, a potem uruchom
  `python -m forvium.core.crypto reencrypt`. Ta sama komenda szyfruje dane zapisane przed
  migracją 0003 (Compose robi to automatycznie w kontenerze `migrate`).
* Nowy klucz: `python -m forvium.core.crypto generate-key`.

## WebAuthn (klucze bezpieczeństwa / passkeys)

Operator dodaje klucz FIDO2 albo passkey w zakładce `Konto`, potwierdzając to kodem TOTP.
Od tej chwili każda ponowna weryfikacja odbywa się kluczem, z weryfikacją użytkownika (PIN lub
biometria):
* prośba o dostęp,
* start i przedłużenie sesji,
* zatwierdzenie Break Glass.

Ochrona:
* wyzwania są jednorazowe (zużywane atomowo), ważne 2 minuty i przypięte do osoby i celu;
* sprawdzane są origin i RP ID (ochrona przed phishingiem);
* licznik podpisów wykrywa sklonowane klucze;
* dodanie i usunięcie klucza są audytowane, a właściciel konta dostaje powiadomienie.

**Break Glass wymaga klucza:** sam kod TOTP nie wystarcza do wniosku, zatwierdzenia ani startu
sesji awaryjnej.

## Zatwierdzanie przez dwie osoby

Organizacja może włączyć wymóg dwóch zatwierdzeń (`Dostęp serwisowy` → `Zatwierdzanie przez dwie
osoby`, potwierdzenie kodem MFA).
* Pierwsze zatwierdzenie tylko zapisuje parametry zgody.
* Druga, **inna** osoba może je potwierdzić albo zawęzić (nigdy rozszerzyć). Dopiero wtedy
  powstaje zgoda z obiema tożsamościami w audycie.
* Zgody stałe w tym trybie też wymagają potwierdzenia przez drugą osobę.
* Wyłączenie ochrony również wymaga drugiej osoby: jedna je zgłasza, druga potwierdza.

## Przedłużanie sesji

Zakładka `Moje prośby` → `Przedłuż`:
* wymaga ponownej weryfikacji i powodu, który klient widzi w powiadomieniu;
* jedno przedłużenie to maksymalnie 15 min, maksymalnie 2 przedłużenia;
* łącznie sesja trwa najwyżej 45 min (Break Glass: 60 min) i nigdy nie dłużej niż ważność zgody.

Baner w trybie wsparcia odświeża pozostały czas co 15 s.

## Podgląd na żywo i nagrania sesji

W trybie wsparcia frontend po każdym widoku wysyła zrzut DOM. Pola tekstowe formularzy nie są
wysyłane. Backend:
* sanityzuje zrzut białą listą (bez skryptów, stylów, linków i obrazów),
* szyfruje go,
* ogranicza rozmiar i częstotliwość zrzutów,
* usuwa zrzuty po 30 dniach.

Klient w `Historii sesji`:
* **Podgląd na żywo** – co operator ogląda teraz (odświeżane co 2 s, iframe w piaskownicy
  bez skryptów), ostatnie operacje i przycisk `Przerwij sesję`;
* **Nagranie** – odtwarzanie klatka po klatce.

Po stronie Forvium nagrania widzą tylko role z `platform.audit.read`, a otwarcie każdej klatki
trafia do audytu (`support.recording.viewed`). Operator widzi na banerze, że klient może go
obserwować.

## Wykrywanie anomalii

Proces w tle (co `FORVIUM_ANOMALY_INTERVAL_SECONDS`) przegląda audyt i tworzy alerty
(zakładka `Alerty`, deduplikacja po kluczu):

| Reguła | Waga | Akcja |
|---|---|---|
| seria ≥5 odmów w sesji w ciągu 10 min | wysoka | **automatyczne zakończenie sesji** |
| ≥3 próby użycia tokenu zakończonej sesji | wysoka | – |
| ≥5 sesji operatora / sesje w ≥3 organizacjach w ciągu godziny | średnia | – |
| blokada operatora po nieudanych próbach MFA/logowania | średnia | – |
| sesja poza godzinami pracy (pn–pt 7–19, Europe/Warsaw) | niska | – |
| każde zatwierdzenie Break Glass | wysoka | – |

Alerty średnie i wyższe trafiają do kierownika supportu i oficerów bezpieczeństwa, a wysokie
dodatkowo e-mailem do zespołu bezpieczeństwa. Alertu nie może obsłużyć osoba, której dotyczy.

## Break Glass

Dostęp awaryjny bez zgody klienta. Domyślnie jest **wyłączony**
(`FORVIUM_BREAK_GLASS_ENABLED=false`).

1. Operator z uprawnieniem `platform.break_glass.request` (Support L2 lub kierownik)
   składa wniosek, potwierdzając go **kluczem WebAuthn**. Wymagane są:
   * kategoria incydentu,
   * uzasadnienie (min. 200 znaków),
   * otwarte zgłoszenie,
   * czas sesji do 30 min.
2. **Inny** oficer bezpieczeństwa zatwierdza wniosek własnym kluczem WebAuthn (4 oczy). Wniosek
   wygasa po 1 h, zgoda awaryjna po 2 h. Administrator platformy nie uczestniczy w
   procedurze (rozdział obowiązków).
3. Powiadomienia trafiają do:
   * oficerów bezpieczeństwa i na adresy `FORVIUM_SECURITY_TEAM_EMAILS` przy wniosku,
     zatwierdzeniu i starcie sesji;
   * klienta (w aplikacji i e-mailem) przy zatwierdzeniu, starcie i końcu sesji.

   Klient może natychmiast cofnąć zgodę awaryjną.
4. Sesja jest nadal READ_ONLY, z banerem „TRYB AWARYJNY FORVIUM (BREAK GLASS) — TYLKO ODCZYT”.
5. **Niezależny audyt.** Każde zdarzenie procedury jest oznaczane `is_break_glass`. Dotyczy
   to także każdej operacji API w sesji awaryjnej, a flaga jest wyliczana z trybu prośby,
   więc kod nie może jej pominąć. Zdarzenia są dodatkowo zapisywane do osobnego pliku z
   łańcuchem skrótów (`FORVIUM_BREAK_GLASS_AUDIT_PATH`).
6. **Przegląd po incydencie** wykonuje oficer niezależny od wnioskującego i zatwierdzającego.
   Klient dostaje z niego raport.

## Audyt

| Zdarzenie | Akcja |
|---|---|
| utworzenie prośby / auto-zatwierdzenie | `support.request.created` / `support.request.auto_approved` |
| akceptacja / odrzucenie | `support.request.approved` / `support.request.rejected` |
| rozpoczęcie / zakończenie sesji | `support.session.started`, `.launched` / `.ended` |
| każda operacja API w trybie wsparcia | `support.api_call` (metoda, szablon trasy, kod HTTP) |
| cofnięcie zgody (też stałej) | `support.consent.revoked`, `support.standing_consent.revoked` + `support.session.revoked` |
| automatyczne wygaśnięcie | `support.session.expired`, `support.request.expired` |
| nieudane próby i blokady | `support.access_denied`, `*.create/approve/start` z `outcome=denied`, `security.lockout` |
| Break Glass | `break_glass.requested/approved/rejected/reviewed` + wszystko z `is_break_glass=true` |
| eksport audytu | `audit.exported` |

* Każdy wpis ma identyfikator operatora (`actor_user_id`) i użytkownika referencyjnego
  (`on_behalf_of_user_id`). Do logu nie trafia treść żądań ani odpowiedzi, a klucze
  wyglądające na poufne są maskowane.
* Udane operacje zapisują się w tej samej transakcji co zmiana. Odmowy i operacje API
  zapisują się we własnej transakcji, więc przetrwają rollback.
* **Panel audytu** (`admin` → `Audyt`, uprawnienie `platform.audit.read`) ma filtry: operator,
  organizacja, zgłoszenie, sesja, akcja, wynik, tryb Break Glass i daty. Ma też paginację
  i eksport CSV.
* **Eksport do zewnętrznego magazynu** działa co `FORVIUM_AUDIT_EXPORT_INTERVAL_SECONDS`:
  * plik JSONL z łańcuchem skrótów HMAC (`FORVIUM_AUDIT_EXPORT_PATH`, np. wolumen WORM),
  * lub partie JSON do SIEM (`FORVIUM_AUDIT_EXPORT_URL`, podpis `X-Forvium-Signature`).

  Weryfikacja łańcucha: `python -m forvium.audit.verify audit.jsonl --key …`.

## Konfiguracja (zmienne `FORVIUM_*`)

| Zmienna | Domyślnie | Opis |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./forvium.db` | w produkcji `postgresql+psycopg://forvium_app:…` |
| `APP_ORIGIN`, `ADMIN_ORIGIN` | `https://app.forvium.com`, `https://admin.forvium.com` | CORS, link startowy sesji |
| `SMTP_HOST`, `_PORT`, `_USERNAME`, `_PASSWORD`, `_FROM`, `_STARTTLS` | brak hosta = e-maile tylko logowane | platformowy SMTP Forvium |
| `EMAIL_INTERVAL_SECONDS` | 15 | wysyłka kolejki e-mail (ponowienia 2/4/8… min, maks. 5 prób) |
| `SUPPORT_SWEEP_INTERVAL_SECONDS` | 60 | wygaszanie sesji i prośb w tle |
| `BREAK_GLASS_ENABLED` | `false` | procedura awaryjna |
| `SECURITY_TEAM_EMAILS` | — | adresy zespołu bezpieczeństwa (po przecinku) |
| `BREAK_GLASS_AUDIT_PATH` | — | niezależny strumień zdarzeń Break Glass |
| `AUDIT_EXPORT_PATH`, `AUDIT_EXPORT_URL`, `AUDIT_EXPORT_HMAC_KEY`, `AUDIT_EXPORT_INTERVAL_SECONDS` | —, —, —, 30 | eksport audytu |
| `DATA_KEYS_WRAPPED`, `VAULT_ADDR`, `VAULT_TOKEN`, `VAULT_TRANSIT_KEY` | —, —, —, `forvium-data` | klucze danych z Vault Transit |
| `DATA_KEYS`, `DATA_KEY_ID` | — | klucze danych wprost (`kid:base64,...`) i aktywny klucz |
| `ALLOW_INSECURE_DEV_KEY` | `false` | tylko lokalnie: stały klucz deweloperski |
| `WEBAUTHN_RP_ID` | host `ADMIN_ORIGIN` | identyfikator RP dla kluczy (np. `forvium.com`) |
| `OPERATOR_LOGIN_WEBAUTHN_ONLY` | `false` | operator z kluczem loguje się wyłącznie kluczem (zalecane w produkcji) |
| `ANOMALY_INTERVAL_SECONDS` | 60 | wykrywanie anomalii |
| `AUTO_CREATE_SCHEMA` | `false` | tylko eksperymenty; schemat tworzą migracje |
| `RUN_BACKGROUND_JOBS` | `true` | `false` w replikach API, gdy zadania wykonuje osobny `worker` |
| `LOG_FORMAT`, `LOG_LEVEL` | `text`, `INFO` | `json` = jeden obiekt JSON na linię (logi aplikacji i dostępu) |
| `METRICS_TOKEN` | — | wymagany `Authorization: Bearer …` dla `/metrics` |

### Wdrożenie

1. Raz uruchom `deploy/postgres/roles.sql` jako superuser.
2. Przy każdym wdrożeniu, przed startem API, uruchom `alembic upgrade head` i
   `python -m forvium.core.crypto reencrypt` jako `forvium_migrator`.
3. Uruchom repliki API (`RUN_BACKGROUND_JOBS=false`) i jeden `worker` jako `forvium_app`,
   za gatewayem z `deploy/gateway/` (w produkcji z TLS).
4. Frontendy budują się z `frontend/Dockerfile` (`--build-arg PANEL=app|admin`).

## Rozwój bez Dockera

```bash
cd backend
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
export FORVIUM_DATABASE_URL=sqlite:///./forvium.db \
       FORVIUM_APP_ORIGIN=http://localhost:8001 FORVIUM_ADMIN_ORIGIN=http://localhost:8002
python -m forvium.seed                 # migracje + dane demo
uvicorn forvium.asgi:app --port 8000
python -m http.server 8001 -d ../frontend/app      # w osobnych terminalach
python -m http.server 8002 -d ../frontend/admin
```

Każda zmiana modelu wymaga migracji: `alembic revision --autogenerate -m "…"`. Test
`test_migrations_match_models` nie przepuści zmiany bez migracji.

## Testy i CI

```bash
cd backend && pytest                                                          # SQLite
FORVIUM_TEST_DATABASE_URL=postgresql+psycopg://postgres@host/forvium_test pytest   # PostgreSQL (+ testy RLS i ról)
```

| Plik | Zakres |
|---|---|
| `test_support_access.py` | 10 obowiązkowych scenariuszy (`test_01`…`test_10`) + MFA, limity czasu, jednostki, powiadomienia |
| `test_standing_consent.py` | zgoda stała: auto-zatwierdzanie, granice, cofnięcie, wygaśnięcie, MFA |
| `test_break_glass.py` | pełna procedura, 4 oczy, uprawnienia, wygaśnięcie, cofnięcie przez klienta, wykrywanie manipulacji |
| `test_admin_oversight.py` | filtry i paginacja audytu, CSV, nadzór i wymuszone zakończenie sesji |
| `test_throttle.py` | limity prób logowania, MFA i kodów startowych |
| `test_infrastructure.py` | migracje ↔ modele, e-mail z ponawianiem, eksport audytu, commit przed odpowiedzią |
| `test_postgres_isolation.py` | RLS, uprawnienia `forvium_app`, pełny przepływ jako konto bez superusera |
| `test_crypto.py` | szyfrogramy w bazie, wiązanie z kolumną, rotacja, Vault Transit, CLI `reencrypt` |
| `test_webauthn.py` | rejestracja i step-up kluczem, powtórzenie asercji, zły origin/RP/brak UV, klon klucza, Break Glass |
| `test_dual_approval.py` | dwie osoby: prośby, zgody stałe, wyłączenie ochrony |
| `test_session_extension.py` | przedłużenia: MFA, limity, granica 45 min i ważności zgody, powiadomienia |
| `test_anomalies.py` | reguły, automatyczne zakończenie sesji, deduplikacja, obsługa alertów |
| `test_recording.py` | podgląd na żywo, nagrania, sanityzacja, szyfrowanie, limity, retencja, audyt otwarć |

Workflow `.github/workflows/forvium-watch.yml` uruchamia:
* testy na SQLite (Python 3.12 i 3.13),
* testy na PostgreSQL 16 oraz migracje jako `forvium_migrator` z `alembic check`,
* kontrolę składni JS i braku skryptów i stylów inline,
* budowę obrazu Docker.
