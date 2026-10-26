# Audit Log → SIEM (Splunk, Elastic, Wazuh)

Zadanie `audit-export` w kontenerze `worker` co `FORVIUM_AUDIT_EXPORT_INTERVAL_SECONDS` (30 s)
wysyła nowe zdarzenia audytu do skonfigurowanych miejsc:
- plik z łańcuchem skrótów,
- własny endpoint HTTP,
- SIEM.

Zdarzenie jest oznaczane jako wyeksportowane dopiero, gdy przyjmą je **wszystkie** miejsca.
Przy awarii SIEM partia zostanie wysłana ponownie, a w panelu (Alerty → Zadania w tle) i w
`/metrics` widać, że eksport stoi.

Każde zdarzenie jest mapowane na **Elastic Common Schema (ECS 8.11)**. Ten sam dokument trafia
do wszystkich trzech systemów:

| Pole ECS | Znaczenie |
|---|---|
| `@timestamp`, `event.id` | czas i stały identyfikator zdarzenia (deduplikacja) |
| `event.action` | np. `support.session.started`, `identity.login.operator`, `platform.operator.role_changed` |
| `event.outcome` | `success` / `failure` (odmowa); oryginał w `forvium.outcome` |
| `event.category` | `authentication`, `iam`, `session`, `configuration`, `intrusion_detection`, `process` |
| `user.id`, `user.target.id` | kto działał (np. operator w sesji wsparcia) i w czyim imieniu (użytkownik referencyjny) |
| `organization.id`, `source.ip`, `url.path`, `http.*` | kontekst |
| `forvium.support.session_id` / `request_id` | sesja i prośba o dostęp serwisowy |
| `labels.forvium_break_glass`, `tags: ["break_glass"]` | procedura awaryjna |
| `forvium.details` | szczegóły zdarzenia (bez treści żądań, tokenów i sekretów) |

Konfiguracja (`.env`, sekcja „Audyt”):

```
FORVIUM_AUDIT_SIEM_TYPE=splunk | elastic | syslog
FORVIUM_AUDIT_SIEM_URL=...
FORVIUM_AUDIT_SIEM_TOKEN=...          # Splunk / Elastic
FORVIUM_AUDIT_SIEM_INDEX=...          # opcjonalnie
FORVIUM_AUDIT_SIEM_CA_FILE=/etc/forvium/siem-ca.pem   # własne CA (opcjonalnie)
```

Certyfikat TLS odbiorcy jest zawsze weryfikowany (TLS ≥ 1.2, nazwa hosta). Nie ma opcji
wyłączenia weryfikacji. Dla wewnętrznego CA zamontuj plik w `compose.site.yaml`, w usłudze
`worker`: `/etc/forvium-watch/siem-ca.pem:/etc/forvium/siem-ca.pem:ro`, i ustaw
`FORVIUM_AUDIT_SIEM_CA_FILE`.

---

## Elastic (Elasticsearch / Elastic Cloud)

Zdarzenia trafiają przez Bulk API do data streamu `logs-forvium.audit-default`, z `_id`
równym `event.id` (operacja `create`). Ponowienie partii nie tworzy duplikatów, bo
odpowiedź `409` jest traktowana jako „już jest”. Wbudowany szablon `logs-*-*` mapuje pola
ECS: `source.ip` jako `ip`, `@timestamp` jako `date`, `event.action` jako `keyword`.

Klucz API z minimalnymi uprawnieniami (Kibana → Dev Tools):

```
POST /_security/api_key
{
  "name": "forvium-watch",
  "role_descriptors": {
    "forvium_writer": {
      "indices": [{ "names": ["logs-forvium.audit-*"], "privileges": ["create_doc", "auto_configure"] }]
    }
  }
}
```

```
FORVIUM_AUDIT_SIEM_TYPE=elastic
FORVIUM_AUDIT_SIEM_URL=https://elastic.example.com:9200
FORVIUM_AUDIT_SIEM_TOKEN=<pole "encoded" z odpowiedzi>
```

Przykładowe zapytania (KQL):

* `data_stream.dataset : "forvium.audit" and tags : "break_glass"`: procedura awaryjna,
* `event.action : "support.api_call" and event.outcome : "failure"`: sesja wsparcia próbowała
  wyjść poza zgodę,
* `event.category : "authentication" and event.outcome : "failure"`: nieudane logowania.

