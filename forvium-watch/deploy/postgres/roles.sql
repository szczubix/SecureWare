-- Role PostgreSQL dla Forvium Watch. Uruchom raz, jako superuser, PRZED pierwsza migracja:
--   psql -v migrator_password="'...'" -v app_password="'...'" -d forvium -f roles.sql
--
-- * forvium_migrator - wlasciciel schematu; uzywany WYLACZNIE przez `alembic upgrade head`.
-- * forvium_app      - konto API: DML na tabelach, na audycie tylko SELECT/INSERT
--                      (uprawnienia nadaje migracja 0002 i kolejne).
-- Zadna z rol nie jest superuserem (superuser omija Row-Level Security).

CREATE ROLE forvium_migrator LOGIN PASSWORD :migrator_password NOSUPERUSER NOCREATEDB NOCREATEROLE;
CREATE ROLE forvium_app LOGIN PASSWORD :app_password NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS;

SELECT format('GRANT CONNECT ON DATABASE %I TO forvium_app', current_database()) \gexec
ALTER SCHEMA public OWNER TO forvium_migrator;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO forvium_app;

-- Tabele tworzone w przyszlosci przez migratora: DML dla aplikacji (audyt zawezaja migracje).
ALTER DEFAULT PRIVILEGES FOR ROLE forvium_migrator IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO forvium_app;
ALTER DEFAULT PRIVILEGES FOR ROLE forvium_migrator IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO forvium_app;
