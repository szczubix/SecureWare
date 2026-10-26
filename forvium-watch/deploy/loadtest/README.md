# Testy obciążeniowe (k6)

## Uruchomienie

```bash
cd forvium-watch
docker compose up -d --build                      # stos z danymi demo
python deploy/loadtest/prepare.py http://localhost:8080 > /tmp/lt/tokens.json   # wymaga pyotp
docker run --rm --network forvium-watch_edge \
  -v "$PWD/deploy/loadtest:/scripts:ro" -v /tmp/lt:/data:ro \
  -e RATE=150 -e DURATION=60s grafana/k6:0.54.0 run /scripts/forvium.js
```

`prepare.py` loguje 4 klientów i kierownika supportu (przez gateway), a potem tworzy
prawdziwą sesję wsparcia: prośbę, zgodę klienta, start i wymianę kodu na token. Sesja
trwa do 15 minut, więc przed kolejną serią przygotuj tokeny od nowa.

k6 wysyła żądania **bezpośrednio do replik API** w sieci Dockera (`http://api:8000`, DNS
round-robin). Gateway ma limity na adres IP, a cały ruch generatora wychodzi z jednego
adresu. Scenariusze o stałym tempie (`constant-arrival-rate`; liczba żądań/s nie spada,
gdy serwer zwalnia):

| Scenariusz | Udział | Żądania |
|---|---|---|
| `customers` | 70% | dashboard, CVE, jednostki, technologie, błędy, zgłoszenia, historia dostępu, powiadomienia |
| `support` | 15% | operator w sesji wsparcia: walidacja sesji, uprawnień i zgody przy każdym żądaniu, RLS, **wpis audytu** |
| `operators` | 15% | panel admin: prośby, audyt, zgłoszenia |

Progi: błędy < 1%, p95 < 300 ms (klienci) / 500 ms (sesja wsparcia, admin).

## Wyniki (26.10.2026)

Środowisko: jedna maszyna, 4 vCPU, 15 GB RAM. Na tej samej maszynie działał cały stos
(2 repliki API, PostgreSQL 16, worker, gateway) **i generator k6**. Na serwerze tylko
z aplikacją wyniki będą lepsze.

| API (repliki × procesy) | Tempo | p95 klienci | p95 sesja wsparcia | Błędy | Uwagi |
|---|---|---|---|---|---|
| 2 × 1 | 100 req/s | 30 ms | 46 ms | 0% | API ~85% CPU na replikę, baza 25% |
| 2 × 1 | 150 req/s | 52 ms | 63 ms | 0% | |
| 2 × 1 | 200 req/s | 4,0 s | 4,1 s | 0% | nasycenie: ~170 req/s, nadmiar czeka w kolejce |
| 2 × 2 | 200 req/s | 286 ms | 307 ms | 0% | 4 procesy API + baza + k6 na 4 rdzeniach |
| 2 × 2 | 250 req/s | 473 ms | 541 ms | 0% | baza ~1 CPU (wpisy audytu sesji wsparcia) |
| 2 × 2 | 300 req/s | 2,4 s | 2,5 s | 0% | nasycenie: ~276 req/s |

Wnioski:

* **Ograniczeniem jest procesor.** Jeden proces API obsługuje ~85 req/s tego miksu, a
  PostgreSQL około 250 req/s na jeden rdzeń. Najdroższa jest sesja wsparcia: każde żądanie
  dodaje wpis audytu.
* **Procesów nie dawaj więcej niż rdzeni** przeznaczonych dla API. Na 4 rdzeniach dzielonych z
  bazą 2 × 2 daje wyższą przepustowość, ale gorsze opóźnienia przy umiarkowanym ruchu niż 2 × 1.
* **Przy przeciążeniu nie ma błędów ani zawieszeń.** Żądania czekają w kolejce
  (`core/concurrency.py`), a po 15 s dostają `503` z `Retry-After`.

### Błąd znaleziony testem i naprawiony

Pierwsza seria przy 200 req/s **zawiesiła API na stałe**. Throughput spadł do zera, CPU też,
a healthcheck zgłaszał `unhealthy`. Przyczyny:

1. Wpisy audytu, limity prób i wyzwania WebAuthn brały drugie połączenie z tej samej puli
   co transakcja żądania.
2. Zależności FastAPI pobierały połączenie w wątku, a potem czekały na kolejny wątek, podczas
   gdy wszystkie wątki czekały na połączenie z wyczerpanej puli.

Naprawa:

* **Osobna pula pomocnicza** na zapisy w niezależnych transakcjach (`core/db.py`).
* **Limit jednoczesnych żądań na proces** równy rozmiarowi głównej puli
  (`core/concurrency.py`): nadmiar czeka bez trzymania połączenia.
* **`/healthz` bez puli wątków**, a rozmiary pul są konfigurowalne.

## Zalecenia sprzętowe

Założenie: aktywny użytkownik panelu wykonuje ~0,3–0,5 req/s (widok to 3–6 wywołań API co
10–20 s). 150 req/s to więc około 300–500 jednocześnie aktywnych użytkowników.

| Skala | Serwer | Konfiguracja | Oczekiwana pojemność |
|---|---|---|---|
| Mała (do ~30 organizacji, do ~300 aktywnych) | 4 vCPU, 8 GB RAM, SSD | `FORVIUM_API_REPLICAS=2`, `FORVIUM_API_WORKERS=1` | ~150 req/s przy p95 < 60 ms (zmierzone) |
| Średnia (do ~150 organizacji) | 8 vCPU, 16 GB RAM | `FORVIUM_API_REPLICAS=2`, `FORVIUM_API_WORKERS=3` | ~400 req/s (szacunek: ~85 req/s na proces, baza na 2 rdzeniach) |
| Duża | baza na osobnym serwerze (4–8 vCPU, szybki SSD), 2+ serwery aplikacji za load balancerem | repliki API na każdym serwerze aplikacji | skaluje się liniowo z procesami API, aż do limitu bazy |

Połączenia z bazą: każdy proces API otwiera do `DB_POOL_SIZE + DB_MAX_OVERFLOW`
(domyślnie 20) połączeń w puli głównej i do `2 × DB_AUX_POOL_SIZE` (10) w pomocniczej.
`max_connections` PostgreSQL (w compose: 200) musi zmieścić:
- `repliki × procesy × 30`,
- workera (~30),
- kopie zapasowe.

Limity bramy na adres IP (`FORVIUM_RATE_API`, domyślnie 50 req/s z buforem 100;
`FORVIUM_RATE_AUTH` dla logowania, 10/min) chronią przed nadużyciem z jednego adresu.
Duży klient za NAT-em (wielu użytkowników z jednego IP) może potrzebować wyższego
`FORVIUM_RATE_API`.
