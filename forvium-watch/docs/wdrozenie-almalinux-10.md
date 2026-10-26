# Wdrożenie Forvium Watch na AlmaLinux 10

Instrukcja opisuje produkcyjną instalację na jednym serwerze z AlmaLinux 10 (x86_64):
Docker CE z oficjalnego repozytorium, SELinux w trybie *enforcing*, firewalld, TLS z
Let's Encrypt, start przez systemd, zaszyfrowane kopie zapasowe poza serwerem i monitoring.

Nazwy pakietów i repozytoriów sprawdzono na AlmaLinux 10.2:
- `docker-ce` 29.9 i `docker-compose-plugin` 5.6 z repozytorium Dockera dla RHEL,
- `certbot`, `age`, `rclone`, `fail2ban` z EPEL.

Konfigurację produkcyjną (`compose.prod.yaml`) przetestowano z TLS, w trybie pierwszego
uruchomienia. Kroki z SELinux (`semanage`, `restorecon`) wymagają prawdziwego hosta.
Po instalacji sprawdź `ausearch -m avc -ts recent` (sekcja 14).

---

## Spis treści

1. [Architektura](#1-architektura)
2. [Wymagania](#2-wymagania)
3. [Przygotowanie systemu](#3-przygotowanie-systemu)
4. [Docker CE](#4-docker-ce)
5. [Pobranie aplikacji](#5-pobranie-aplikacji)
6. [Konfiguracja i sekrety](#6-konfiguracja-i-sekrety)
7. [SELinux](#7-selinux)
8. [TLS (Let's Encrypt)](#8-tls-lets-encrypt)
9. [Uruchomienie i start z systemem](#9-uruchomienie-i-start-z-systemem)
10. [Pierwsze konta](#10-pierwsze-konta)
11. [Kopie zapasowe](#11-kopie-zapasowe)
12. [Monitoring](#12-monitoring)
13. [Aktualizacje i rotacja kluczy](#13-aktualizacje-i-rotacja-kluczy)
14. [Rozwiązywanie problemów](#14-rozwiązywanie-problemów)
15. [Lista kontrolna przed startem](#15-lista-kontrolna-przed-startem)

---

## 1. Architektura

```
Internet ──443/80──▶ gateway (nginx, TLS, HSTS, limity zapytań, lista adresów panelu admin)
                       ├── app.<domena>   ─▶ app   (panel klienta, statyczny, CSP)
                       ├── admin.<domena> ─▶ admin (panel operatorów, statyczny, CSP)
                       └── api.<domena>   ─▶ api × 2 (FastAPI, bez zadań w tle)
                                               │
              sieć "backend" (bez portów na zewnątrz)
                       ├── db       PostgreSQL 16 (RLS, osobne role)
                       ├── worker   zadania w tle (wygaszanie sesji, e-mail, anomalie, eksport audytu, raporty)
                       ├── backup   zaszyfrowane kopie (age), retencja, test odtwarzania
                       └── prometheus / alertmanager / grafana (opcjonalnie, profil "monitoring")
```

Na zewnątrz publikowane są tylko porty 80 i 443 bramy. Prometheus i Grafana nasłuchują
wyłącznie na `127.0.0.1`.

## 2. Wymagania

| Element | Minimum | Zalecane |
|---|---|---|
| Serwer | 2 vCPU, 4 GB RAM | 4 vCPU, 8 GB RAM |
| Dysk | 40 GB SSD | 80 GB SSD + osobny wolumen na `/var/lib/docker` |
| System | AlmaLinux 10 (instalacja minimalna) | |
| DNS | rekordy A/AAAA: `app.`, `admin.`, `api.` `<domena>` → adres serwera | |
| Poczta | serwer SMTP (powiadomienia, linki aktywacyjne) z SPF/DKIM dla nadawcy | |
| Kopie | zdalny magazyn obsługiwany przez rclone (S3, SFTP, Azure Blob, B2…) | magazyn z blokadą usuwania (object lock / WORM) |
| Stacja administratora | `age` (generowanie klucza głównego kopii) | sejf na klucz prywatny |

Dobór serwera i liczby procesów API (wyniki testów obciążeniowych):
[deploy/loadtest/README.md](../deploy/loadtest/README.md). W skrócie: 4 vCPU obsłużą
~150 req/s, czyli ok. 300–500 aktywnych użytkowników, przy p95 < 60 ms
(`FORVIUM_API_WORKERS=1`). Przy 8 vCPU ustaw `FORVIUM_API_WORKERS=3`.

Przykłady poniżej używają domeny `forvium.example.com`. Polecenia wykonuj jako root
(albo przez `sudo`).

## 3. Przygotowanie systemu

```bash
dnf -y upgrade
hostnamectl set-hostname watch.forvium.example.com
timedatectl set-timezone Europe/Warsaw
systemctl enable --now chronyd

# Narzędzia: SELinux, firewall, automatyczne poprawki bezpieczeństwa, git
dnf -y install policycoreutils-python-utils firewalld dnf-automatic git
dnf -y install epel-release
dnf -y install certbot age rclone

# SELinux musi zostać w trybie enforcing
getenforce            # Enforcing
```

**SSH:** logowanie wyłącznie kluczem, bez roota.

```bash
cat > /etc/ssh/sshd_config.d/50-forvium.conf <<'EOF'
PermitRootLogin no
PasswordAuthentication no
KbdInteractiveAuthentication no
EOF
systemctl reload sshd
```

**Automatyczne poprawki bezpieczeństwa** (bez automatycznego restartu):

```bash
sed -i 's/^upgrade_type.*/upgrade_type = security/; s/^apply_updates.*/apply_updates = yes/' /etc/dnf/automatic.conf
systemctl enable --now dnf-automatic.timer
```

**Firewall:** z internetu tylko SSH, HTTP i HTTPS.

```bash
systemctl enable --now firewalld
firewall-cmd --permanent --add-service=ssh --add-service=http --add-service=https
firewall-cmd --reload
```

> Docker publikuje porty kontenerów własnymi regułami nftables, z pominięciem reguł
> firewalld. Dlatego `compose.prod.yaml` publikuje wyłącznie 80/443, a narzędzia
> monitoringu tylko na `127.0.0.1`. Nie dodawaj innych sekcji `ports:`.

**Opcjonalnie fail2ban dla SSH:**

```bash
dnf -y install fail2ban
cat > /etc/fail2ban/jail.d/sshd.local <<'EOF'
[sshd]
enabled = true
backend = systemd
EOF
systemctl enable --now fail2ban
```

**Retencja dziennika:** logi wszystkich kontenerów trafiają do journald.

```bash
mkdir -p /etc/systemd/journald.conf.d
cat > /etc/systemd/journald.conf.d/forvium.conf <<'EOF'
[Journal]
Storage=persistent
SystemMaxUse=4G
MaxRetentionSec=90day
EOF
systemctl restart systemd-journald
```

## 4. Docker CE

AlmaLinux 10 korzysta z repozytorium Dockera dla RHEL.

```bash
dnf config-manager --add-repo https://download.docker.com/linux/rhel/docker-ce.repo
dnf -y install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin container-selinux

mkdir -p /etc/docker
cat > /etc/docker/daemon.json <<'EOF'
{
  "selinux-enabled": true,
  "log-driver": "journald",
  "live-restore": true
}
EOF
systemctl enable --now docker
docker compose version    # Docker Compose 5.x (wymagane >= 2.24 - składnia !override)
```

* `selinux-enabled`: kontenery dostają etykiety SELinux (`container_t`), więc proces
  w kontenerze nie czyta dowolnych plików hosta.
* `live-restore`: restart demona Dockera, np. przy aktualizacji, nie zatrzymuje kontenerów.

## 5. Pobranie aplikacji

Kod trzymaj w `/opt/src`, a katalog roboczy podlinkuj jako `/opt/forvium-watch`. Na tę
ścieżkę wskazują jednostka systemd i hook certbota.

```bash
mkdir -p /opt/src
git clone https://github.com/szczubix/SecureWare.git /opt/src/secureware
cd /opt/src/secureware
git checkout <tag-wydania>          # zawsze konkretny tag/commit, nie gałąź robocza
ln -s /opt/src/secureware/forvium-watch /opt/forvium-watch
```

> Jeśli projekt trafi do osobnego repozytorium, zmienia się tylko ścieżka klonowania.
> Dalej `/opt/forvium-watch` wskazuje katalog z `compose.yaml`.

## 6. Konfiguracja i sekrety

### 6.1 Katalog konfiguracji hosta

```bash
install -d -m 700 /etc/forvium-watch /etc/forvium-watch/tls
install -d -m 755 /var/www/acme

# Lista adresów, z których wolno otworzyć panel operatorów (admin.<domena>)
cp /opt/forvium-watch/deploy/gateway/admin-allow.conf.example /etc/forvium-watch/admin-allow.conf
vi /etc/forvium-watch/admin-allow.conf     # wpisz sieć biura / VPN, na końcu "deny all;"
```

### 6.2 Klucz główny kopii zapasowych (na stacji administratora, NIE na serwerze)

```bash
age-keygen -o forvium-backup-master.key
# Public key: age1....   <- wpiszesz go do .env jako BACKUP_AGE_RECIPIENT
```

Plik `forvium-backup-master.key` przechowuj offline (sejf, menedżer sekretów, wydruk w
kopercie) w co najmniej dwóch miejscach. Bez niego nie odtworzysz kopii po utracie serwera.

### 6.3 Plik `.env`

```bash
cd /opt/forvium-watch
cp .env.prod.example .env
chown root:root .env && chmod 600 .env

gen() { openssl rand -base64 32 | tr -d '/+=' | cut -c1-32; }
sed -i "s|^FORVIUM_POSTGRES_PASSWORD=.*|FORVIUM_POSTGRES_PASSWORD=$(gen)|" .env
sed -i "s|^FORVIUM_MIGRATOR_PASSWORD=.*|FORVIUM_MIGRATOR_PASSWORD=$(gen)|" .env
sed -i "s|^FORVIUM_APP_PASSWORD=.*|FORVIUM_APP_PASSWORD=$(gen)|" .env
sed -i "s|^FORVIUM_BACKUP_PASSWORD=.*|FORVIUM_BACKUP_PASSWORD=$(gen)|" .env
sed -i "s|^FORVIUM_RESTORE_PASSWORD=.*|FORVIUM_RESTORE_PASSWORD=$(gen)|" .env
sed -i "s|^FORVIUM_AUDIT_EXPORT_HMAC_KEY=.*|FORVIUM_AUDIT_EXPORT_HMAC_KEY=$(gen)|" .env
# Klucz danych (AES-256): identyfikator:klucz_base64
sed -i "s|^FORVIUM_DATA_KEYS=.*|FORVIUM_DATA_KEYS=k$(date +%Y%m):$(openssl rand -base64 32)|" .env
sed -i "s|^FORVIUM_DATA_KEY_ID=.*|FORVIUM_DATA_KEY_ID=k$(date +%Y%m)|" .env
vi .env   # domena, SMTP, adresy zespołu bezpieczeństwa, BACKUP_AGE_RECIPIENT, hasło Grafany
```

Co uzupełnić ręcznie:

| Zmienna | Opis |
|---|---|
| `FORVIUM_DOMAIN` | np. `forvium.example.com`: panele `app.`/`admin.`, API `api.` |
| `FORVIUM_SMTP_*` | serwer pocztowy. Bez działającej poczty nikt nie dostanie linku aktywacyjnego |
| `FORVIUM_SECURITY_TEAM_EMAILS` | odbiorcy alertów (Break Glass, anomalie) |
| `BACKUP_AGE_RECIPIENT` | klucz publiczny z punktu 6.2 |
| `FORVIUM_OPERATOR_LOGIN_WEBAUTHN_ONLY` | `true` (domyślnie): operator z kluczem bezpieczeństwa loguje się tylko kluczem |
| `FORVIUM_BREAK_GLASS_ENABLED` | `false`, dopóki procedura awaryjna nie zostanie formalnie przyjęta |
| `FORVIUM_AUDIT_SIEM_*` | opcjonalnie wysyłka audytu do Splunk / Elastic / Wazuh: `deploy/siem/README.md` |
| `FORVIUM_API_WORKERS`, `FORVIUM_RATE_API` | procesy uvicorn na replikę i limit bramy na adres IP: `deploy/loadtest/README.md` |
| `COMPOSE_PROFILES` | `monitoring`, jeśli uruchamiasz Prometheus/Grafanę na tym serwerze |

**Klucze danych:** `FORVIUM_DATA_KEYS` szyfruje w bazie sekrety MFA, sekrety organizacji,
nagrania sesji i raporty. Utrata klucza oznacza utratę tych danych, więc zapisz kopię klucza
razem z kluczem głównym kopii. Zalecany wariant to klucze opakowane w Vault Transit
(`FORVIUM_DATA_KEYS_WRAPPED`, `FORVIUM_VAULT_ADDR`, `FORVIUM_VAULT_TOKEN`). Wtedy w `.env`
nie ma jawnego klucza.

Sprawdzenie konfiguracji (brak zmiennej wymaganej = błąd z opisem):

```bash
docker compose -f compose.yaml -f compose.prod.yaml config -q && echo OK
```

## 7. SELinux

Kontenery z etykietą `container_t` czytają tylko pliki z typem `container_file_t`. Nadaj go
trwale katalogom montowanym do kontenerów (pliki konfiguracyjne tylko do odczytu):

```bash
semanage fcontext -a -t container_file_t "/opt/src/secureware/forvium-watch/deploy/postgres(/.*)?"
semanage fcontext -a -t container_file_t "/opt/src/secureware/forvium-watch/deploy/gateway(/.*)?"
semanage fcontext -a -t container_file_t "/opt/src/secureware/forvium-watch/deploy/monitoring(/.*)?"
semanage fcontext -a -t container_file_t "/etc/forvium-watch(/.*)?"
semanage fcontext -a -t container_file_t "/var/www/acme(/.*)?"
restorecon -Rv /opt/src/secureware/forvium-watch/deploy /etc/forvium-watch /var/www/acme
```

Reguły `semanage fcontext` przetrwają `restorecon`, aktualizację kodu i relabel systemu.
Nie wyłączaj SELinux. Jeśli coś jest blokowane, zobacz sekcję 14.

## 8. TLS (Let's Encrypt)

Brama potrzebuje certyfikatu, żeby wystartować. Certbot w trybie *webroot* potrzebuje z
kolei działającej bramy na porcie 80. Dlatego najpierw zakładasz tymczasowy certyfikat
self-signed, potem pobierasz właściwy.

```bash
D=forvium.example.com

# 1) Tymczasowy certyfikat (tylko do pierwszego startu)
openssl req -x509 -newkey rsa:2048 -nodes -days 7 -subj "/CN=$D" \
  -addext "subjectAltName=DNS:app.$D,DNS:admin.$D,DNS:api.$D" \
  -keyout /etc/forvium-watch/tls/privkey.pem -out /etc/forvium-watch/tls/fullchain.pem
chmod 600 /etc/forvium-watch/tls/privkey.pem
restorecon -Rv /etc/forvium-watch

# 2) Uruchom stos poleceniami z sekcji 9, potem pobierz właściwy certyfikat dla trzech nazw
certbot certonly --webroot -w /var/www/acme --cert-name forvium-watch \
  -d app.$D -d admin.$D -d api.$D \
  --email security@$D --agree-tos --no-eff-email

# 3) Hook: kopiuje certyfikat do /etc/forvium-watch/tls i przeładowuje nginx (bez przerwy)
install -m 755 /opt/forvium-watch/deploy/tls/certbot-deploy-hook.sh \
  /etc/letsencrypt/renewal-hooks/deploy/forvium-watch.sh
/etc/letsencrypt/renewal-hooks/deploy/forvium-watch.sh      # pierwsze użycie ręcznie

# 4) Automatyczne odnawianie (timer z pakietu certbot, 2× dziennie)
systemctl enable --now certbot-renew.timer
certbot renew --dry-run
```

Kontrola:

```bash
curl -sI https://app.$D | grep -i strict-transport-security
curl -s https://api.$D/healthz        # {"ok":true}
curl -s -o /dev/null -w '%{http_code}\n' https://api.$D/metrics   # 404 (tylko wewnętrznie)
```

Brama obsługuje TLS 1.2 i 1.3 oraz HTTP/2, wysyła HSTS (2 lata), przekierowuje HTTP na
HTTPS i odrzuca połączenia z nieznaną nazwą hosta (SNI).

## 9. Uruchomienie i start z systemem

```bash
cd /opt/forvium-watch
docker compose -f compose.yaml -f compose.prod.yaml build
docker compose -f compose.yaml -f compose.prod.yaml up -d

# Start po restarcie serwera
install -m 644 deploy/systemd/forvium-watch.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable forvium-watch.service
```

Kontener `migrate` przy każdym starcie wykonuje migracje bazy (`alembic upgrade head`) i
przeszyfrowuje dane aktywnym kluczem, a dopiero potem startują `api` i `worker`. Danych
demonstracyjnych w produkcji nie ma (`SEED_DEMO=false`).

Stan:

```bash
docker compose -f compose.yaml -f compose.prod.yaml ps
# api ×2, worker, backup: (healthy); gateway, app, admin: Up; migrate: Exited (0)

journalctl -t forvium/forvium-watch-api-1 -f        # logi JSON jednej repliki API
journalctl -t forvium/forvium-watch-worker-1 --since -1h
```

## 10. Pierwsze konta

Na świeżej instalacji nie ma żadnego operatora. Pierwszego administratora platformy i
pierwszego oficera bezpieczeństwa (zatwierdza role uprzywilejowane i Break Glass) tworzy
polecenie `bootstrap`. Działa tylko, gdy nie istnieje jeszcze niezablokowane konto z daną
rolą.

```bash
cd /opt/forvium-watch
C="docker compose -f compose.yaml -f compose.prod.yaml"
$C run --rm -T migrate python -m forvium.platform_admin.bootstrap \
  --email jan.admin@forvium.example.com --name "Jan Kowalski" --role platform_admin
$C run --rm -T migrate python -m forvium.platform_admin.bootstrap \
  --email ewa.security@forvium.example.com --name "Ewa Nowak" --role security_officer
```

Każda osoba dostaje e-mailem jednorazowy link (`https://admin.<domena>/activate.html#token=…`,
ważny 72 h). Link jest też wypisany w konsoli, na wypadek gdyby poczta jeszcze nie działała.
Przekaż go właściwej osobie bezpiecznym kanałem. Osoba sama ustawia hasło i aplikację
uwierzytelniającą, potem w panelu (zakładka **Konto**) dodaje klucz bezpieczeństwa.
Od tej chwili loguje się wyłącznie kluczem.

Dalej wszystko odbywa się w panelu admin:

* **Operatorzy:** kolejne osoby (link aktywacyjny e-mailem). Role uprzywilejowane zatwierdza
  oficer bezpieczeństwa.
* **Organizacje:** klient z pierwszym właścicielem. Właściciel aktywuje konto linkiem i sam
  zaprasza swoich pracowników (app → Członkowie).
* **Zgłoszenia:** zakłada kierownik supportu. Dostęp serwisowy zawsze wymaga otwartego
  zgłoszenia klienta.

## 11. Kopie zapasowe

Kontener `backup` co dobę:
1. tworzy zrzut bazy rolą tylko do odczytu, w spójnej migawce, razem z archiwum eksportu audytu,
2. szyfruje oba pliki kluczem publicznym `age` i zapisuje manifest z sumami kontrolnymi,
3. usuwa zestawy starsze niż `BACKUP_RETENTION_DAYS`, ale zawsze zostawia co najmniej 3.

Raz w tygodniu robi **test odtwarzania** do tymczasowej bazy. Rola `forvium_restore` ma
tylko `CREATEDB`. Test sprawdza:
- wersję migracji,
- liczby wierszy każdej tabeli,
- RLS,
- trigger audytu.

Jak działają klucze:

* Każda kopia jest szyfrowana kluczem głównym z `BACKUP_AGE_RECIPIENT` (offline).
* Przy włączonym teście odtwarzania (`RESTORE_TEST_INTERVAL_SECONDS` > 0) kopia jest
  szyfrowana także lokalnym kluczem testu, przechowywanym w wolumenie `backup-keys` na
  serwerze. Serwer, który i tak ma dostęp do bazy, może wtedy odszyfrować własne kopie.
  Magazyn zdalny nie może.
* `RESTORE_TEST_INTERVAL_SECONDS=0` oznacza, że serwer nie ma żadnego klucza prywatnego.
  Wtedy test odtwarzania wykonuj ręcznie na osobnej maszynie (poniżej), np. raz w miesiącu.

Stan i ręczne operacje:

```bash
B="docker compose -f compose.yaml -f compose.prod.yaml exec -T backup python3 /usr/local/bin/forvium_backup.py"
$B list            # zestawy: znacznik czasu, wersja migracji, liczba wierszy
$B check           # healthcheck: świeża kopia + udany ostatni test
$B backup          # kopia na żądanie (np. przed aktualizacją)
$B restore-test
```

Stan zadań `backup` i `restore-test` widać też w panelu admin (Alerty → Zadania w tle), w
`/metrics` (`forvium_job_stale`) i w alercie `ForviumBackgroundJobStopped`.

### 11.1 Kopia poza serwerem (rclone)

```bash
rclone config --config /etc/forvium-watch/rclone.conf     # zdefiniuj zdalny magazyn, np. "offsite"
chmod 600 /etc/forvium-watch/rclone.conf
echo 'OFFSITE_REMOTE=offsite:forvium-watch-backups' > /etc/forvium-watch/offsite.env

install -m 755 /opt/forvium-watch/deploy/backup/offsite-sync.sh /usr/local/sbin/forvium-offsite-sync
install -m 644 /opt/forvium-watch/deploy/systemd/forvium-backup-offsite.{service,timer} /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now forvium-backup-offsite.timer
systemctl start forvium-backup-offsite.service && journalctl -u forvium-backup-offsite -n 20
```

Synchronizacja używa `rclone copy --immutable`: raz wysłany zestaw nie jest nadpisywany ani
usuwany z serwera. Retencję w magazynie zdalnym ustaw jego własnymi regułami (lifecycle).
Najlepiej z blokadą usuwania (object lock), żeby atakujący z dostępem do serwera nie
skasował kopii.

### 11.2 Odtwarzanie awaryjne (inny serwer, klucz główny)

1. Przygotuj nowy serwer według sekcji 3–7. W punkcie 6.3 użyj **tych samych** kluczy danych
   (`FORVIUM_DATA_KEYS` / Vault) i haseł ról.
2. Uruchom samą bazę: `docker compose -f compose.yaml -f compose.prod.yaml up -d db`.
3. Pobierz zestaw z magazynu zdalnego, np. do `/root/restore/<zestaw>/`.
4. Odtwórz go do nowej bazy kluczem głównym. Polecenie `restore` nigdy nie nadpisuje
   istniejącej bazy:

   ```bash
   docker run --rm --network forvium-watch_backend \
     -v /root/restore:/backups:ro -v /root/forvium-backup-master.key:/keys/backup.key:ro \
     -e PGHOST=db -e RESTORE_PGUSER=postgres -e RESTORE_PGPASSWORD="$FORVIUM_POSTGRES_PASSWORD" \
     forvium-watch-backup restore <zestaw> --target-db forvium_restored
   ```

5. Przełącz aplikację na odtworzoną bazę. Najprościej: zatrzymaj stos, zmień w PostgreSQL
   nazwy baz (`ALTER DATABASE forvium RENAME TO forvium_old; ALTER DATABASE forvium_restored
   RENAME TO forvium;`) i uruchom całość. `migrate` doprowadzi schemat do aktualnej wersji.
6. Odtwórz katalog eksportu audytu z `audit.tar.gz.age` (`age -d -i … | tar -xz`) do wolumenu
   `forvium-watch_audit-export`.
7. Usuń klucz główny z serwera po zakończeniu.

## 12. Monitoring

Włącz profil w `.env` (`COMPOSE_PROFILES=monitoring`) i skopiuj konfigurację Alertmanagera
z prawdziwym odbiorcą:

```bash
cp /opt/forvium-watch/deploy/monitoring/alertmanager.yml /etc/forvium-watch/alertmanager.yml
vi /etc/forvium-watch/alertmanager.yml      # SMTP firmy / PagerDuty / Slack zamiast Mailpit
restorecon -v /etc/forvium-watch/alertmanager.yml
systemctl restart forvium-watch
```

Grafana i Prometheus nasłuchują tylko na `127.0.0.1`. Dostęp przez tunel SSH:

```bash
ssh -L 3000:127.0.0.1:3000 -L 9090:127.0.0.1:9090 admin@watch.forvium.example.com
# http://localhost:3000 (admin / FORVIUM_GRAFANA_PASSWORD), dashboard "Forvium Watch"
```

Reguły alertów (`deploy/monitoring/alerts.yml`):
- zatrzymane zadanie w tle, w tym kopie,
- niedostępna replika API,
- więcej niż 5% błędów 5xx,
- otwarte alerty bezpieczeństwa o wysokiej wadze,
- niewysyłane e-maile.

Monitoring z zewnątrz, np. sondę dostępności, kieruj na `https://api.<domena>/healthz`.

## 13. Aktualizacje i rotacja kluczy

### Aktualizacja aplikacji

```bash
cd /opt/src/secureware && git fetch --tags && git checkout <nowy-tag>
cd /opt/forvium-watch
C="docker compose -f compose.yaml -f compose.prod.yaml"
$C exec -T backup python3 /usr/local/bin/forvium_backup.py backup     # kopia przed aktualizacją
$C build
$C up -d            # migrate -> api/worker; kontenery są odtwarzane (krótka przerwa, kilka sekund)
$C ps
```

Migracje są tylko „do przodu”. Powrót do poprzedniej wersji oznacza odtworzenie kopii
sprzed aktualizacji (sekcja 11.2). Dlatego kopia przed aktualizacją jest obowiązkowa.

### Aktualizacje systemu

`dnf-automatic` instaluje poprawki bezpieczeństwa codziennie. Raz w miesiącu, w oknie
serwisowym, wykonaj `dnf -y upgrade` i `reboot`. Po starcie systemd (`forvium-watch.service`)
i polityki `restart: unless-stopped` podnoszą cały stos.

### Rotacja klucza danych

```bash
# 1) dopisz nowy klucz NA POCZĄTKU listy i ustaw go jako aktywny
#    FORVIUM_DATA_KEYS=k202611:<nowy_base64>,k202610:<stary_base64>
#    FORVIUM_DATA_KEY_ID=k202611
vi /opt/forvium-watch/.env
systemctl restart forvium-watch     # migrate przeszyfruje dane ("Przepisano N pól aktywnym kluczem")
# 2) stary klucz usuń dopiero po pełnym cyklu retencji kopii (kopie mają dane zaszyfrowane starym kluczem)
```

### Pełna baza haseł z wycieków (opcjonalnie)

Domyślnie aplikacja odrzuca ~46 tys. najczęstszych haseł z wycieków (lista dołączona do kodu).
Pełną bazę Pwned Passwords (setki milionów skrótów SHA-1, ~40 GB) można podłączyć offline:

1. Pobierz plik skrótów SHA-1 posortowany po skrócie, w formacie `SKRÓT:liczba`, np.
   narzędziem `haveibeenpwned-downloader` w trybie jednego pliku. Szczegóły w jego
   dokumentacji.
2. Umieść plik np. w `/srv/pwned/pwnedpasswords.txt` i nadaj etykietę `container_file_t`
   (sekcja 7).
3. Utwórz `/opt/forvium-watch/compose.site.yaml` (lokalne ustawienia serwera, plik
   ignorowany przez git):

   ```yaml
   services:
     api:
       volumes: ["/srv/pwned/pwnedpasswords.txt:/srv/pwned/pwnedpasswords.txt:ro"]
       environment: {FORVIUM_BREACHED_PASSWORDS_FILE: /srv/pwned/pwnedpasswords.txt}
     worker:
       volumes: ["/srv/pwned/pwnedpasswords.txt:/srv/pwned/pwnedpasswords.txt:ro"]
       environment: {FORVIUM_BREACHED_PASSWORDS_FILE: /srv/pwned/pwnedpasswords.txt}
   ```

   Dopisz `-f compose.site.yaml` do poleceń `docker compose` i do `ExecStart`/`ExecStop`
   w `/etc/systemd/system/forvium-watch.service`, potem `systemctl daemon-reload` i
   `systemctl restart forvium-watch`.

Wyszukiwanie jest binarne (kilkadziesiąt odczytów na sprawdzenie) i nie wysyła żadnych
danych na zewnątrz. Konta z hasłem, które pojawi się w bazie, przy następnym logowaniu muszą
zmienić hasło.

### Rotacja haseł ról bazy

Zmień hasło w PostgreSQL (`ALTER ROLE forvium_app PASSWORD '…'`), potem w `.env`, a następnie
`systemctl restart forvium-watch`.

## 14. Rozwiązywanie problemów

| Objaw | Przyczyna i rozwiązanie |
|---|---|
| `permission denied` przy czytaniu plików konfiguracyjnych w kontenerze | etykieta SELinux. Sprawdź `ausearch -m avc -ts recent` i `ls -Z <plik>`, wykonaj ponownie `restorecon` z sekcji 7 |
| gateway restartuje się, `cannot load certificate` | brak plików w `/etc/forvium-watch/tls`. Wróć do sekcji 8, punkt 1 |
| `required variable ... is missing` przy `docker compose` | brak wartości w `.env` (komunikat podaje nazwę) |
| nikt nie dostaje linków aktywacyjnych | SMTP. Zobacz `journalctl -t forvium/forvium-watch-worker-1 \| grep -i smtp` i alert `ForviumEmailDeliveryFailing` |
| `backup` w stanie `unhealthy` | `$B check` podaje przyczynę: brak świeżej kopii albo nieudany test odtwarzania. Szczegóły w `journalctl -t forvium/forvium-watch-backup-1` |
| panel admin zwraca 403 | adres spoza `/etc/forvium-watch/admin-allow.conf`. Po zmianie: `docker compose … exec gateway nginx -s reload` |
| operator nie może się zalogować kodem z aplikacji | przy `FORVIUM_OPERATOR_LOGIN_WEBAUTHN_ONLY=true` operator z kluczem loguje się tylko kluczem. Przy utracie klucza administrator blokuje konto i zakłada nowe |
| 429 przy logowaniu | limity prób (brama i aplikacja) działają zgodnie z założeniem. Odczekaj 15 min |

## 15. Lista kontrolna przed startem

- [ ] SELinux `Enforcing`, brak wpisów AVC dla kontenerów (`ausearch -m avc -ts today`).
- [ ] `firewall-cmd --list-services`: tylko `ssh http https`; `ss -tlnp` pokazuje publicznie tylko 22/80/443.
- [ ] `.env` ma prawa `600`, a klucze danych i klucz główny kopii są zapisane poza serwerem.
- [ ] Certyfikat Let's Encrypt działa (`certbot renew --dry-run` OK), a HSTS jest obecny.
- [ ] `admin-allow.conf` ogranicza panel operatorów do sieci firmy / VPN.
- [ ] Pierwszy administrator i oficer bezpieczeństwa mają klucze bezpieczeństwa i logują się tylko kluczem.
- [ ] Kopia, test odtwarzania i kopia poza serwerem zakończyły się sukcesem (`$B check`, `journalctl -u forvium-backup-offsite`).
- [ ] Ręczny test odtwarzania kluczem głównym na osobnej maszynie (sekcja 11.2) przeprowadzony i opisany.
- [ ] Alertmanager wysyła alerty do właściwego odbiorcy (test: `docker compose … stop worker` → alert po ~5 min, potem `start`).
- [ ] Break Glass pozostaje wyłączony, dopóki procedura nie zostanie formalnie przyjęta.
