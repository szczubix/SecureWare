# Forvium Watch — Support Access

Bezpieczny dostęp serwisowy: operator Forvium może otworzyć panel klienta w jego
kontekście, w trybie **READ_ONLY**, za zgodą klienta, bez znajomości hasła i bez
przejmowania sesji użytkownika.

```
forvium-watch/
├── compose.yaml        całe środowisko lokalne: PostgreSQL, migracje, API, oba frontendy, Mailpit
├── backend/            wspólny backend FastAPI (api.forvium.com)
│   ├── forvium/
│   │   ├── identity/          Identity & Access – konta, sesje, MFA, limity prób
│   │   ├── organizations/     Organizations & RBAC – Permission, role, dane organizacji
│   │   ├── platform_admin/    Platform Administration – role operatorów, użytkownicy, zgłoszenia
│   │   ├── support_tickets/   Support Tickets – zgłoszenia, do których przypinany jest dostęp
│   │   ├── audit/             Audit Log – zdarzenia, middleware API, eksport, łańcuch skrótów
│   │   ├── notifications/     Notification Engine – powiadomienia w aplikacji + wysyłka e-mail
│   │   ├── support_access/    prośby, zgody (też stałe), sesje, zakresy, Break Glass, nadzór
│   │   └── access.py          jedno miejsce uwierzytelniania i autoryzacji (RBAC + RLS)
│   ├── migrations/            Alembic: 0001 schemat (+ trigger audytu), 0002 RLS i uprawnienia
│   └── tests/
├── deploy/             role PostgreSQL, konfiguracja nginx (nagłówki bezpieczeństwa, CSP)
└── frontend/
    ├── admin/          admin.forvium.com – użytkownicy, prośby, nadzór, audyt, Break Glass
    └── app/            app.forvium.com – zgody (też stałe), historia, powiadomienia, baner wsparcia
```

## Szybki start

```bash
cd forvium-watch
docker compose up --build
```

| Usługa | Adres |
|---|---|
| app (klient) | http://localhost:8001 |
| admin (operatorzy) | http://localhost:8002 |
| API | http://localhost:8000 (dokumentacja: `/docs`) |
| Mailpit (wysłane e-maile) | http://localhost:8025 |

Kontener `migrate` uruchamia migracje jako właściciel schematu i ładuje dane demo.
Hasło wszystkich kont to `Forvium-demo-2026!`, a sekrety TOTP do zeskanowania lub wpisania
w aplikacji uwierzytelniającej są w `docker compose logs migrate`.

| Konto | Rola |
|---|---|
| `alice@acme.example` | właścicielka organizacji Acme (zatwierdza dostęp) |
| `bob@acme.example` | członek Acme (użytkownik referencyjny) |
| `carol@beta.example` | właścicielka organizacji Beta |
| `ola@forvium.com` | Support L2 (prośby, Break Glass) |
| `piotr@forvium.com` | Support L1 (bez CVE) |
| `marta@forvium.com` | kierownik supportu (nadzór sesji, audyt) |
| `ewa@forvium.com`, `tomasz@forvium.com` | oficerowie bezpieczeństwa (zatwierdzanie i przegląd Break Glass) |

Break Glass jest domyślnie wyłączony. Żeby go włączyć lokalnie, uruchom
`FORVIUM_BREAK_GLASS_ENABLED=true docker compose up`.

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

## Break Glass

Dostęp awaryjny bez zgody klienta. Domyślnie jest **wyłączony**
(`FORVIUM_BREAK_GLASS_ENABLED=false`).

1. Operator z uprawnieniem `platform.break_glass.request` (Support L2 lub kierownik)
   składa wniosek. Wymagane są:
   * kategoria incydentu,
   * uzasadnienie (min. 200 znaków),
   * otwarte zgłoszenie,
   * czas sesji do 30 min,
   * kod MFA.
2. **Inny** oficer bezpieczeństwa zatwierdza wniosek własnym kodem MFA (4 oczy). Wniosek
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

Ograniczenie: MFA to TOTP. Klucze sprzętowe (WebAuthn) wymagają osobnej implementacji.

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
| `AUTO_CREATE_SCHEMA` | `false` | tylko eksperymenty; schemat tworzą migracje |

### Wdrożenie

1. Raz uruchom `deploy/postgres/roles.sql` jako superuser.
2. Przy każdym wdrożeniu, przed startem API, uruchom `alembic upgrade head` jako `forvium_migrator`.
3. Uruchom API jako `forvium_app`, za reverse proxy z TLS.
4. Frontendy serwuj przez nginx z `deploy/nginx/frontend.conf`.

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

Workflow `.github/workflows/forvium-watch.yml` uruchamia:
* testy na SQLite (Python 3.12 i 3.13),
* testy na PostgreSQL 16 oraz migracje jako `forvium_migrator` z `alembic check`,
* kontrolę składni JS i braku skryptów i stylów inline,
* budowę obrazu Docker.
