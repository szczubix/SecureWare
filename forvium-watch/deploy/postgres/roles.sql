-- Role PostgreSQL dla Forvium Watch. Uruchom raz, jako superuser, PRZED pierwsza migracja:
--   psql -v migrator_password="'...'" -v app_password="'...'" -v backup_password="'...'" -d forvium -f roles.sql
--
-- * forvium_migrator - wlasciciel schematu; uzywany WYLACZNIE przez `alembic upgrade head`.
-- * forvium_app      - konto API: DML na tabelach, na audycie tylko SELECT/INSERT
--                      (uprawnienia nadaje migracja 0002 i kolejne).
-- * forvium_backup   - kopie zapasowe: tylko odczyt (pg_read_all_data) z BYPASSRLS, zeby
--                      pg_dump widzial wszystkie organizacje; bez prawa zapisu.
-- Zadna z rol nie jest superuserem (superuser omija Row-Level Security).

CREATE ROLE forvium_migrator LOGIN PASSWORD :migrator_password NOSUPERUSER NOCREATEDB NOCREATEROLE;
CREATE ROLE forvium_app LOGIN PASSWORD :app_password NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;
CREATE ROLE forvium_backup LOGIN PASSWORD :backup_password NOSUPERUSER NOCREATEDB NOCREATEROLE BYPASSRLS
    IN ROLE pg_read_all_data;

SELECT format('GRANT CONNECT ON DATABASE %I TO forvium_app, forvium_backup', current_database()) \gexec
ALTER SCHEMA public OWNER TO forvium_migrator;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO forvium_app;

-- Tabele tworzone w przyszlosci przez migratora: DML dla aplikacji (audyt zawezaja migracje).
ALTER DEFAULT PRIVILEGES FOR ROLE forvium_migrator IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO forvium_app;
ALTER DEFAULT PRIVILEGES FOR ROLE forvium_migrator IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO forvium_app;
