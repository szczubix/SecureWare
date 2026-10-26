"""Integracje Audit Log z systemami SIEM (wysylka w zadaniu `audit-export`).

    FORVIUM_AUDIT_SIEM_TYPE   splunk | elastic | syslog
    FORVIUM_AUDIT_SIEM_URL    splunk:  https://splunk:8088            (HTTP Event Collector)
                              elastic: https://elastic:9200           (Bulk API, data stream)
                              syslog:  tls://siem:6514 albo tcp://siem:514  (RFC 5424, JSON);
                                       Wazuh remoted: tcp://wazuh:514?framing=lf
    FORVIUM_AUDIT_SIEM_TOKEN  splunk: token HEC; elastic: klucz API (base64 "id:key")
    FORVIUM_AUDIT_SIEM_INDEX  splunk: indeks; elastic: data stream (domyslnie logs-forvium.audit-default)
    FORVIUM_AUDIT_SIEM_CA_FILE   wlasny CA dla TLS (weryfikacji certyfikatu nie da sie wylaczyc)

Zdarzenia sa mapowane na Elastic Common Schema (ECS) - ten sam dokument trafia do Elastic,
jako `event` do Splunka i jako tresc komunikatu syslog (Wazuh dekoduje JSON). Kazde
zdarzenie ma stabilny `event.id`: przy ponowieniu partii odbiorca deduplikuje (Elastic:
`_id` = event.id, operacja `create`), wiec eksport jest "co najmniej raz" bez duplikatow
w Elastic. Partia zostaje oznaczona jako wyeksportowana dopiero po potwierdzeniu odbiorcy.
"""

from __future__ import annotations

import json
import socket
import ssl
import urllib.request
from datetime import UTC, datetime
from urllib.parse import parse_qs, urlparse

PRODUCT = {"vendor": "Forvium", "product": "Forvium Watch", "type": "audit"}
OUTCOME = {"success": "success", "denied": "failure", "failure": "failure"}


def _category(action: str) -> list[str]:
    if action.startswith(("identity.login", "identity.activation", "identity.password", "identity.mfa",
                          "identity.webauthn")):
        return ["authentication"]
    if action.startswith(("platform.operator", "platform.user", "organizations.member")):
        return ["iam"]
    if action.startswith(("support.", "break_glass.", "reports.", "support_tickets.")):
        return ["session"] if ".session." in action else ["process"]
    if action.startswith("security."):
        return ["intrusion_detection"]
    if action.startswith(("platform.organization", "support.settings")):
        return ["configuration"]
    return ["process"]


def to_ecs(e: dict) -> dict:
    """Zdarzenie audytu (audit.chain.event_dict) -> dokument ECS."""
    doc: dict = {
        "@timestamp": e["occurred_at"],
        "ecs": {"version": "8.11.0"},
        "event": {"id": e["id"], "kind": "event", "action": e["action"], "category": _category(e["action"]),
                  "outcome": OUTCOME.get(e["outcome"], "unknown"), "dataset": "forvium.audit",
                  "module": "forvium", "provider": "forvium-watch"},
        "observer": PRODUCT,
        "labels": {"forvium_actor_type": e["actor_type"], "forvium_break_glass": e["is_break_glass"]},
        "forvium": {"outcome": e["outcome"], "details": e.get("details") or {}},
    }
    if e.get("actor_user_id"):
        doc["user"] = {"id": e["actor_user_id"]}
    if e.get("on_behalf_of_user_id"):
        doc.setdefault("user", {})["target"] = {"id": e["on_behalf_of_user_id"]}
    if e.get("organization_id"):
        doc["organization"] = {"id": e["organization_id"]}
    if e.get("ip_address"):
        doc["source"] = {"ip": e["ip_address"]}
    if e.get("http_method") or e.get("status_code"):
        doc["http"] = {"request": {"method": e.get("http_method")}, "response": {"status_code": e.get("status_code")}}
    if e.get("route"):
        doc["url"] = {"path": e["route"]}
    if e.get("support_session_id") or e.get("support_request_id"):
        doc["forvium"]["support"] = {"session_id": e.get("support_session_id"),
                                     "request_id": e.get("support_request_id")}
    if e["is_break_glass"]:
        doc["tags"] = ["break_glass"]
    return doc


def _tls_context(ca_file: str | None) -> ssl.SSLContext:
    ctx = ssl.create_default_context(cafile=ca_file or None)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    if ca_file:
        # Wewnetrzne CA (np. generowane przez Elasticsearch) czesto nie maja rozszerzenia
        # "key usage", ktorego od Pythona 3.13 wymaga tryb scisly. Lancuch i nazwa hosta
        # sa nadal weryfikowane (jak w curl/requests).
        ctx.verify_flags &= ~getattr(ssl, "VERIFY_X509_STRICT", 0)
    return ctx


def _post(url: str, body: bytes, headers: dict, ca_file: str | None, timeout: int) -> tuple[int, bytes]:
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    handlers = [urllib.request.HTTPSHandler(context=_tls_context(ca_file))]
    opener = urllib.request.build_opener(*handlers)
    with opener.open(req, timeout=timeout) as resp:  # noqa: S310 - URL z konfiguracji
        return resp.status, resp.read()


