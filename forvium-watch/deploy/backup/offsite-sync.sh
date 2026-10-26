#!/bin/sh
# Kopia zaszyfrowanych zestawow (age) poza serwer przez rclone (S3, SFTP, Azure, B2...).
# Instalacja: install -m 755 offsite-sync.sh /usr/local/sbin/forvium-offsite-sync
# Uruchamiane przez forvium-backup-offsite.timer. Konfiguracja:
#   /etc/forvium-watch/offsite.env  -> OFFSITE_REMOTE=nazwa_zdalnego:sciezka
#   /etc/forvium-watch/rclone.conf  -> definicja zdalnego magazynu (rclone config)
set -eu
: "${OFFSITE_REMOTE:?ustaw OFFSITE_REMOTE w /etc/forvium-watch/offsite.env}"
SRC="$(docker volume inspect -f '{{.Mountpoint}}' "${BACKUP_VOLUME:-forvium-watch_backups}")"
# --immutable: zestaw raz wyslany nie jest nadpisywany (ochrona przed podmiana / ransomware).
exec rclone copy --immutable --checksum \
  --exclude "/restore-test.json" --exclude "/.*/**" \
  --config /etc/forvium-watch/rclone.conf \
  "$SRC" "$OFFSITE_REMOTE"
