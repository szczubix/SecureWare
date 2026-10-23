"""Kopie zapasowe Forvium Watch: zaszyfrowany zrzut bazy + archiwum eksportu audytu.

    forvium_backup.py backup        jedna kopia (zestaw w BACKUP_DIR/<znacznik czasu>/)
    forvium_backup.py restore-test  odtworzenie najnowszej kopii do tymczasowej bazy i weryfikacja
    forvium_backup.py restore SET --target-db NAZWA   odtworzenie (procedura awaryjna, DR)
    forvium_backup.py run           petla: kopia co BACKUP_INTERVAL_SECONDS, test odtwarzania
                                    co RESTORE_TEST_INTERVAL_SECONDS
    forvium_backup.py check         healthcheck: swieza kopia i udany ostatni test odtwarzania

Zestaw kopii:
  db.dump.age      pg_dump -Fc zaszyfrowany kluczem publicznym age (BACKUP_AGE_RECIPIENT) -
                   host kopii nie potrafi ich odszyfrowac; klucz prywatny trzymany jest osobno
  audit.tar.gz.age archiwum katalogu eksportu audytu (lancuch skrotow, Break Glass)
  manifest.json    SHA-256 plikow, wersja migracji, liczba wierszy kazdej tabeli
                   (policzona w TEJ SAMEJ migawce co zrzut) - podstawa testu odtwarzania

Polaczenia przez zmienne libpq: PGHOST/PGPORT/PGDATABASE; kopia jako BACKUP_PGUSER
(rola forvium_backup: tylko odczyt, BYPASSRLS), odtwarzanie jako RESTORE_PGUSER
(superuser lub wlasciciel klastra). Stan zadan trafia do tabeli job_runs (jak zadania
workera), wiec obejmuje go istniejacy monitoring i alerty.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

import psycopg

BACKUP_DIR = Path(os.environ.get("BACKUP_DIR", "/backups"))
AUDIT_DIR = Path(os.environ.get("BACKUP_AUDIT_DIR", "/var/forvium/audit"))
RETENTION_DAYS = int(os.environ.get("BACKUP_RETENTION_DAYS", "14"))
KEEP_MIN = int(os.environ.get("BACKUP_KEEP_MIN", "3"))
INTERVAL = int(os.environ.get("BACKUP_INTERVAL_SECONDS", "86400"))
RESTORE_TEST_INTERVAL = int(os.environ.get("RESTORE_TEST_INTERVAL_SECONDS", str(7 * 86400)))
RESTORE_TEST_DB = "forvium_restore_check"
STATUS_FILE = BACKUP_DIR / "status.json"


def log(msg: str, **fields) -> None:
    print(json.dumps({"ts": datetime.now(UTC).isoformat(), "logger": "forvium.backup", "msg": msg, **fields},
                     ensure_ascii=False), flush=True)


def _conninfo(user_var: str, password_var: str, dbname: str | None = None) -> str:
    parts = {"user": os.environ[user_var], "password": os.environ.get(password_var, ""),
             "host": os.environ.get("PGHOST", "db"), "port": os.environ.get("PGPORT", "5432"),
             "dbname": dbname or os.environ.get("PGDATABASE", "forvium")}
    return psycopg.conninfo.make_conninfo(**{k: v for k, v in parts.items() if v})


def _pg_env(user_var: str, password_var: str) -> dict:
    env = dict(os.environ, PGUSER=os.environ[user_var])
    env["PGPASSWORD"] = os.environ.get(password_var, "")
    return env


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _recipient() -> str:
    recipient = os.environ.get("BACKUP_AGE_RECIPIENT", "").strip()
    if recipient:
        return recipient
    # Tylko lokalnie: klucz generowany przy pierwszym uruchomieniu w osobnym wolumenie.
    identity = Path(os.environ.get("BACKUP_AGE_IDENTITY_FILE", "/keys/backup.key"))
    if not identity.exists():
        identity.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["age-keygen", "-o", str(identity)], check=True, capture_output=True)
        log("Wygenerowano lokalny klucz kopii (w produkcji ustaw BACKUP_AGE_RECIPIENT)", identity=str(identity))
    out = subprocess.run(["age-keygen", "-y", str(identity)], check=True, capture_output=True, text=True)
    return out.stdout.strip()


def _encrypt(src_cmd: list[str], dest: Path, recipient: str, env: dict | None = None) -> None:
    """Strumieniowo: polecenie -> age -> plik (niezaszyfrowane dane nie trafiaja na dysk)."""
    with dest.open("wb") as out:
        producer = subprocess.Popen(src_cmd, stdout=subprocess.PIPE, env=env)
        age = subprocess.run(["age", "-r", recipient], stdin=producer.stdout, stdout=out)
        producer.stdout.close()
        if producer.wait() != 0 or age.returncode != 0:
            raise RuntimeError(f"{src_cmd[0]} albo age zakończyło się błędem")


def _heartbeat(job: str, interval: int, started: datetime, error: str | None) -> None:
    """Zapis do job_runs (konto aplikacji), zeby monitoring widzial zatrzymane kopie."""
    if not os.environ.get("HEARTBEAT_PGUSER"):
        return
    duration = int((datetime.now(UTC) - started).total_seconds() * 1000)
    now = datetime.now(UTC).replace(tzinfo=None)  # job_runs trzyma czas UTC bez strefy
    try:
        with psycopg.connect(_conninfo("HEARTBEAT_PGUSER", "HEARTBEAT_PGPASSWORD")) as conn:
            conn.execute(
                """INSERT INTO job_runs (job, interval_seconds, last_started_at, last_success_at, last_error,
                                         last_error_at, last_duration_ms, runs, failures)
                   VALUES (%(job)s, %(interval)s, %(started)s, %(ok)s, %(err)s, %(err_at)s, %(dur)s, 1, %(fail)s)
                   ON CONFLICT (job) DO UPDATE SET
                     interval_seconds = EXCLUDED.interval_seconds, last_started_at = EXCLUDED.last_started_at,
                     last_success_at = COALESCE(EXCLUDED.last_success_at, job_runs.last_success_at),
                     last_error = COALESCE(EXCLUDED.last_error, job_runs.last_error),
                     last_error_at = COALESCE(EXCLUDED.last_error_at, job_runs.last_error_at),
                     last_duration_ms = EXCLUDED.last_duration_ms,
                     runs = job_runs.runs + 1, failures = job_runs.failures + EXCLUDED.failures""",
                {"job": job, "interval": interval, "started": started.replace(tzinfo=None),
                 "ok": now if error is None else None, "err": error[:300] if error else None,
                 "err_at": now if error else None, "dur": duration, "fail": 1 if error else 0})
    except psycopg.Error as exc:
        log("Nie udało się zapisać stanu zadania", job=job, error=type(exc).__name__)


# --------------------------------------------------------------------------- kopia


def backup() -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    work = BACKUP_DIR / f".{stamp}.partial"
    work.mkdir(parents=True)
    recipient = _recipient()
    env = _pg_env("BACKUP_PGUSER", "BACKUP_PGPASSWORD")
    # Migawka REPEATABLE READ trzymana przez caly zrzut: pg_dump i liczniki widza te same dane.
    with psycopg.connect(_conninfo("BACKUP_PGUSER", "BACKUP_PGPASSWORD")) as conn:
        conn.execute("BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY")
        snapshot = conn.execute("SELECT pg_export_snapshot()").fetchone()[0]
        tables = [r[0] for r in conn.execute(
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename")]
        counts = {t: conn.execute(f'SELECT count(*) FROM public."{t}"').fetchone()[0] for t in tables}
        version = conn.execute("SELECT version_num FROM alembic_version").fetchone()[0]
        server = conn.execute("SHOW server_version").fetchone()[0]
        _encrypt(["pg_dump", "-Fc", "--snapshot", snapshot, "--no-password"], work / "db.dump.age", recipient, env)
        conn.rollback()
    files = ["db.dump.age"]
    if AUDIT_DIR.is_dir():
        _encrypt(["tar", "-czf", "-", "-C", str(AUDIT_DIR), "."], work / "audit.tar.gz.age", recipient)
        files.append("audit.tar.gz.age")
    manifest = {
        "created_at": datetime.now(UTC).isoformat(), "alembic_version": version, "server_version": server,
        "recipient": recipient, "row_counts": counts,
        "files": {f: {"sha256": _sha256(work / f), "bytes": (work / f).stat().st_size} for f in files},
    }
    (work / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    final = BACKUP_DIR / stamp
    work.rename(final)  # zestaw jest widoczny dopiero, gdy jest kompletny
    log("Kopia zapasowa gotowa", set=stamp, tables=len(counts), rows=sum(counts.values()),
        bytes=sum(v["bytes"] for v in manifest["files"].values()))
    prune()
    return final


def backup_sets() -> list[Path]:
    if not BACKUP_DIR.is_dir():
        return []
    return sorted(p for p in BACKUP_DIR.iterdir() if p.is_dir() and not p.name.startswith(".")
                  and (p / "manifest.json").exists())


def prune() -> None:
    sets = backup_sets()
    cutoff = datetime.now(UTC) - timedelta(days=RETENTION_DAYS)
    for p in sets[:-KEEP_MIN] if KEEP_MIN else sets:
        created = datetime.fromisoformat(json.loads((p / "manifest.json").read_text())["created_at"])
        if created < cutoff:
            shutil.rmtree(p)
            log("Usunięto starą kopię (retencja)", set=p.name)
    for p in BACKUP_DIR.glob(".*.partial"):
        if time.time() - p.stat().st_mtime > 86400:
            shutil.rmtree(p, ignore_errors=True)


# ---------------------------------------------------------------------- odtwarzanie


def _identity() -> str:
    path = os.environ.get("BACKUP_AGE_IDENTITY_FILE", "/keys/backup.key")
    if not Path(path).exists():
        raise SystemExit(f"Brak klucza prywatnego kopii: {path} (BACKUP_AGE_IDENTITY_FILE)")
    return path


def _verify_checksums(backup_set: Path) -> dict:
    manifest = json.loads((backup_set / "manifest.json").read_text())
    for name, meta in manifest["files"].items():
        if _sha256(backup_set / name) != meta["sha256"]:
            raise RuntimeError(f"Niezgodna suma kontrolna: {backup_set.name}/{name}")
    return manifest


def _restore_into(backup_set: Path, target_db: str) -> None:
    env = _pg_env("RESTORE_PGUSER", "RESTORE_PGPASSWORD")
    identity = _identity()
    with tempfile.TemporaryDirectory() as tmp:
        dump = Path(tmp) / "db.dump"
        subprocess.run(["age", "-d", "-i", identity, "-o", str(dump), str(backup_set / "db.dump.age")], check=True)
        subprocess.run(["createdb", "--no-password", target_db], check=True, env=env)
        # --exit-on-error: czesciowo odtworzona baza to blad, nie sukces.
        subprocess.run(["pg_restore", "--no-password", "--exit-on-error", "-d", target_db, str(dump)],
                       check=True, env=env)


def restore_test() -> dict:
    try:
        return _restore_test()
    except Exception as exc:
        # Kazda porazka (tez uszkodzony plik) ma byc widoczna w healthchecku.
        (BACKUP_DIR / "restore-test.json").write_text(json.dumps(
            {"tested_at": datetime.now(UTC).isoformat(), "ok": False, "error": f"{type(exc).__name__}: {exc}"},
            indent=2, ensure_ascii=False) + "\n")
        raise


def _restore_test() -> dict:
    sets = backup_sets()
    if not sets:
        raise RuntimeError("Brak kopii do przetestowania")
    backup_set = sets[-1]
    manifest = _verify_checksums(backup_set)
    admin = _conninfo("RESTORE_PGUSER", "RESTORE_PGPASSWORD", dbname="postgres")
    with psycopg.connect(admin, autocommit=True) as conn:
        conn.execute(f'DROP DATABASE IF EXISTS "{RESTORE_TEST_DB}"')
    checks: dict[str, object] = {}
    mismatched: dict[str, dict] = {}
    try:
        _restore_into(backup_set, RESTORE_TEST_DB)
        with psycopg.connect(_conninfo("RESTORE_PGUSER", "RESTORE_PGPASSWORD", dbname=RESTORE_TEST_DB)) as conn:
            version = conn.execute("SELECT version_num FROM alembic_version").fetchone()[0]
            checks["alembic_version"] = version == manifest["alembic_version"]
            for table, expected in manifest["row_counts"].items():
                got = conn.execute(f'SELECT count(*) FROM public."{table}"').fetchone()[0]
                if got != expected:
                    mismatched[table] = {"expected": expected, "restored": got}
            checks["row_counts"] = not mismatched
            forced = conn.execute("SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
                                  "WHERE n.nspname = 'public' AND c.relforcerowsecurity").fetchone()[0]
            checks["rls_forced_tables"] = forced > 0
            # Audyt tylko do dopisywania: trigger musi istniec i odrzucic zmiane (nawet superusera).
            triggers = conn.execute("SELECT count(*) FROM pg_trigger WHERE tgrelid = 'audit_events'::regclass "
                                    "AND NOT tgisinternal").fetchone()[0]
            rejected = True
            if manifest["row_counts"].get("audit_events"):
                try:
                    with conn.transaction():
                        conn.execute("UPDATE audit_events SET action = action "
                                     "WHERE id = (SELECT id FROM audit_events LIMIT 1)")
                    rejected = False
                except psycopg.errors.RaiseException:
                    pass
            checks["audit_append_only"] = triggers > 0 and rejected
        if "audit.tar.gz.age" in manifest["files"]:
            with tempfile.TemporaryDirectory() as tmp:
                tar = Path(tmp) / "audit.tar.gz"
                subprocess.run(["age", "-d", "-i", _identity(), "-o", str(tar),
                                str(backup_set / "audit.tar.gz.age")], check=True)
                listing = subprocess.run(["tar", "-tzf", str(tar)], check=True, capture_output=True, text=True)
                checks["audit_archive"] = bool(listing.stdout.strip())
    finally:
        with psycopg.connect(admin, autocommit=True) as conn:
            conn.execute(f'DROP DATABASE IF EXISTS "{RESTORE_TEST_DB}"')
    ok = all(checks.values())
    result = {"tested_at": datetime.now(UTC).isoformat(), "set": backup_set.name, "ok": ok, "checks": checks,
              "row_count_mismatches": mismatched,
              "rows": sum(manifest["row_counts"].values())}
    (BACKUP_DIR / "restore-test.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    log("Test odtwarzania " + ("udany" if ok else "NIEUDANY"), **{k: v for k, v in result.items() if k != "tested_at"})
    if not ok:
        raise RuntimeError("Test odtwarzania nie powiódł się: " + json.dumps(checks))
    return result


def restore(set_name: str, target_db: str) -> None:
    backup_set = BACKUP_DIR / set_name
    manifest = _verify_checksums(backup_set)
    admin = _conninfo("RESTORE_PGUSER", "RESTORE_PGPASSWORD", dbname="postgres")
    with psycopg.connect(admin, autocommit=True) as conn:
        if conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", (target_db,)).fetchone():
            raise SystemExit(f"Baza {target_db} istnieje - odtwarzamy tylko do nowej bazy (bez nadpisywania).")
    _restore_into(backup_set, target_db)
    log("Odtworzono kopię", set=set_name, target_db=target_db, alembic_version=manifest["alembic_version"])


# ---------------------------------------------------------------------------- petla


def _timed(job: str, interval: int, fn) -> bool:
    started = datetime.now(UTC)
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 - blad jest raportowany, petla dziala dalej
        log("Zadanie nie powiodło się", job=job, error=f"{type(exc).__name__}: {exc}")
        _heartbeat(job, interval, started, f"{type(exc).__name__}: {exc}")
        return False
    _heartbeat(job, interval, started, None)
    return True


def run_forever() -> None:
    last_test: float | None = None  # pierwszy test zaraz po pierwszej kopii
    while True:
        t0 = time.monotonic()
        due = last_test is None or time.monotonic() - last_test >= RESTORE_TEST_INTERVAL - INTERVAL / 2
        if _timed("backup", INTERVAL, backup) and due:
            if _timed("restore-test", RESTORE_TEST_INTERVAL, restore_test):
                last_test = time.monotonic()
        time.sleep(max(1.0, INTERVAL - (time.monotonic() - t0)))


def check() -> int:
    sets = backup_sets()
    if not sets:
        print("brak kopii")
        return 1
    created = datetime.fromisoformat(json.loads((sets[-1] / "manifest.json").read_text())["created_at"])
    age = (datetime.now(UTC) - created).total_seconds()
    if age > 2 * INTERVAL + 600:
        print(f"ostatnia kopia sprzed {int(age)} s")
        return 1
    test_file = BACKUP_DIR / "restore-test.json"
    if test_file.exists() and not json.loads(test_file.read_text())["ok"]:
        print("ostatni test odtwarzania nieudany")
        return 1
    print("ok", sets[-1].name)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("backup")
    sub.add_parser("restore-test")
    sub.add_parser("run")
    sub.add_parser("check")
    sub.add_parser("list")
    r = sub.add_parser("restore")
    r.add_argument("set")
    r.add_argument("--target-db", required=True)
    args = parser.parse_args(argv)
    if args.cmd == "backup":
        _timed("backup", INTERVAL, backup) or sys.exit(1)
    elif args.cmd == "restore-test":
        _timed("restore-test", RESTORE_TEST_INTERVAL, restore_test) or sys.exit(1)
    elif args.cmd == "restore":
        restore(args.set, args.target_db)
    elif args.cmd == "run":
        run_forever()
    elif args.cmd == "check":
        return check()
    elif args.cmd == "list":
        for p in backup_sets():
            m = json.loads((p / "manifest.json").read_text())
            print(p.name, m["alembic_version"], sum(m["row_counts"].values()), "wierszy")
    return 0


if __name__ == "__main__":
    sys.exit(main())