class SplunkHecSink:
    """Splunk HTTP Event Collector: /services/collector/event, partia JSON-ow (jeden na zdarzenie)."""

    def __init__(self, url: str, token: str, index: str | None, ca_file: str | None, timeout: int = 15) -> None:
        self.url = url.rstrip("/") + "/services/collector/event"
        self.token, self.index, self.ca_file, self.timeout = token, index, ca_file, timeout

    def send(self, events: list[dict]) -> str | None:
        lines = []
        for e in events:
            ts = datetime.fromisoformat(e["occurred_at"].replace("Z", "+00:00")).replace(tzinfo=UTC).timestamp()
            item = {"time": round(ts, 3), "source": "forvium-watch", "sourcetype": "forvium:audit:ecs",
                    "event": to_ecs(e)}
            if self.index:
                item["index"] = self.index
            lines.append(json.dumps(item, ensure_ascii=False, default=str))
        status, body = _post(self.url, "\n".join(lines).encode(),
                             {"Authorization": f"Splunk {self.token}", "Content-Type": "application/json"},
                             self.ca_file, self.timeout)
        reply = json.loads(body or b"{}")
        if status >= 300 or reply.get("code", 0) != 0:
            raise RuntimeError(f"Splunk HEC: HTTP {status}, {reply.get('text')}")
        return None


class ElasticBulkSink:
    """Elasticsearch / OpenSearch Bulk API do data streamu; _id = event.id (deduplikacja)."""

    def __init__(self, url: str, api_key: str | None, index: str | None, ca_file: str | None,
                 timeout: int = 15) -> None:
        self.index = index or "logs-forvium.audit-default"
        self.url = url.rstrip("/") + f"/{self.index}/_bulk"
        self.api_key, self.ca_file, self.timeout = api_key, ca_file, timeout

    def send(self, events: list[dict]) -> str | None:
        lines = []
        for e in events:
            lines.append(json.dumps({"create": {"_id": e["id"]}}))
            lines.append(json.dumps(to_ecs(e), ensure_ascii=False, default=str))
        headers = {"Content-Type": "application/x-ndjson"}
        if self.api_key:
            headers["Authorization"] = f"ApiKey {self.api_key}"
        status, body = _post(self.url, ("\n".join(lines) + "\n").encode(), headers, self.ca_file, self.timeout)
        reply = json.loads(body or b"{}")
        if status >= 300:
            raise RuntimeError(f"Elastic bulk: HTTP {status}")
        if reply.get("errors"):
            # 409 = dokument o tym _id juz jest (ponowienie partii) - to nie blad.
            bad = [i for i in reply.get("items", []) if list(i.values())[0].get("status", 200) not in (200, 201, 409)]
            if bad:
                first = list(bad[0].values())[0].get("error", {})
                raise RuntimeError(f"Elastic bulk: {len(bad)} odrzuconych, np. {first.get('type')}: {first.get('reason')}")
        return None


class SyslogSink:
    """RFC 5424 przez TCP lub TLS (RFC 5425, ramkowanie octet-counting); tresc = dokument ECS w JSON.

    Wazuh: <remote><connection>syslog</connection><protocol>tcp</protocol>... oraz dekoder JSON
    (deploy/siem/wazuh). Facility local4, poziom: notice (sukces) / warning (odmowa, Break Glass).
    """

    def __init__(self, url: str, ca_file: str | None, timeout: int = 15, hostname: str | None = None) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in ("tcp", "tls"):
            raise ValueError("FORVIUM_AUDIT_SIEM_URL dla syslog: tcp://host:port albo tls://host:port")
        # Ramkowanie: octet-counting (RFC 5425/6587, domyslne, np. rsyslog/syslog-ng) albo
        # znak nowej linii (?framing=lf - np. Wazuh remoted). JSON nie zawiera znakow nowej linii.
        framing = parse_qs(parsed.query).get("framing", ["octet"])[0]
        if framing not in ("octet", "lf"):
            raise ValueError("framing: octet albo lf")
        self.framing = framing
        self.tls = parsed.scheme == "tls"
        self.host, self.port = parsed.hostname, parsed.port or (6514 if self.tls else 514)
        self.ca_file, self.timeout = ca_file, timeout
        self.hostname = hostname or socket.gethostname()

    def _frame(self, e: dict) -> bytes:
        severity = 4 if (e["outcome"] != "success" or e["is_break_glass"]) else 5
        pri = 20 * 8 + severity  # local4
        msg = json.dumps(to_ecs(e), ensure_ascii=False, default=str)
        line = f"<{pri}>1 {e['occurred_at']} {self.hostname} forvium-watch - {e['action']} - {msg}".encode()
        if self.framing == "lf":
            return line + b"\n"
        return str(len(line)).encode() + b" " + line

    def send(self, events: list[dict]) -> str | None:
        raw = socket.create_connection((self.host, self.port), timeout=self.timeout)
        conn = _tls_context(self.ca_file).wrap_socket(raw, server_hostname=self.host) if self.tls else raw
        with conn:
            conn.sendall(b"".join(self._frame(e) for e in events))
        return None


def sink_from_settings(settings):
    kind = (settings.audit_siem_type or "").lower()
    if not kind:
        return None
    url, token = settings.audit_siem_url, settings.audit_siem_token or None
    index, ca = settings.audit_siem_index or None, settings.audit_siem_ca_file or None
    if not url:
        raise ValueError("FORVIUM_AUDIT_SIEM_URL jest wymagany, gdy ustawiono FORVIUM_AUDIT_SIEM_TYPE")
    if kind == "splunk":
        if not token:
            raise ValueError("Splunk HEC wymaga FORVIUM_AUDIT_SIEM_TOKEN")
        return SplunkHecSink(url, token, index, ca)
    if kind == "elastic":
        return ElasticBulkSink(url, token, index, ca)
    if kind == "syslog":
        return SyslogSink(url, ca)
    raise ValueError(f"Nieznany FORVIUM_AUDIT_SIEM_TYPE: {kind} (splunk | elastic | syslog)")
