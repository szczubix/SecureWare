#!/bin/sh
# Inicjalizacja kontenera PostgreSQL (docker-entrypoint-initdb.d): role migratora i aplikacji.
set -eu
psql -v ON_ERROR_STOP=1 \
     -v migrator_password="'${FORVIUM_MIGRATOR_PASSWORD}'" \
     -v app_password="'${FORVIUM_APP_PASSWORD}'" \
     --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
     -f /forvium/roles.sql
