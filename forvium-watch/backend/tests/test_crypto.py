"""Szyfrowanie danych w spoczynku."""

from __future__ import annotations

import base64
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from cryptography.exceptions import InvalidTag
from sqlalchemy import select, text

from forvium.core.config import Settings
from forvium.core.crypto import (
    CryptoConfigError,
    KeyRing,
    get_keyring,
    keyring_from_settings,
    reencrypt_all,
    set_keyring,
)
from forvium.identity.models import User
from forvium.organizations.models import Organization


def _raw(env, sql):
    with env.app.state.db.sessionmaker() as db:
        return db.execute(text(sql)).all()


def test_secrets_are_encrypted_in_database(env):
    rows = _raw(env, "SELECT mfa_secret FROM users")
    assert rows and all(r[0].startswith("fwenc:v1:k1:") for r in rows)
    dump = repr(_raw(env, "SELECT secrets, smtp_config, webhooks FROM organizations"))
    assert "sk-acme-secret" not in dump and "smtp-super-secret" not in dump and "abc123" not in dump
    assert "fwenc:v1:" in dump
    # Aplikacja widzi wartosci jawne, a logowanie z TOTP dziala.
    with env.app.state.db.sessionmaker() as db:
        acme = db.scalar(select(Organization).where(Organization.name.like("Acme%")))
        assert acme.secrets == {"siem_api_key": "sk-acme-secret"}
    assert env.login_app("alice")


def test_ciphertext_is_bound_to_column(env):
    keyring = get_keyring()
    token = keyring.encrypt(b"JBSWY3DPEHPK3PXP", "users.mfa_secret")
    with pytest.raises(InvalidTag):
        keyring.decrypt(token, "organizations.secrets")


def test_key_rotation_and_legacy_plaintext(env):
    # Dane zapisane starym kluczem k0 oraz "stare" dane jawne sprzed wlaczenia szyfrowania.
    old = KeyRing(get_keyring().keys, "k0")
    with env.app.state.db.sessionmaker() as db:
        db.execute(text("UPDATE users SET mfa_secret = :v WHERE email = 'bob@acme.example'"),
                   {"v": old.encrypt(b"JBSWY3DPEHPK3PXPBOBBBBBB", "users.mfa_secret")})
        db.execute(text("UPDATE organizations SET secrets = :v WHERE name = 'Beta S.A.'"),
                   {"v": json.dumps({"siem_api_key": "sk-beta-secret"})})
        db.commit()
    assert env.login_app("bob")  # odczyt kluczem k0 nadal dziala
    with env.app.state.db.sessionmaker() as db:
        beta = db.scalar(select(Organization).where(Organization.name == "Beta S.A."))
        assert beta.secrets == {"siem_api_key": "sk-beta-secret"}  # odczyt danych jawnych
        assert reencrypt_all(db) == 2
        db.commit()
    assert _raw(env, "SELECT count(*) FROM users WHERE mfa_secret LIKE 'fwenc:v1:k0:%'")[0][0] == 0
    assert "sk-beta-secret" not in repr(_raw(env, "SELECT secrets FROM organizations"))
    with env.app.state.db.sessionmaker() as db:
        assert reencrypt_all(db) == 0  # wszystko juz aktywnym kluczem
        bob = db.scalar(select(User).where(User.email == "bob@acme.example"))
        assert bob.mfa_secret == "JBSWY3DPEHPK3PXPBOBBBBBB"


def test_app_refuses_to_start_without_key():
    with pytest.raises(CryptoConfigError, match="Brak klucza"):
        keyring_from_settings(Settings(data_keys="", data_keys_wrapped="", allow_insecure_dev_key=False))
    with pytest.raises(CryptoConfigError, match="32 bajty"):
        keyring_from_settings(Settings(data_keys="x:" + base64.b64encode(b"short").decode()))


def test_vault_transit_unwraps_data_keys(env):
    dek = b"v" * 32
    seen = {}

    class Vault(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            seen["path"] = self.path
            seen["token"] = self.headers["X-Vault-Token"]
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            seen["ciphertext"] = body["ciphertext"]
            out = json.dumps({"data": {"plaintext": base64.b64encode(dek).decode()}}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(out)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Vault)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    previous = get_keyring()
    try:
        ring = keyring_from_settings(Settings(
            data_keys="", data_keys_wrapped="v2:vault:v1:abcdef", data_key_id="v2",
            vault_addr=f"http://127.0.0.1:{server.server_port}", vault_token="s.test", vault_transit_key="fw"))
        assert ring.keys == {"v2": dek} and ring.active_kid == "v2"
        assert seen == {"path": "/v1/transit/decrypt/fw", "token": "s.test", "ciphertext": "vault:v1:abcdef"}
    finally:
        server.shutdown()
        set_keyring(previous)


def test_reencrypt_cli_encrypts_legacy_plaintext(env, tmp_path):
    """Sciezka aktualizacji: dane jawne sprzed szyfrowania -> `python -m forvium.core.crypto reencrypt`."""
    import os
    import subprocess
    import sys

    with env.app.state.db.sessionmaker() as db:
        db.execute(text("UPDATE users SET mfa_secret = 'JBSWY3DPEHPK3PXPCAROLCCC' WHERE email = 'carol@beta.example'"))
        db.commit()
    url = str(env.app.state.db.engine.url.render_as_string(hide_password=False))
    from conftest import TEST_DATA_KEYS

    result = subprocess.run([sys.executable, "-m", "forvium.core.crypto", "reencrypt"], capture_output=True, text=True,
                            env={**os.environ, "FORVIUM_DATABASE_URL": url, "FORVIUM_DATA_KEYS": TEST_DATA_KEYS,
                                 "FORVIUM_DATA_KEY_ID": "k1"}, cwd=os.path.dirname(os.path.dirname(__file__)))
    assert result.returncode == 0, result.stderr
    assert "Przepisano 1 pol" in result.stdout
    raw = _raw(env, "SELECT mfa_secret FROM users WHERE email = 'carol@beta.example'")[0][0]
    assert raw.startswith("fwenc:v1:k1:")
    assert env.login_app("carol")
