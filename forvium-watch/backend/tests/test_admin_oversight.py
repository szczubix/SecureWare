"""Widok audytu i nadzor sesji w panelu admin."""

from __future__ import annotations

import csv
import io


def test_audit_filters_and_pagination(env):
    s = env.open_support_session()
    h = env.h(s["support"])
    env.client.get(env.org_url("/dashboard"), headers=h)
    env.client.get(env.org_url("/export"), headers=h)

    marta = env.login_admin("marta")
    hm = env.h(marta)
    ola = env.ids["users"]["ola"]
    r = env.client.get(f"/api/admin/audit?operator_id={ola}&action_prefix=support.api_call", headers=hm).json()
    assert r["total"] == 2 and {e["route"] for e in r["events"]} == {
        "/api/app/orgs/{org_id}/dashboard", "/api/app/orgs/{org_id}/export"}
    r = env.client.get(f"/api/admin/audit?operator_id={ola}&outcome=denied&action_prefix=support.api_call",
                       headers=hm).json()
    assert r["total"] == 1
    r = env.client.get("/api/admin/audit?ticket=FW-1001&limit=2&offset=0", headers=hm).json()
    assert r["total"] > 2 and len(r["events"]) == 2
    page2 = env.client.get("/api/admin/audit?ticket=FW-1001&limit=2&offset=2", headers=hm).json()
    assert {e["id"] for e in r["events"]}.isdisjoint({e["id"] for e in page2["events"]})


def test_audit_requires_permission(env):
    op = env.login_admin("ola")  # support_l2 - bez AUDIT_READ
    assert env.client.get("/api/admin/audit", headers=env.h(op)).status_code == 403


def test_audit_csv_export_is_itself_audited(env):
    env.open_support_session()
    marta = env.login_admin("marta")
    r = env.client.get("/api/admin/audit/export.csv?ticket=FW-1001", headers=env.h(marta))
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/csv")
    rows = list(csv.reader(io.StringIO(r.text)))
    assert rows[0][0] == "occurred_at" and len(rows) > 3
    exported = env.audit(action="audit.exported")
    assert exported and exported[0].actor_user_id == env.ids["users"]["marta"]


def test_supervisor_sees_and_terminates_sessions(env):
    s = env.open_support_session()
    marta = env.login_admin("marta")
    sessions = env.client.get("/api/admin/support-access/oversight/sessions?status=active",
                              headers=env.h(marta)).json()["sessions"]
    assert [x["id"] for x in sessions] == [s["session_id"]]
    assert sessions[0]["operator_email"] == "ola@forvium.com"
    r = env.client.post(f"/api/admin/support-access/oversight/sessions/{s['session_id']}/terminate",
                        headers=env.h(marta))
    assert r.status_code == 200 and r.json()["session"]["end_reason"] == "terminated_by_supervisor"
    assert env.client.get(env.org_url("/dashboard"), headers=env.h(s["support"])).status_code == 401
    ended = env.audit(action="support.session.ended", support_session_id=s["session_id"])
    assert ended[0].actor_user_id == env.ids["users"]["marta"] and ended[0].actor_type == "operator"
    # Zwykly operator nie ma nadzoru.
    assert env.client.get("/api/admin/support-access/oversight/sessions",
                          headers=env.h(s["op"])).status_code == 403
