# Forvium Watch — Support Access

Bezpieczny dostęp serwisowy: operator Forvium może otworzyć panel klienta w jego
kontekście, w trybie **READ_ONLY**, za zgodą klienta, bez znajomości hasła i bez
przejmowania sesji użytkownika.

```
forvium-watch/
├── backend/            wspólny backend FastAPI (api.forvium.com)
│   ├── forvium/
│   │   ├── identity/          Identity & Access – konta, sesje, MFA, operacje na koncie
│   │   ├── organizations/     Organizations & RBAC – Permission, role, dane organizacji
│   │   ├── platform_admin/    Platform Administration – role operatorów, użytkownicy, audyt
│   │   ├── support_tickets/   Support Tickets – zgłoszenia, do których przypinany jest dostęp
│   │   ├── audit/             Audit Log – zdarzenia + middleware operacji API
│   │   ├── notifications/     Notification Engine – powiadomienia w aplikacji + kolejka e-mail
│   │   ├── support_access/    prośby, zgody, sesje wsparcia, zakresy, polityka, Break Glass
│   │   └── access.py          jedno miejsce uwierzytelniania i autoryzacji (RBAC)
│   └── tests/
└── frontend/
    ├── admin/          admin.forvium.com – Użytkownicy → Szczegóły → Dostęp serwisowy
    └── app/            app.forvium.com – zgody, historia dostępu, baner trybu wsparcia
```

## Przepływ

1. **Prośba** (`admin`) – operator wybiera organizację i użytkownika referencyjnego, podaje
   powód, numer otwartego zgłoszenia tej organizacji, czas (1–15 min, domyślnie 15) i zakres.
   Wymagana **ponowna weryfikacja MFA** (TOTP). Zatwierdzający po stronie klienta
   dostają powiadomienie w aplikacji i e-mail.
2. **Zgoda** (`app`) – właściciel lub administrator organizacji zatwierdza prośbę (może
   zawęzić zakres i jednostki oraz ustawić ważność zgody) albo ją odrzuca. Zgoda
   (`SupportConsent`) określa organizację, zakres, jednostki i termin ważności.
   Operator nie może zatwierdzić własnej prośby, nawet jeśli jest członkiem organizacji.
   Żadne konto operatorskie Forvium nie może zatwierdzać zgód.
3. **Sesja** (`admin` → `app`) – operator uruchamia sesję, ponownie przechodząc MFA. Backend
   tworzy osobny rekord `SupportSession` i jednorazowy kod startowy ważny 60 s. Panel
   admin otwiera `app.forvium.com/support-launch.html#code=…` w nowej karcie (`noopener`).
   Strona wymienia kod na token `fws_…`, trzymany tylko w `sessionStorage` tej karty.
4. **Każde żądanie** z tokenem `fws_` przechodzi pełną walidację
   (`support_access.service.validate_support_token`): status i czas sesji, zgoda (cofnięta
   lub wygasła), status prośby, aktywność operatora i jego uprawnienia platformowe,
   członkostwo użytkownika referencyjnego, istnienie organizacji, otwarte zgłoszenie.
   Uprawnienia są przeliczane na bieżąco.
5. **Zakończenie** – przycisk „Zakończ dostęp” na banerze, zakończenie z panelu admin,
   zakończenie lub cofnięcie zgody przez klienta, wygaśnięcie albo zamknięcie zgłoszenia.

## Model bezpieczeństwa

* **Brak osobnego systemu uprawnień.** Sesja wsparcia przechodzi przez tę samą zależność
  `require_org_permission(Permission.X)` co klient. Jej efektywne uprawnienia to:

  ```
  uprawnienia roli użytkownika referencyjnego
  ∩ uprawnienia zakresów zatwierdzonych w zgodzie
  ∩ zakresy dopuszczone dla roli platformowej operatora (np. L1 bez CVE)
  ∩ SUPPORT_READ_ONLY_PERMISSIONS
  − SUPPORT_FORBIDDEN_PERMISSIONS
  ```

  Twarda lista zakazów: ustawienia, role i członkostwa, usunięcie organizacji, eksport,
  płatności, subskrypcja, SMTP, webhooki, sekrety, tokeny API oraz zatwierdzanie zgód.
* **READ_ONLY na dwóch poziomach.** Każda metoda inna niż GET/HEAD/OPTIONS jest odrzucana
  dla tokenu `fws_`. Jedyny wyjątek to `POST /api/app/support/session/end`. Niezależnie od
  tego działa RBAC.