Sprawdzone na Elasticsearch 8.15 z włączonym bezpieczeństwem:
- HTTPS z CA wygenerowanym przez Elasticsearch,
- klucz API powyżej,
- deduplikacja ponowionej partii,
- mapowanie pól.

## Splunk (HTTP Event Collector)

1. Settings → Data inputs → HTTP Event Collector → New Token. Ustaw indeks (np. `forvium`)
   i źródło `forvium:audit:ecs`. Włącz HEC (Global Settings), port 8088 z SSL.
2. `props.conf` (aplikacja na indeksatorze / search headzie):

   ```
   [forvium:audit:ecs]
   KV_MODE = json
   TIME_PREFIX = "@timestamp":"
   TIME_FORMAT = %Y-%m-%dT%H:%M:%S.%6N%Z
   SHOULD_LINEMERGE = false
   ```

3. Konfiguracja:

   ```
   FORVIUM_AUDIT_SIEM_TYPE=splunk
   FORVIUM_AUDIT_SIEM_URL=https://splunk.example.com:8088
   FORVIUM_AUDIT_SIEM_TOKEN=<token HEC>
   FORVIUM_AUDIT_SIEM_INDEX=forvium
   ```

Zdarzenia trafiają do `/services/collector/event` z polem `time` z `@timestamp`. Przykład
wyszukiwania: `index=forvium sourcetype="forvium:audit:ecs" tags{}=break_glass`.
Integrację przetestowano na odbiorniku zgodnym z protokołem HEC, nie na instancji Splunk.

## Wazuh (syslog → remoted)

Wazuh odbiera zdarzenia jako syslog RFC 5424 przez TCP, z treścią JSON (ECS). Dekoder i
reguły są w tym katalogu.

1. Na managerze, w `/var/ossec/etc/ossec.conf`:

   ```xml
   <remote>
     <connection>syslog</connection>
     <port>514</port>
     <protocol>tcp</protocol>
     <allowed-ips>ADRES_SERWERA_FORVIUM/32</allowed-ips>
   </remote>
   ```

2. Skopiuj `wazuh/forvium_decoders.xml` → `/var/ossec/etc/decoders/` i
   `wazuh/forvium_rules.xml` → `/var/ossec/etc/rules/` (właściciel `wazuh:wazuh`), potem
   `systemctl restart wazuh-manager`.
3. Konfiguracja Forvium (Wazuh remoted oczekuje wiadomości rozdzielonych znakiem nowej linii):

   ```
   FORVIUM_AUDIT_SIEM_TYPE=syslog
   FORVIUM_AUDIT_SIEM_URL=tcp://wazuh.example.com:514?framing=lf
   ```

Wazuh remoted nie obsługuje TLS dla syslog. Kanał zabezpiecz siecią prywatną lub VPN
między serwerem Forvium a managerem. Inna możliwość to rsyslog z TLS przed Wazuh: wtedy
`tls://host:6514` z domyślnym ramkowaniem `octet`.

Reguły (`100700–100708`):

| ID | Poziom | Kiedy |
|---|---|---|
| 100700 | 3 | każde zdarzenie Forvium Watch |
| 100701 | 5 | odmowa (`event.outcome = failure`) |
| 100702 | 5 | nieudane uwierzytelnienie |
| 100703 | 10 | 5 nieudanych uwierzytelnień z jednego adresu w 2 min |
| 100704 | 6 | rozpoczęto sesję wsparcia |
| 100705 | 12 | dowolne zdarzenie procedury Break Glass |
| 100706 | 10 | alert bezpieczeństwa wykrywania anomalii |
| 100707 | 8 | zmiana roli lub blokada operatora, blokada lub reset dostępu klienta |
| 100708 | 7 | sesja wsparcia próbowała operacji poza zgodą |

Sprawdzone na Wazuh 4.9.2:
- `wazuh-logtest` przechodzi dla wszystkich typów zdarzeń,
- wysyłka przez sieć do `remoted` (TCP, `framing=lf`) tworzy alerty w `alerts.json`.

## Inny SIEM (rsyslog, syslog-ng, QRadar, Sentinel przez AMA)

`FORVIUM_AUDIT_SIEM_TYPE=syslog` z `tls://host:6514` (RFC 5425, ramkowanie octet-counting)
albo `tcp://host:514`. Facility `local4`, poziom `notice` (sukces) albo `warning` (odmowa,
Break Glass). Treść to jeden dokument JSON (ECS) w linii.
