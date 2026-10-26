"""Integracje SIEM: mapowanie ECS, Splunk HEC, Elastic Bulk, syslog RFC 5424 (lokalne odbiorniki testowe)."""

from __future__ import annotations

import json
import socket
import threading
from datetime import timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from conftest import make_env
from forvium.audit.export import run_audit_export
from forvium.audit.siem import ElasticBulkSink, SplunkHecSink, SyslogSink, sink_from_settings, to_ecs
from forvium.core.clock import clock

EVENT = {
    "id": "e1", "occurred_at": "2026-10-26T10:00:00Z", "action": "support.api_call", "outcome": "denied",
    "actor_user_id": "op1", "actor_type": "support", "on_behalf_of_user_id": "u1", "organization_id": "org1",
    "support_session_id": "s1", "support_request_id": "r1", "is_break_glass": True, "http_method": "POST",
    "route": "/api/app/orgs/{org_id}/settings", "status_code": 403, "ip_address": "203.0.113.7", "details": {"x": 1},
}


def test_ecs_mapping():
    doc = to_ecs(EVENT)
    assert doc["@timestamp"] == "2026-10-26T10:00:00Z"
    assert doc["event"] == {"id": "e1", "kind": "event", "action": "support.api_call", "category": ["process"],
                            "outcome": "failure", "dataset": "forvium.audit", "module": "forvium",
                            "provider": "forvium-watch"}
    assert doc["user"] == {"id": "op1", "target": {"id": "u1"}}
    assert doc["source"]["ip"] == "203.0.113.7" and doc["http"]["response"]["status_code"] == 403
    assert doc["forvium"]["support"] == {"session_id": "s1", "request_id": "r1"} and doc["tags"] == ["break_glass"]
    assert to_ecs({**EVENT, "action": "identity.login.operator"})["event"]["category"] == ["authentication"]


class _Recorder(BaseHTTPRequestHandler):
    requests: list = []
    reply: dict = {}
    status: int = 200

    def do_POST(self):  # noqa: N802
        body = self.rfile.read(int(self.headers["Content-Length"]))
        type(self).requests.append({"path": self.path, "headers": dict(self.headers), "body": body})
        out = json.dumps(type(self).reply).encode()
        self.send_response(type(self).status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)

    def log_message(self, *args):
        pass


@pytest.fixture
def http_server(monkeypatch):
    for var in ("HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy"):
        monkeypatch.delenv(var, raising=False)
    handler = type("H", (_Recorder,), {"requests": [], "reply": {}, "status": 200})
    server = HTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_port}", handler
    server.shutdown()


def test_splunk_hec(http_server):
    url, h = http_server
    h.reply = {"text": "Success", "code": 0}
    SplunkHecSink(url, "tok-123", "security", None).send([EVENT, {**EVENT, "id": "e2"}])
    req = h.requests[0]
    assert req["path"] == "/services/collector/event"
    assert req["headers"]["Authorization"] == "Splunk tok-123"
    items = [json.loads(line) for line in req["body"].decode().splitlines()]
    assert [i["event"]["event"]["id"] for i in items] == ["e1", "e2"]
    assert items[0]["index"] == "security" and items[0]["sourcetype"] == "forvium:audit:ecs"
    h.reply = {"text": "Invalid token", "code": 4}
    with pytest.raises(RuntimeError):
        SplunkHecSink(url, "zly", None, None).send([EVENT])


def test_elastic_bulk_with_dedup(http_server):
    url, h = http_server
    h.reply = {"errors": True, "items": [{"create": {"status": 201}}, {"create": {"status": 409}}]}
    ElasticBulkSink(url, "a2V5", None, None).send([EVENT, {**EVENT, "id": "e2"}])  # 409 = juz jest
    req = h.requests[0]
    assert req["path"] == "/logs-forvium.audit-default/_bulk"
    assert req["headers"]["Authorization"] == "ApiKey a2V5"
    lines = req["body"].decode().splitlines()
    assert json.loads(lines[0]) == {"create": {"_id": "e1"}} and json.loads(lines[1])["event"]["id"] == "e1"
    h.reply = {"errors": True, "items": [{"create": {"status": 400, "error": {"type": "mapper_parsing_exception",
                                                                            "reason": "zly typ"}}}]}
    with pytest.raises(RuntimeError, match="mapper_parsing_exception"):
        ElasticBulkSink(url, None, None, None).send([EVENT])


def test_syslog_rfc5424_octet_counting():
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    received = bytearray()

    def accept():
        conn, _ = server.accept()
        with conn:
            while chunk := conn.recv(65536):
                received.extend(chunk)

    t = threading.Thread(target=accept)
    t.start()
    SyslogSink(f"tcp://127.0.0.1:{server.getsockname()[1]}", None, hostname="watch01").send(
        [EVENT, {**EVENT, "id": "e2", "outcome": "success", "is_break_glass": False}])
    t.join(5)
    server.close()
    frames, data = [], bytes(received)
    while data:
        length, rest = data.split(b" ", 1)
        frames.append(rest[:int(length)].decode())
        data = rest[int(length):]
    assert len(frames) == 2
    assert frames[0].startswith("<164>1 2026-10-26T10:00:00Z watch01 forvium-watch - support.api_call - {")
    assert frames[1].startswith("<165>1 ")  # local4.notice dla sukcesu
    assert json.loads(frames[0].split(" - ", 2)[2])["event"]["id"] == "e1"


def test_syslog_lf_framing_for_wazuh():
    sink = SyslogSink("tcp://127.0.0.1:514?framing=lf", None, hostname="h")
    frame = sink._frame(EVENT)
    assert frame.startswith(b"<164>1 ") and frame.endswith(b"}\n") and frame.count(b"\n") == 1
    with pytest.raises(ValueError):
        SyslogSink("tcp://x:514?framing=zle", None)


def test_settings_validation():
    class S:
        audit_siem_type, audit_siem_url, audit_siem_token, audit_siem_index, audit_siem_ca_file = "splunk", "x", "", "", ""
    with pytest.raises(ValueError):
        sink_from_settings(S)
    S.audit_siem_type, S.audit_siem_url = "syslog", "udp://x:514"
    with pytest.raises(ValueError):
        sink_from_settings(S)
    S.audit_siem_type = ""
    assert sink_from_settings(S) is None


def test_export_job_sends_to_siem_once(tmp_path, http_server):
    url, h = http_server
    h.reply = {"errors": False, "items": []}
    env = make_env(tmp_path, audit_siem_type="elastic", audit_siem_url=url)
    env.login_admin("ola")
    clock.advance(timedelta(seconds=30))
    assert run_audit_export(env.app) > 0
    sent = [json.loads(line) for r in h.requests for line in r["body"].decode().splitlines()[1::2]]
    assert any(d["event"]["action"] == "identity.login.operator" for d in sent)
    # Kolejny przebieg nie wysyla tego samego ponownie.
    count = len(h.requests)
    run_audit_export(env.app)
    assert len(h.requests) == count