* **Operacje na koncie** (hasło, MFA, tokeny, powiadomienia klienta) używają
  `require_user_principal`, więc w trybie wsparcia zawsze dają 403.
* **Izolacja sesji.** Trzy rozłączne typy tokenów (`fwu_` klient, `fwo_` operator,
  `fws_` wsparcie), każdy weryfikowany we własnej tabeli. `/api/admin` przyjmuje tylko
  `fwo_`, a `/api/app` przyjmuje `fwu_` i `fws_`. Sesja wsparcia nie tworzy, nie zmienia
  i nie unieważnia sesji klienta ani operatora. W bazie trzymane są wyłącznie skróty
  SHA-256 tokenów.
* **Izolacja organizacji.** Token `fws_` działa tylko dla `organization_id` z sesji, a
  zgoda może dodatkowo zawęzić widoczne jednostki (wraz z poddrzewami).
* **Odczyt bez sekretów.** `config/status` zwraca tylko stan konfiguracji (czy SMTP jest
  skonfigurowany, liczba webhooków), bez hostów, haseł, URL-i i kluczy.
* **Historia jest jawna.** Prośby, zgody i sesje nie mają operacji usuwania ani ukrywania.
  Klient widzi pełną historię i aktywność każdej sesji (metoda i trasa każdego żądania).

## Audyt

| Zdarzenie | Akcja |
|---|---|
| utworzenie prośby | `support.request.created` |
| akceptacja / odrzucenie | `support.request.approved` / `support.request.rejected` |
| rozpoczęcie / zakończenie sesji | `support.session.started`, `support.session.launched` / `support.session.ended` |
| każda operacja API w trybie wsparcia | `support.api_call` (metoda, szablon trasy, kod HTTP) |
| cofnięcie zgody | `support.consent.revoked` + `support.session.revoked` |
| automatyczne wygaśnięcie | `support.session.expired`, `support.request.expired` |
| nieudane próby | `support.access_denied`, `support.*.create/approve/start` z `outcome=denied` |

Każdy wpis ma `actor_user_id` (operator) i `on_behalf_of_user_id` (użytkownik
referencyjny), a do tego `organization_id`, `support_session_id` i `support_request_id`.

* Zdarzenia udanych operacji zapisują się w tej samej transakcji co zmiana (`AuditLog.log`).
* Odmowy i operacje API zapisują się we własnej transakcji (`AuditLog.record`), więc
  przetrwają rollback.
* Do logu nie trafia treść żądań ani odpowiedzi. Szczegóły przechodzą przez `sanitize`,
  który maskuje klucze typu password, token, secret, mfa, smtp, webhook.

## Break Glass

Nie jest aktywny. Model przewiduje `AccessMode.BREAK_GLASS`, a
`support_access/break_glass.py` definiuje osobną politykę: `enabled=False`, wymagane
uzasadnienie, drugi zatwierdzający, sprzętowe MFA, limit czasu, powiadomienie zespołu
bezpieczeństwa i niezależny sink audytu. Prośby w tym trybie są odrzucane
(`break_glass_disabled`), a uprawnienia `platform.break_glass` nie ma żadna rola.

## Uruchomienie (dev)

```bash
cd backend
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
export FORVIUM_DATABASE_URL=sqlite:///./forvium.db \
       FORVIUM_APP_ORIGIN=http://localhost:8001 FORVIUM_ADMIN_ORIGIN=http://localhost:8002
python -m forvium.seed                 # konta demo i sekrety TOTP
uvicorn forvium.asgi:app --port 8000
# w osobnych terminalach (ustaw window.FORVIUM_API w config.js na http://localhost:8000):
python -m http.server 8001 -d ../frontend/app
python -m http.server 8002 -d ../frontend/admin
```

W produkcji `FORVIUM_DATABASE_URL` wskazuje PostgreSQL
(`postgresql+psycopg://…`). Funkcję `support_access.service.sweep_expired` należy
uruchamiać cyklicznie, np. co minutę, żeby wygasłe sesje zmieniały status także wtedy,
gdy nikt ich nie używa. Dostęp i tak jest blokowany przy każdym żądaniu.

## Testy

```bash
cd backend && pytest
```

`tests/test_support_access.py` pokrywa 10 obowiązkowych scenariuszy (`test_01` … `test_10`)
oraz przypadki dodatkowe:

* wymóg MFA,
* limit 15 min,
* jednorazowy kod startowy,
* zawężenie jednostek,
* limit zakresu operatora L1,
* blokada odczytu sekretów,
* powiadomienia,
* zamknięcie zgłoszenia,
* zakończenie sesji przez klienta,
* Break Glass.
