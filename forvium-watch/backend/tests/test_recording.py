"""Podglad na zywo i nagrywanie sesji wsparcia."""

from __future__ import annotations

from datetime import timedelta

from sqlalchemy import text

from forvium.core.clock import clock

DASHBOARD = ('<nav class="card"><strong>Acme</strong></nav><div class="card"><h2>Dashboard</h2>'
             '<script>fetch("//evil")</script><img src=x onerror=alert(1)><input type="text" value="tajne">'
             '<div class="grid"><div class="card">CVE <h2>2</h2></div></div></div>')


def _snap(env, token, view, html):
    return env.client.post("/api/app/support/session/snapshot", headers=env.h(token), json={"view": view, "html": html})


def test_customer_sees_live_view_and_can_stop_session(env):
    s = env.open_support_session()
    assert _snap(env, s["support"], "Dashboard", DASHBOARD).json()["seq"] == 1
    live_url = env.org_url(f"/support-access/sessions/{s['session_id']}/live")
    live = env.client.get(live_url, headers=env.h(s["alice"])).json()
    assert live["active"] and live["current_view"] == "Dashboard" and live["latest_seq"] == 1
    html = live["snapshot"]["html"]
    assert "<h2>Dashboard</h2>" in html and "<script" not in html and "onerror" not in html and "tajne" not in html
    # Polling: bez nowego zrzutu nie ma ponownej tresci.
    assert env.client.get(live_url + "?after=1", headers=env.h(s["alice"])).json()["snapshot"] is None
    clock.advance(timedelta(seconds=1))
    _snap(env, s["support"], "CVE", "<table><tr><td>CVE-2024-6387</td></tr></table>")
    live = env.client.get(live_url + "?after=1", headers=env.h(s["alice"])).json()
    assert live["current_view"] == "CVE" and "CVE-2024-6387" in live["snapshot"]["html"]
    # Klient przerywa sesje z podgladu.
    env.client.post(env.org_url(f"/support-access/sessions/{s['session_id']}/terminate"), headers=env.h(s["alice"]))
    assert env.client.get(live_url, headers=env.h(s["alice"])).json()["active"] is False
    assert _snap(env, s["support"], "x", "<p>x</p>").status_code == 401


def test_recording_replay_and_forvium_access_is_audited(env):
    s = env.open_support_session()
    for i, view in enumerate(["Dashboard", "Jednostki", "CVE"]):
        clock.advance(timedelta(seconds=1))
        _snap(env, s["support"], view, f"<h2>{view}</h2><p>klatka {i}</p>")
    env.client.post("/api/app/support/session/end", headers=env.h(s["support"]))
    base = env.org_url(f"/support-access/sessions/{s['session_id']}/recording")
    frames = env.client.get(base, headers=env.h(s["alice"])).json()["frames"]
    assert [f["view"] for f in frames] == ["Dashboard", "Jednostki", "CVE"] and "html" not in frames[0]
    assert "klatka 1" in env.client.get(base + "/2", headers=env.h(s["alice"])).json()["html"]
    # Inna organizacja nie ma dostepu.
    carol = env.login_app("carol")
    assert env.client.get(env.org_url(f"/support-access/sessions/{s['session_id']}/recording", org="beta"),
                          headers=env.h(carol)).status_code == 404
    # Po stronie Forvium: tylko AUDIT_READ i kazde otwarcie w audycie.
    admin_base = f"/api/admin/support-access/sessions/{s['session_id']}/recording"
    assert env.client.get(admin_base, headers=env.h(s["op"])).status_code == 403
    marta = env.login_admin("marta")
    assert len(env.client.get(admin_base, headers=env.h(marta)).json()["frames"]) == 3
    assert env.client.get(admin_base + "/3", headers=env.h(marta)).status_code == 200
    viewed = env.audit(action="support.recording.viewed")
    assert viewed[0].actor_user_id == env.ids["users"]["marta"] and viewed[0].details == {"seq": 3}


def test_snapshots_are_encrypted_limited_and_purged(env):
    s = env.open_support_session()
    _snap(env, s["support"], "Dashboard", "<p>poufne dane klienta</p>")
    with env.app.state.db.sessionmaker() as db:
        raw = db.execute(text("SELECT html FROM support_session_snapshots")).scalar()
    assert raw.startswith("fwenc:v1:") and "poufne" not in raw
    # Limit czestotliwosci i rozmiaru.
    assert _snap(env, s["support"], "x", "<p>x</p>").status_code == 429
    clock.advance(timedelta(seconds=1))
    assert _snap(env, s["support"], "x", "<p>" + "a" * 400_000 + "</p>").status_code == 413
    # Zwykly klient nie moze wysylac zrzutow, a operator nie zapisze nic innego.
    assert _snap(env, s["alice"], "x", "<p>x</p>").status_code == 404
    # Retencja.
    from forvium.support_access.scheduler import run_sweep

    clock.advance(timedelta(days=31))
    run_sweep(env.app)
    with env.app.state.db.sessionmaker() as db:
        assert db.execute(text("SELECT count(*) FROM support_session_snapshots")).scalar() == 0
    assert env.audit(action="support.recording.purged")


def test_sanitizer_blocks_dangerous_markup():
    from forvium.security.html_sanitizer import sanitize_html

    dirty = ('<div onclick="x()"><a href="javascript:alert(1)">l</a><iframe src="//evil"></iframe>'
             '<textarea>haslo</p>dalej</textarea><style>*{}</style><svg><script>1</script></svg>'
             '<input type="password" value="p"><input type="checkbox" checked onfocus="x">'
             '<td colspan="2;x">c</td><p style="background:url(//evil)">t</p></div>')
    clean = sanitize_html(dirty)
    for bad in ("onclick", "javascript", "iframe", "haslo", "dalej", "style", "svg", "script", "password",
                "onfocus", "url("):
        assert bad not in clean, bad
    assert '<input type="checkbox" checked disabled>' in clean and "<p>t</p>" in clean
