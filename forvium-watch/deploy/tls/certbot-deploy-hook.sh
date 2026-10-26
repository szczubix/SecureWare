#!/bin/sh
# Hook certbota (--deploy-hook): kopiuje odnowiony certyfikat Forvium Watch do katalogu
# czytanego przez gateway i przeladowuje nginx bez przerwy w dzialaniu.
# Instalacja: /etc/letsencrypt/renewal-hooks/deploy/forvium-watch.sh (chmod 755).
set -eu
CERT_NAME="${CERT_NAME:-forvium-watch}"
[ -n "${RENEWED_LINEAGE:-}" ] && [ "$(basename "$RENEWED_LINEAGE")" != "$CERT_NAME" ] && exit 0
SRC="/etc/letsencrypt/live/$CERT_NAME"
DST="${FORVIUM_TLS_DIR:-/etc/forvium-watch/tls}"
# Klucz czyta proces glowny nginx (root w kontenerze) - wystarcza prawa 600.
install -d -m 700 "$DST"
install -m 644 "$SRC/fullchain.pem" "$DST/fullchain.pem"
install -m 600 "$SRC/privkey.pem" "$DST/privkey.pem"
# Etykieta SELinux container_file_t (regula semanage fcontext z instrukcji wdrozenia).
restorecon -R "$DST" 2>/dev/null || true
cd "${FORVIUM_DIR:-/opt/forvium-watch}"
docker compose -f compose.yaml -f compose.prod.yaml exec -T gateway nginx -s reload
