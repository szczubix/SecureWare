"""PostgreSQL: Row-Level Security dla sesji wsparcia i uprawnienia roli aplikacji.

* RLS: gdy w transakcji ustawiono `forvium.support_org` (robi to API dla kazdego
  zadania z tokenem sesji wsparcia), tabele z danymi organizacji zwracaja i
  przyjmuja WYLACZNIE wiersze tej organizacji. Nawet blad w kodzie aplikacji
  nie pokaze operatorowi danych innej organizacji. Zwykle zadania (bez
  ustawienia) dzialaja bez zmian. FORCE obejmuje tez wlasciciela tabel;
  superuser omija RLS, wiec API nie moze laczyc sie jako superuser.
* Rola `forvium_app` (jesli istnieje - patrz deploy/postgres/roles.sql):
  pelny DML na tabelach aplikacji, ale na `audit_events` / `audit_exports`
  tylko SELECT i INSERT.

Na SQLite migracja nic nie robi.

Revision ID: 0002
Revises: 0001
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0002"
down_revision: Union[str, Sequence[str], None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (tabela, kolumna organizacji)
ORG_SCOPED_TABLES = [
    ("organizations", "id"),
    ("org_units", "organization_id"),
    ("memberships", "organization_id"),
    ("technologies", "organization_id"),
    ("diagnostic_events", "organization_id"),
    ("support_tickets", "organization_id"),
]

APPEND_ONLY_TABLES = ["audit_events", "audit_exports"]

APP_GRANTS_SQL = """
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'forvium_app') THEN
        GRANT USAGE ON SCHEMA public TO forvium_app;
        GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO forvium_app;
        GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO forvium_app;
        REVOKE UPDATE, DELETE, TRUNCATE ON {append_only} FROM forvium_app;
        REVOKE ALL ON alembic_version FROM forvium_app;
        GRANT SELECT ON alembic_version TO forvium_app;
    END IF;
END
$$;
""".format(append_only=", ".join(APPEND_ONLY_TABLES))


def _predicate(column: str) -> str:
    setting = "current_setting('forvium.support_org', true)"
    return f"(coalesce({setting}, '') = '' OR {column} = {setting})"


def upgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return
    for table, column in ORG_SCOPED_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY forvium_support_org_isolation ON {table} "
            f"USING {_predicate(column)} WITH CHECK {_predicate(column)}"
        )
    op.execute(APP_GRANTS_SQL)


def downgrade() -> None:
    if op.get_bind().dialect.name != "postgresql":
        return
    for table, _ in ORG_SCOPED_TABLES:
        op.execute(f"DROP POLICY IF EXISTS forvium_support_org_isolation ON {table}")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
