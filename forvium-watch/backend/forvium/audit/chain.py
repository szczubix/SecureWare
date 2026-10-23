"""Strumien zdarzen audytu z lancuchem skrotow (tamper-evident).

Kazda linia JSONL zawiera zdarzenie, `prev_hash` i `hash`:

    hash = HMAC-SHA256(key, prev_hash + canonical_json(event))   (gdy podano klucz)
    hash = SHA-256(prev_hash + canonical_json(event))            (bez klucza)

Usuniecie, zmiana lub przestawienie dowolnej linii psuje lancuch od tego
miejsca, co wykrywa `python -m forvium.audit.verify plik.jsonl [--key ...]`.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import threading
from pathlib import Path

GENESIS = "0" * 64


def canonical(event: dict) -> str:
    return json.dumps(event, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def chain_hash(prev_hash: str, event: dict, key: bytes | None = None) -> str:
    payload = (prev_hash + canonical(event)).encode()
    if key:
        return hmac.new(key, payload, hashlib.sha256).hexdigest()
    return hashlib.sha256(payload).hexdigest()


def event_dict(e) -> dict:
    """Serializacja AuditEvent do eksportu."""
    return {
        "id": e.id,
        "occurred_at": e.occurred_at.isoformat() + "Z",
        "action": e.action,
        "outcome": e.outcome,
        "actor_user_id": e.actor_user_id,
        "actor_type": e.actor_type,
        "on_behalf_of_user_id": e.on_behalf_of_user_id,
        "organization_id": e.organization_id,
        "support_session_id": e.support_session_id,
        "support_request_id": e.support_request_id,
        "is_break_glass": bool(e.is_break_glass),
        "http_method": e.http_method,
        "route": e.route,
        "status_code": e.status_code,
        "ip_address": e.ip_address,
        "details": e.details or {},
    }


class ChainedJsonlFile:
    """Plik JSONL tylko do dopisywania; ostatni skrot odczytywany z konca pliku."""

    def __init__(self, path: str, key: bytes | None = None) -> None:
        self.path = Path(path)
        self.key = key
        self._lock = threading.Lock()
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _last_hash(self) -> str:
        if not self.path.exists() or self.path.stat().st_size == 0:
            return GENESIS
        with self.path.open("rb") as f:
            f.seek(0, os.SEEK_END)
            pos = f.tell()
            buf = b""
            while pos > 0:
                step = min(4096, pos)
                pos -= step
                f.seek(pos)
                buf = f.read(step) + buf
                lines = buf.strip().splitlines()
                if len(lines) > 1 or pos == 0:
                    return json.loads(lines[-1])["hash"]
        return GENESIS

    def append(self, events: list[dict]) -> str:
        with self._lock:
            prev = self._last_hash()
            with self.path.open("a", encoding="utf-8") as f:
                for event in events:
                    h = chain_hash(prev, event, self.key)
                    f.write(json.dumps({"event": event, "prev_hash": prev, "hash": h}, ensure_ascii=False,
                                       default=str) + "\n")
                    prev = h
                f.flush()
                os.fsync(f.fileno())
            return prev


def verify_file(path: str, key: bytes | None = None) -> tuple[bool, int, str]:
    """Zwraca (ok, liczba poprawnych linii, komunikat)."""
    prev = GENESIS
    count = 0
    with open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec["prev_hash"] != prev:
                return False, count, f"linia {lineno}: przerwany lancuch (prev_hash)"
            if chain_hash(prev, rec["event"], key) != rec["hash"]:
                return False, count, f"linia {lineno}: niezgodny skrot - zdarzenie zmienione"
            prev = rec["hash"]
            count += 1
    return True, count, "lancuch poprawny"
