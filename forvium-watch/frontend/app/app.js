// app.forvium.com - panel klienta (tryb zwykly i tryb wsparcia Forvium).
(() => {
  const API = window.FORVIUM_API;
  const SUPPORT_KEY = "fw_support_token";
  const USER_KEY = "fw_user_token";
  const root = document.getElementById("root");
  const banner = document.getElementById("support-banner");

  const supportToken = sessionStorage.getItem(SUPPORT_KEY);
  const token = () => supportToken || sessionStorage.getItem(USER_KEY);
  const SCOPE_LABELS = {
    dashboard: "Dashboard organizacji",
    units: "Struktura jednostek",
    technologies_cve: "Technologie i CVE",
    diagnostics: "Błędy i stan konfiguracji",
  };

  function el(tag, attrs = {}, ...children) {
    const node = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (k.startsWith("on")) node[k] = v;
      else if (v !== false && v != null) node.setAttribute(k, v === true ? "" : v);
    }
    for (const c of children.flat()) node.append(c instanceof Node ? c : document.createTextNode(String(c ?? "")));
    return node;
  }

  async function api(path, opts = {}) {
    const headers = { "Content-Type": "application/json" };
    if (token()) headers.Authorization = "Bearer " + token();
    const r = await fetch(API + path, { ...opts, headers, body: opts.body ? JSON.stringify(opts.body) : undefined });
    const data = await r.json().catch(() => ({}));
    if (r.status === 401 && supportToken) supportEnded();
    if (!r.ok) throw Object.assign(new Error(data.message || "Błąd " + r.status), { status: r.status, code: data.error });
    return data;
  }

  const fmt = (iso) => (iso ? new Date(iso).toLocaleString("pl-PL") : "—");
  const card = (...children) => el("div", { class: "card" }, ...children);
  const checkedValues = (labels) => labels.map((l) => l.querySelector("input")).filter((i) => i.checked).map((i) => i.value);
  const askMfa = (what) => prompt(`${what}\nPotwierdź kodem MFA z aplikacji uwierzytelniającej:`);

  // Podglad zrzutu widoku operatora: iframe w piaskownicy BEZ skryptow (tresc i tak jest sanityzowana na serwerze).
  function snapshotFrame() {
    const frame = el("iframe", { class: "snapshot", sandbox: "", title: "Widok operatora Forvium", referrerpolicy: "no-referrer" });
    frame.show = (html) => {
      frame.srcdoc = `<!doctype html><html><head><link rel="stylesheet" href="${location.origin}/styles.css"></head>` +
        `<body class="snapshot-body"><main>${html}</main></body></html>`;
    };
    return frame;
  }

  // ------------------------------------------------------------- tryb wsparcia
  let bannerTimer;
  function supportEnded() {
    sessionStorage.removeItem(SUPPORT_KEY);
    clearInterval(bannerTimer);
    banner.hidden = false;
    banner.replaceChildren(el("span", { class: "title" }, "Sesja wsparcia Forvium zakończona"));
    root.replaceChildren(card("Dostęp serwisowy wygasł lub został zakończony. Możesz zamknąć te kartę."));
  }

  // Zrzut biezacego widoku dla klienta (podglad na zywo i nagranie). Pola formularzy nie sa wysylane.
  async function captureView(label) {
    if (!supportToken) return;
    const clone = root.cloneNode(true);
    clone.querySelectorAll("input:not([type=checkbox]):not([type=radio]), textarea, select").forEach((n) => n.remove());
    try {
      await api("/api/app/support/session/snapshot", { method: "POST", body: { view: label, html: clone.innerHTML } });
    } catch (_) { /* zrzut nie moze blokowac pracy - np. limit czestotliwosci */ }
  }

  async function startSupportMode() {
    const info = await api("/api/app/support/session");
    let remaining = info.remaining_seconds;
    const timeEl = el("span");
    const tick = () => {
      if (remaining <= 0) return supportEnded();
      const m = Math.floor(remaining / 60), s = String(remaining % 60).padStart(2, "0");
      timeEl.textContent = `Pozostały czas: ${m}:${s}`;
      remaining -= 1;
    };
    banner.hidden = false;
    banner.replaceChildren(
      el("span", { class: "title" }, info.banner),
      el("span", { class: "meta" },
        el("span", {}, "Organizacja: ", info.organization.name),
        el("span", {}, "Operator: ", info.operator_id),
        el("span", {}, "Zgłoszenie: ", info.ticket_number),
        el("span", {}, "Klient widzi ten ekran na żywo"),
        timeEl),
      el("button", { onclick: async () => {
        try { await api("/api/app/support/session/end", { method: "POST" }); } catch (_) {}
        supportEnded();
      } }, "Zakończ dostęp"),
    );
    tick();
    bannerTimer = setInterval(tick, 1000);
    // Rewalidacja co 15 s: przedluzenie sesji, cofniecie zgody, zakonczenie przez klienta.
    setInterval(() => api("/api/app/support/session").then((i) => { remaining = i.remaining_seconds; }).catch(() => {}), 15000);
    document.getElementById("who").textContent = "Widok użytkownika: " + info.reference_user.display_name;
    renderOrg(info.organization, info.permissions);
  }

  // ---------------------------------------------------------------- logowanie
  function renderLogin(error) {
    const form = el("form", { class: "card", onsubmit: async (e) => {
      e.preventDefault();
      try {
        const r = await api("/api/app/auth/login", { method: "POST", body: Object.fromEntries(new FormData(form)) });
        sessionStorage.setItem(USER_KEY, r.token);
        renderHome();
      } catch (err) { renderLogin(err.message); }
    } },
      el("h2", {}, "Logowanie"),
      el("label", {}, "E-mail"), el("input", { name: "email", type: "email", required: true, autocomplete: "username" }),
      el("label", {}, "Hasło"), el("input", { name: "password", type: "password", required: true, autocomplete: "current-password" }),
      el("label", {}, "Kod MFA"), el("input", { name: "mfa_code", inputmode: "numeric", autocomplete: "one-time-code" }),
      el("p", { class: "error" }, error || ""),
      el("button", { type: "submit" }, "Zaloguj"));
    root.replaceChildren(form);
  }

  async function renderHome() {
    let me;
    try { me = await api("/api/app/me"); } catch (_) { return renderLogin(); }
    document.getElementById("who").textContent = me.user.display_name;
    if (me.organizations.length === 1) return renderOrg(me.organizations[0]);
    root.replaceChildren(card(el("h2", {}, "Organizacje"),
      ...me.organizations.map((o) => el("p", {}, el("a", { href: "#", onclick: (e) => { e.preventDefault(); renderOrg(o); } }, o.name)))));
  }

  // --------------------------------------------------------------- organizacja
  function renderOrg(org, supportPermissions) {
    const content = el("div");
    // Kazdy widok renderuje sie do wlasnego, swiezego kontenera - wynik wolniejszego,
    // nieaktualnego widoku trafia do odpietego elementu i niczego nie nadpisuje.
    let current = null;
    const show = async (label, fn) => {
      const pane = el("div");
      current = pane;
      content.replaceChildren(pane);
      await fn(pane);
      if (pane === current) captureView(label);
    };
    const views = {
      "Dashboard": (pane) => viewDashboard(org, pane),
      "Jednostki": (pane) => viewList(org, pane, "/units", "units", ["name"]),
      "Technologie": (pane) => viewList(org, pane, "/technologies", "technologies", ["name", "version"]),
      "CVE": (pane) => viewList(org, pane, "/cves", "cves", ["id", "severity", "technology"]),
      "Diagnostyka": (pane) => viewDiagnostics(org, pane),
    };
    if (!supportPermissions) {
      views["Dostęp serwisowy"] = (pane) => viewSupportAccess(org, pane);
      views["Powiadomienia"] = (pane) => viewNotifications(pane);
    }
    const nav = el("nav", { class: "card" }, el("strong", {}, org.name, " "),
      ...Object.entries(views).map(([label, fn]) => el("a", { onclick: () => show(label, fn) }, label)));
    root.replaceChildren(nav, content);
    show("Dashboard", views["Dashboard"]);
  }

  async function guarded(content, fn) {
    try { await fn(); } catch (e) {
      content.replaceChildren(el("div", { class: "card error" },
        e.code === "forbidden_in_support_mode" ? "Ta sekcja nie jest objęta zgoda na dostęp serwisowy." : e.message));
    }
  }

  function viewDashboard(org, content) {
    return guarded(content, async () => {
      const d = await api(`/api/app/orgs/${org.id}/dashboard`);
      const tiles = [["Jednostki", d.units], ["Technologie", d.technologies]];
      if (d.cves) tiles.push(["CVE", d.cves.total], ["Krytyczne", d.cves.critical], ["Wysokie", d.cves.high]);
      content.replaceChildren(card(el("h2", {}, "Dashboard"),
        el("div", { class: "grid" }, ...tiles.map(([k, v]) => card(el("div", { class: "muted" }, k), el("h2", {}, v))))));
    });
  }

  function viewList(org, content, path, key, cols) {
    return guarded(content, async () => {
      const d = await api(`/api/app/orgs/${org.id}${path}`);
      content.replaceChildren(card(el("table", {},
        el("tr", {}, ...cols.map((c) => el("th", {}, c))),
        ...d[key].map((row) => el("tr", {}, ...cols.map((c) => el("td", {}, row[c])))))));
    });
  }

  function viewDiagnostics(org, content) {
    return guarded(content, async () => {
      const [cfg, errs] = await Promise.all([api(`/api/app/orgs/${org.id}/config/status`), api(`/api/app/orgs/${org.id}/errors`)]);
      content.replaceChildren(
        card(el("h3", {}, "Stan konfiguracji"),
          el("p", {}, "SMTP skonfigurowany: ", cfg.smtp_configured ? "tak" : "nie"),
          el("p", {}, "Webhooki: ", cfg.webhooks_count, " · Sekrety: ", cfg.secrets_count, " · Plan: ", cfg.subscription_plan)),
        card(el("h3", {}, "Błędy"), el("table", {},
          ...errs.errors.map((e) => el("tr", {}, el("td", {}, fmt(e.created_at)), el("td", {}, e.level), el("td", {}, e.component), el("td", {}, e.message))))));
    });
  }

  // ------------------------------------------------- dostep serwisowy (klient)
  function viewSupportAccess(org, content) {
    return guarded(content, async () => {
      const [h, settings] = await Promise.all([api(`/api/app/orgs/${org.id}/support-access`),
        api(`/api/app/orgs/${org.id}/support-access/settings`)]);
      const reload = () => viewSupportAccess(org, content);
      const { units } = await api(`/api/app/orgs/${org.id}/units`).catch(() => ({ units: [] }));
      const unitName = Object.fromEntries(units.map((u) => [u.id, u.name]));
      const decisionCards = h.requests.filter((r) => r.status === "pending" || r.status === "pending_customer_confirmation")
        .map((r) => decisionCard(org, r, units, reload));

      const consentRows = h.requests.filter((r) => r.consent).map((r) => {
        const c = r.consent;
        const active = !c.revoked_at && new Date(c.valid_until) > new Date();
        const scopeText = c.scopes.map((s) => SCOPE_LABELS[s] || s).join(", ") +
          (c.unit_ids ? " · jednostki: " + c.unit_ids.map((id) => unitName[id] || id).join(", ") : "");
        const basis = { customer: c.second_approver_user_id ? "decyzja klienta (2 osoby)" : "decyzja klienta",
          standing: "zgoda stała", break_glass: el("span", { class: "danger-text" }, "BREAK GLASS") }[c.basis] || c.basis;
        return el("tr", {}, el("td", {}, r.ticket_number), el("td", {}, r.operator_id), el("td", {}, basis), el("td", {}, scopeText),
          el("td", {}, fmt(c.valid_until)), el("td", {}, c.revoked_at ? "cofnięta " + fmt(c.revoked_at) : active ? "aktywna" : "wygasła"),
          el("td", {}, active ? el("button", { class: "danger", onclick: async () => {
            await api(`/api/app/orgs/${org.id}/support-access/consents/${c.id}/revoke`, { method: "POST" }).catch((e) => alert(e.message));
            reload();
          } }, "Cofnij zgodę") : ""));
      });

      const panel = el("div");
      const sessionRows = h.sessions.map((s) => el("tr", {},
        el("td", {}, fmt(s.started_at)), el("td", {}, s.operator_id), el("td", {}, s.ticket_number),
        el("td", {}, el("span", { class: "pill" }, s.status), s.extensions_count ? ` (przedłużona ${s.extensions_count}x)` : ""),
        el("td", {}, fmt(s.ended_at || s.expires_at)),
        el("td", { class: "row" },
          s.status === "active" ? el("button", { onclick: () => livePanel(org, s, panel, reload) }, "Podgląd na żywo") : "",
          el("button", { class: "secondary", onclick: () => replayPanel(org, s, panel) }, "Nagranie"),
          el("button", { class: "secondary", onclick: async () => {
            const a = await api(`/api/app/orgs/${org.id}/support-access/sessions/${s.id}/activity`);
            panel.replaceChildren(card(el("h3", {}, "Aktywność sesji ", s.id), el("table", {},
              ...a.events.map((e) => el("tr", {}, el("td", {}, fmt(e.occurred_at)), el("td", {}, e.action),
                el("td", {}, e.method || ""), el("td", {}, e.route || ""), el("td", {}, e.outcome))))));
          } }, "Aktywność"),
          s.status === "active" ? el("button", { class: "danger", onclick: async () => {
            await api(`/api/app/orgs/${org.id}/support-access/sessions/${s.id}/terminate`, { method: "POST" }).catch((e) => alert(e.message));
            reload();
          } }, "Zakończ") : "")));

      content.replaceChildren(
        card(el("h2", {}, "Dostęp serwisowy Forvium"),
          el("p", { class: "muted" }, "Operator Forvium może zobaczyć Twoją organizację wyłącznie w trybie tylko do odczytu, w zakresie i czasie, które zatwierdzisz. Trwającą sesję możesz oglądać na żywo i przerwać w każdej chwili.")),
        settingsCard(org, settings, reload),
        ...(decisionCards.length ? decisionCards : [el("div", { class: "card muted" }, "Brak oczekujących próśb.")]),
        card(el("h3", {}, "Zgody"), el("table", {},
          el("tr", {}, ...["Zgłoszenie", "Operator", "Podstawa", "Zakres", "Ważna do", "Status", ""].map((t) => el("th", {}, t))), ...consentRows)),
        standingSection(org, h.standing_consents || [], units, reload, settings.dual_approval),
        card(el("h3", {}, "Historia sesji"), el("table", {},
          el("tr", {}, ...["Start", "Operator", "Zgłoszenie", "Status", "Koniec", ""].map((t) => el("th", {}, t))), ...sessionRows)),
        reportsCard(org),
        panel);
    });
  }

  // Pobranie pliku z API (naglowek Authorization, wiec nie zwykly link).
  async function download(path, fallbackName) {
    const r = await fetch(API + path, { headers: { Authorization: "Bearer " + token() } });
    if (!r.ok) throw new Error("Nie udało się pobrać pliku (" + r.status + ")");
    const name = (r.headers.get("Content-Disposition") || "").match(/filename="([^"]+)"/);
    const url = URL.createObjectURL(await r.blob());
    const a = el("a", { href: url, download: name ? name[1] : fallbackName });
    document.body.append(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 10000);
  }

  // Miesieczne raporty dostepu serwisowego (PDF) - tworzone automatycznie po koncu miesiaca.
  function reportsCard(org) {
    const body = el("div", {}, el("p", { class: "muted" }, "Ładowanie…"));
    const load = async () => {
      try {
        const { reports } = await api(`/api/app/orgs/${org.id}/access-reports`);
        body.replaceChildren(reports.length ? el("table", {},
          el("tr", {}, ...["Okres", "Utworzono", "SHA-256", ""].map((t) => el("th", {}, t))),
          ...reports.map((r) => el("tr", {}, el("td", {}, r.period_label), el("td", {}, fmt(r.created_at)),
            el("td", { class: "mono", title: r.sha256 }, r.sha256.slice(0, 16) + "…"),
            el("td", {}, el("button", { class: "secondary", onclick: () => download(
              `/api/app/orgs/${org.id}/access-reports/${r.id}/pdf`, `raport-${r.period_start}.pdf`).catch((e) => alert(e.message)) }, "Pobierz PDF")))))
          : el("p", { class: "muted" }, "Pierwszy raport pojawi się po zakończeniu miesiąca."));
      } catch (e) { body.replaceChildren(el("p", { class: "error" }, e.message)); }
    };
    const month = el("input", { type: "month" });
    load();
    return card(el("h3", {}, "Raporty dostępu"),
      el("p", { class: "muted" }, "Co miesiąc: wszystkie prośby Forvium o dostęp, decyzje, sesje wsparcia (czas, zakres, oglądane widoki, zablokowane próby) i zmiany zgód. Skrót SHA-256 pozwala sprawdzić, że plik nie został zmieniony."),
      body,
      el("div", { class: "row" }, month, el("button", { class: "secondary", onclick: async () => {
        if (!month.value) return;
        const [year, m] = month.value.split("-").map(Number);
        try {
          await api(`/api/app/orgs/${org.id}/access-reports`, { method: "POST", body: { year, month: m } });
          load();
        } catch (e) { alert(e.message); }
      } }, "Utwórz raport za wybrany miesiąc")));
  }

  // Zatwierdzanie prosby - pierwsze albo (przy zatwierdzaniu przez dwie osoby) potwierdzenie przez drugą osobę.
  function decisionCard(org, r, units, reload) {
    const confirming = r.status === "pending_customer_confirmation";
    const grant = r.pending_grant || {};
    const scopeList = confirming ? grant.scopes : r.scopes;
    const scopes = scopeList.map((s) => el("label", {}, el("input", { type: "checkbox", value: s, checked: true }), " ", SCOPE_LABELS[s] || s));
    const allowedUnits = confirming && grant.unit_ids ? units.filter((u) => grant.unit_ids.includes(u.id)) : units;
    // Pusty wybor = wszystkie dozwolone jednostki; zaznaczenie obejmuje tez jednostki podrzedne.
    const unitBoxes = allowedUnits.map((u) => el("label", {}, el("input", { type: "checkbox", value: u.id, checked: confirming && !!grant.unit_ids }), " ", u.name));
    const hours = el("input", { type: "number", min: 1, max: confirming ? grant.valid_hours : 168, value: confirming ? grant.valid_hours : 24 });
    const note = el("input", { placeholder: "Notatka (opcjonalnie)" });
    return el("div", { class: "card" + (confirming ? " highlight" : "") },
      el("h3", {}, confirming ? "Potwierdź dostęp (druga osoba) · " : "Prośba o dostęp · ", r.ticket_number),
      confirming ? el("p", { class: "danger-text" }, "Pierwsze zatwierdzenie: ", r.first_approved_by_user_id, ". Twoja organizacja wymaga drugiej osoby - możesz tylko potwierdzić lub zawęzić zakres.") : "",
      el("p", {}, "Operator Forvium: ", r.operator_id),
      el("p", {}, "Powód: ", r.reason),
      el("p", {}, "Tryb: ", el("span", { class: "pill" }, r.access_level), " · Czas sesji: ", r.duration_minutes, " min"),
      el("label", {}, "Zakres zgody"), ...scopes,
      ...(unitBoxes.length ? [el("label", {}, "Ogranicz do jednostek (brak zaznaczenia = wszystkie dozwolone)"), ...unitBoxes] : []),
      el("label", {}, "Zgoda ważna (godziny)"), hours,
      el("label", {}, "Notatka"), note,
      el("div", { class: "row spaced" },
        el("button", { onclick: async () => {
          const unitIds = checkedValues(unitBoxes);
          try {
            const res = await api(`/api/app/orgs/${org.id}/support-access/requests/${r.id}/approve`, { method: "POST",
              body: { scopes: checkedValues(scopes), unit_ids: unitIds.length ? unitIds : null,
                      valid_hours: Number(hours.value), note: note.value } });
            if (res.status === "pending_customer_confirmation") alert("Zapisano. Dostęp zacznie obowiązywać po potwierdzeniu przez drugą osobę.");
          } catch (e) { alert(e.message); }
          reload();
        } }, confirming ? "Potwierdź" : "Zatwierdź"),
        el("button", { class: "danger", onclick: async () => {
          await api(`/api/app/orgs/${org.id}/support-access/requests/${r.id}/reject`, { method: "POST", body: { note: note.value } }).catch((e) => alert(e.message));
          reload();
        } }, "Odrzuć")));
  }

  function settingsCard(org, settings, reload) {
    const put = async (enabled) => {
      const code = askMfa(enabled ? "Włączenie zatwierdzania przez dwie osoby." : "Wyłączenie zatwierdzania przez dwie osoby.");
      if (code === null) return;
      await api(`/api/app/orgs/${org.id}/support-access/settings`, { method: "PUT", body: { dual_approval: enabled, mfa_code: code } })
        .catch((e) => alert(e.message));
      reload();
    };
    return card(el("h3", {}, "Zatwierdzanie przez dwie osoby"),
      el("p", { class: "muted" }, "Gdy włączone, każdy dostęp serwisowy (i każda zgoda stała) wymaga zatwierdzenia przez dwie różne osoby z Twojej organizacji. Wyłączenie też wymaga drugiej osoby."),
      el("p", {}, "Status: ", el("strong", {}, settings.dual_approval ? "włączone" : "wyłączone"),
        settings.dual_approval_disable_requested_by ? el("span", { class: "danger-text" }, " · zgłoszono wyłączenie (", settings.dual_approval_disable_requested_by, ") - czeka na drugą osobę") : ""),
      settings.dual_approval
        ? el("button", { class: "secondary", onclick: () => put(false) }, settings.dual_approval_disable_requested_by ? "Potwierdź wyłączenie" : "Wyłącz")
        : el("button", { onclick: () => put(true) }, "Włącz"));
  }

  // ---------------------------------------------------- podglad na zywo / nagranie
  function livePanel(org, s, panel, reload) {
    const frame = snapshotFrame();
    const status = el("p", { class: "muted" }, "Laczenie…");
    const feed = el("table");
    let latest = 0;
    let timer;
    const poll = async () => {
      if (!panel.contains(frame)) return clearInterval(timer);
      try {
        const live = await api(`/api/app/orgs/${org.id}/support-access/sessions/${s.id}/live?after=${latest}`);
        if (live.snapshot) { frame.show(live.snapshot.html); latest = live.snapshot.seq; }
        status.textContent = live.active
          ? `Operator ${live.operator_id} ogląda teraz: ${live.current_view || "—"} · pozostało ${Math.ceil(live.remaining_seconds / 60)} min`
          : "Sesja zakończona.";
        feed.replaceChildren(...live.activity.map((e) => el("tr", {}, el("td", {}, fmt(e.occurred_at)),
          el("td", {}, e.method, " ", e.route), el("td", {}, el("span", { class: "pill" }, e.outcome)))));
        if (!live.active) clearInterval(timer);
      } catch (e) { status.textContent = e.message; }
    };
    panel.replaceChildren(card(
      el("h3", {}, "Podgląd na żywo · sesja ", s.ticket_number),
      status,
      el("div", { class: "row" }, el("button", { class: "danger", onclick: async () => {
        await api(`/api/app/orgs/${org.id}/support-access/sessions/${s.id}/terminate`, { method: "POST" }).catch((e) => alert(e.message));
        clearInterval(timer);
        reload();
      } }, "Przerwij sesję")),
      frame,
      el("h3", { class: "spaced" }, "Ostatnie operacje operatora"), feed));
    poll();
    timer = setInterval(poll, 2000);
  }

  async function replayPanel(org, s, panel) {
    const base = `/api/app/orgs/${org.id}/support-access/sessions/${s.id}/recording`;
    const { frames } = await api(base);
    if (!frames.length) return panel.replaceChildren(card(el("p", { class: "muted" }, "Brak nagrania tej sesji.")));
    const frame = snapshotFrame();
    const caption = el("p", { class: "muted" });
    const slider = el("input", { type: "range", min: 1, max: frames.length, value: 1, class: "slider" });
    const load = async () => {
      const f = frames[Number(slider.value) - 1];
      const data = await api(`${base}/${f.seq}`);
      frame.show(data.html);
      caption.textContent = `Klatka ${slider.value}/${frames.length} · ${fmt(f.captured_at)} · widok: ${f.view}`;
    };
    slider.oninput = load;
    panel.replaceChildren(card(el("h3", {}, "Nagranie sesji · ", s.ticket_number), caption, slider, frame));
    load();
  }

  // ------------------------------------------------------ zgody stale (klient)
  const ROLE_LABELS = { support_l1: "Support L1", support_l2: "Support L2", support_lead: "Kierownik supportu" };

  function standingSection(org, standing, units, reload, dual) {
    const rows = standing.map((st) => el("tr", {},
      el("td", {}, st.scopes.map((x) => SCOPE_LABELS[x] || x).join(", ")),
      el("td", {}, st.max_session_minutes, " min"),
      el("td", {}, st.allowed_platform_roles ? st.allowed_platform_roles.map((r) => ROLE_LABELS[r] || r).join(", ") : "każda"),
      el("td", {}, fmt(st.valid_until)),
      el("td", {}, st.revoked_at ? "cofnięta" : st.pending_confirmation ? "czeka na drugą osobę" : st.active ? "aktywna" : "wygasła"),
      el("td", { class: "row" },
        st.pending_confirmation ? el("button", { onclick: async () => {
          const code = askMfa("Potwierdzenie zgody stałej.");
          if (code === null) return;
          await api(`/api/app/orgs/${org.id}/support-access/standing-consents/${st.id}/confirm`, { method: "POST", body: { mfa_code: code } })
            .catch((e) => alert(e.message));
          reload();
        } }, "Potwierdź") : "",
        st.active || st.pending_confirmation ? el("button", { class: "danger", onclick: async () => {
          await api(`/api/app/orgs/${org.id}/support-access/standing-consents/${st.id}/revoke`, { method: "POST" }).catch((e) => alert(e.message));
          reload();
        } }, "Cofnij") : "")));
    const box = (value, label, checked = false) => el("label", {}, el("input", { type: "checkbox", value, checked }), " ", label);
    const scopeBoxes = Object.entries(SCOPE_LABELS).map(([k, l]) => box(k, l, k === "dashboard" || k === "diagnostics"));
    const roleBoxes = Object.entries(ROLE_LABELS).map(([k, l]) => box(k, l));
    const unitBoxes = units.map((u) => box(u.id, u.name));
    const minutes = el("input", { type: "number", min: 1, max: 15, value: 15 });
    const days = el("input", { type: "number", min: 1, max: 365, value: 90 });
    const note = el("input", { placeholder: "Notatka (opcjonalnie)" });
    const mfa = el("input", { inputmode: "numeric", autocomplete: "one-time-code", placeholder: "Kod MFA" });
    const msg = el("p", { class: "error" });
    return card(
      el("h3", {}, "Zgody stałe"),
      el("p", { class: "muted" }, "Zgoda stała pozwala supportowi Forvium otwierać sesje tylko do odczytu bez każdorazowego pytania - w granicach poniżej. O każdym takim dostępie dostaniesz powiadomienie, a zgodę można cofnąć w każdej chwili (kończy to też trwające sesje).",
        dual ? " Przy zatwierdzaniu przez dwie osoby nowa zgoda stała zacznie działać po potwierdzeniu przez drugą osobę." : ""),
      el("table", {}, el("tr", {}, ...["Zakres", "Sesja do", "Role supportu", "Ważna do", "Status", ""].map((t) => el("th", {}, t))), ...rows),
      el("details", { class: "spaced" }, el("summary", {}, "Dodaj zgodę stała"),
        el("label", {}, "Zakres"), ...scopeBoxes,
        ...(unitBoxes.length ? [el("label", {}, "Ogranicz do jednostek (brak zaznaczenia = wszystkie)"), ...unitBoxes] : []),
        el("label", {}, "Tylko dla ról supportu (brak zaznaczenia = każda)"), ...roleBoxes,
        el("label", {}, "Maksymalny czas sesji (min)"), minutes,
        el("label", {}, "Ważna przez (dni)"), days,
        el("label", {}, "Notatka"), note,
        el("label", {}, "Potwierdź kodem MFA"), mfa, msg,
        el("button", { onclick: async () => {
          try {
            const roles = checkedValues(roleBoxes), unitIds = checkedValues(unitBoxes);
            await api(`/api/app/orgs/${org.id}/support-access/standing-consents`, { method: "POST", body: {
              scopes: checkedValues(scopeBoxes), unit_ids: unitIds.length ? unitIds : null,
              allowed_platform_roles: roles.length ? roles : null, max_session_minutes: Number(minutes.value),
              valid_days: Number(days.value), note: note.value, mfa_code: mfa.value } });
            reload();
          } catch (e) { msg.textContent = e.message; }
        } }, "Udziel zgody stałej")));
  }

  // ---------------------------------------------------------- powiadomienia
  async function viewNotifications(content) {
    const { notifications } = await api("/api/app/notifications");
    content.replaceChildren(card(el("h2", {}, "Powiadomienia")),
      ...(notifications.length ? notifications.map((n) => card(el("h3", {}, n.title),
        el("p", { class: "muted" }, fmt(n.created_at)), el("pre", { class: "body" }, n.body)))
        : [el("div", { class: "card muted" }, "Brak powiadomień.")]));
  }

  if (supportToken) startSupportMode().catch(() => supportEnded());
  else renderHome();
})();
