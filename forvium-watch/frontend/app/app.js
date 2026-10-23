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
    diagnostics: "Bledy i stan konfiguracji",
  };

  function el(tag, attrs = {}, ...children) {
    const node = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (k === "onclick" || k === "onsubmit" || k === "onchange") node[k] = v;
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
    if (!r.ok) throw Object.assign(new Error(data.message || "Blad " + r.status), { status: r.status, code: data.error });
    return data;
  }

  const fmt = (iso) => (iso ? new Date(iso).toLocaleString("pl-PL") : "—");

  // ------------------------------------------------------------- tryb wsparcia
  let bannerTimer;
  function supportEnded() {
    sessionStorage.removeItem(SUPPORT_KEY);
    clearInterval(bannerTimer);
    banner.hidden = false;
    banner.replaceChildren(el("span", { class: "title" }, "Sesja wsparcia Forvium zakonczona"));
    root.replaceChildren(el("div", { class: "card" }, "Dostep serwisowy wygasl lub zostal zakonczony. Mozesz zamknac te karte."));
  }

  async function startSupportMode() {
    const info = await api("/api/app/support/session");
    let remaining = info.remaining_seconds;
    const timeEl = el("span");
    const tick = () => {
      if (remaining <= 0) return supportEnded();
      const m = Math.floor(remaining / 60), s = String(remaining % 60).padStart(2, "0");
      timeEl.textContent = `Pozostaly czas: ${m}:${s}`;
      remaining -= 1;
    };
    banner.hidden = false;
    banner.replaceChildren(
      el("span", { class: "title" }, info.banner),
      el("span", { class: "meta" },
        el("span", {}, "Organizacja: ", info.organization.name),
        el("span", {}, "Operator: ", info.operator_id),
        el("span", {}, "Zgloszenie: ", info.ticket_number),
        timeEl),
      el("button", { onclick: async () => {
        try { await api("/api/app/support/session/end", { method: "POST" }); } catch (_) {}
        supportEnded();
      } }, "Zakoncz dostep"),
    );
    tick();
    bannerTimer = setInterval(tick, 1000);
    // Okresowa rewalidacja (cofniecie zgody po stronie klienta konczy sesje natychmiast w API).
    setInterval(() => api("/api/app/support/session").then((i) => { remaining = i.remaining_seconds; }).catch(() => {}), 30000);
    document.getElementById("who").textContent = "Widok uzytkownika: " + info.reference_user.display_name;
    renderOrg(info.organization, info.permissions);
  }

  // ---------------------------------------------------------------- logowanie
  function renderLogin(error) {
    const form = el("form", { class: "card", onsubmit: async (e) => {
      e.preventDefault();
      const f = new FormData(form);
      try {
        const r = await api("/api/app/auth/login", { method: "POST", body: Object.fromEntries(f) });
        sessionStorage.setItem(USER_KEY, r.token);
        renderHome();
      } catch (err) { renderLogin(err.message); }
    } },
      el("h2", {}, "Logowanie"),
      el("label", {}, "E-mail"), el("input", { name: "email", type: "email", required: true }),
      el("label", {}, "Haslo"), el("input", { name: "password", type: "password", required: true }),
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
    root.replaceChildren(el("div", { class: "card" }, el("h2", {}, "Organizacje"),
      ...me.organizations.map((o) => el("p", {}, el("a", { href: "#", onclick: (e) => { e.preventDefault(); renderOrg(o); } }, o.name)))));
  }

  // --------------------------------------------------------------- organizacja
  function renderOrg(org, supportPermissions) {
    const content = el("div");
    // Kazdy widok renderuje sie do wlasnego, swiezego kontenera - wynik wolniejszego,
    // nieaktualnego widoku trafia do odpietego elementu i niczego nie nadpisuje.
    const show = (fn) => { const pane = el("div"); content.replaceChildren(pane); fn(pane); };
    const views = {
      "Dashboard": (pane) => viewDashboard(org, pane),
      "Jednostki": (pane) => viewList(org, pane, "/units", "units", ["name"]),
      "Technologie": (pane) => viewList(org, pane, "/technologies", "technologies", ["name", "version"]),
      "CVE": (pane) => viewList(org, pane, "/cves", "cves", ["id", "severity", "technology"]),
      "Diagnostyka": (pane) => viewDiagnostics(org, pane),
    };
    if (!supportPermissions) {
      views["Dostep serwisowy"] = (pane) => viewSupportAccess(org, pane);
      views["Powiadomienia"] = (pane) => viewNotifications(pane);
    }
    const nav = el("nav", { class: "card" }, el("strong", {}, org.name, " "),
      ...Object.entries(views).map(([label, fn]) => el("a", { onclick: () => show(fn) }, label)));
    root.replaceChildren(nav, content);
    show(views["Dashboard"]);
  }

  async function guarded(content, fn) {
    try { await fn(); } catch (e) {
      content.replaceChildren(el("div", { class: "card error" },
        e.code === "forbidden_in_support_mode" ? "Ta sekcja nie jest objeta zgoda na dostep serwisowy." : e.message));
    }
  }

  function viewDashboard(org, content) {
    guarded(content, async () => {
      const d = await api(`/api/app/orgs/${org.id}/dashboard`);
      const tiles = [["Jednostki", d.units], ["Technologie", d.technologies]];
      if (d.cves) tiles.push(["CVE", d.cves.total], ["Krytyczne", d.cves.critical], ["Wysokie", d.cves.high]);
      content.replaceChildren(el("div", { class: "card" }, el("h2", {}, "Dashboard"),
        el("div", { class: "grid" }, ...tiles.map(([k, v]) => el("div", { class: "card" }, el("div", { class: "muted" }, k), el("h2", {}, v))))));
    });
  }

  function viewList(org, content, path, key, cols) {
    guarded(content, async () => {
      const d = await api(`/api/app/orgs/${org.id}${path}`);
      content.replaceChildren(el("div", { class: "card" }, el("table", {},
        el("tr", {}, ...cols.map((c) => el("th", {}, c))),
        ...d[key].map((row) => el("tr", {}, ...cols.map((c) => el("td", {}, row[c])))))));
    });
  }

  function viewDiagnostics(org, content) {
    guarded(content, async () => {
      const [cfg, errs] = await Promise.all([api(`/api/app/orgs/${org.id}/config/status`), api(`/api/app/orgs/${org.id}/errors`)]);
      content.replaceChildren(
        el("div", { class: "card" }, el("h3", {}, "Stan konfiguracji"),
          el("p", {}, "SMTP skonfigurowany: ", cfg.smtp_configured ? "tak" : "nie"),
          el("p", {}, "Webhooki: ", cfg.webhooks_count, " · Sekrety: ", cfg.secrets_count, " · Plan: ", cfg.subscription_plan)),
        el("div", { class: "card" }, el("h3", {}, "Bledy"), el("table", {},
          ...errs.errors.map((e) => el("tr", {}, el("td", {}, fmt(e.created_at)), el("td", {}, e.level), el("td", {}, e.component), el("td", {}, e.message))))));
    });
  }

  // ------------------------------------------------- dostep serwisowy (klient)
  function viewSupportAccess(org, content) {
    guarded(content, async () => {
      const h = await api(`/api/app/orgs/${org.id}/support-access`);
      const pending = h.requests.filter((r) => r.status === "pending");
      const reload = () => viewSupportAccess(org, content);
      const { units } = await api(`/api/app/orgs/${org.id}/units`).catch(() => ({ units: [] }));
      const unitName = Object.fromEntries(units.map((u) => [u.id, u.name]));

      const pendingCards = pending.map((r) => {
        const scopes = r.scopes.map((s) => el("label", {}, el("input", { type: "checkbox", value: s, checked: true }), " ", SCOPE_LABELS[s] || s));
        // Pusty wybor = wszystkie jednostki; zaznaczenie obejmuje tez jednostki podrzedne.
        const unitBoxes = units.map((u) => el("label", {}, el("input", { type: "checkbox", value: u.id }), " ", u.name));
        const hours = el("input", { type: "number", min: 1, max: 168, value: 24 });
        const note = el("input", { placeholder: "Notatka (opcjonalnie)" });
        return el("div", { class: "card" },
          el("h3", {}, "Prosba o dostep · ", r.ticket_number),
          el("p", {}, "Operator Forvium: ", r.operator_id),
          el("p", {}, "Powod: ", r.reason),
          el("p", {}, "Tryb: ", el("span", { class: "pill" }, r.access_level), " · Czas sesji: ", r.duration_minutes, " min"),
          el("label", {}, "Zakres zgody"), ...scopes,
          ...(unitBoxes.length ? [el("label", {}, "Ogranicz do jednostek (brak zaznaczenia = wszystkie)"), ...unitBoxes] : []),
          el("label", {}, "Zgoda wazna (godziny)"), hours,
          el("label", {}, "Notatka"), note,
          el("div", { class: "row spaced" },
            el("button", { onclick: async () => {
              const checked = (labels) => labels.map((l) => l.querySelector("input")).filter((i) => i.checked).map((i) => i.value);
              const unitIds = checked(unitBoxes);
              await api(`/api/app/orgs/${org.id}/support-access/requests/${r.id}/approve`, { method: "POST",
                body: { scopes: checked(scopes), unit_ids: unitIds.length ? unitIds : null,
                        valid_hours: Number(hours.value), note: note.value } }).catch((e) => alert(e.message));
              reload();
            } }, "Zatwierdz"),
            el("button", { class: "danger", onclick: async () => {
              await api(`/api/app/orgs/${org.id}/support-access/requests/${r.id}/reject`, { method: "POST", body: { note: note.value } }).catch((e) => alert(e.message));
              reload();
            } }, "Odrzuc")));
      });

      const consentRows = h.requests.filter((r) => r.consent).map((r) => {
        const c = r.consent;
        const active = !c.revoked_at && new Date(c.valid_until) > new Date();
        const scopeText = c.scopes.map((s) => SCOPE_LABELS[s] || s).join(", ") +
          (c.unit_ids ? " · jednostki: " + c.unit_ids.map((id) => unitName[id] || id).join(", ") : "");
        const basis = { customer: "decyzja klienta", standing: "zgoda stala",
          break_glass: el("span", { class: "danger-text" }, "BREAK GLASS") }[c.basis] || c.basis;
        return el("tr", {}, el("td", {}, r.ticket_number), el("td", {}, r.operator_id), el("td", {}, basis), el("td", {}, scopeText),
          el("td", {}, fmt(c.valid_until)), el("td", {}, c.revoked_at ? "cofnieta " + fmt(c.revoked_at) : active ? "aktywna" : "wygasla"),
          el("td", {}, active ? el("button", { class: "danger", onclick: async () => {
            await api(`/api/app/orgs/${org.id}/support-access/consents/${c.id}/revoke`, { method: "POST" }).catch((e) => alert(e.message));
            reload();
          } }, "Cofnij zgode") : ""));
      });

      const activity = el("div");
      const sessionRows = h.sessions.map((s) => el("tr", {},
        el("td", {}, fmt(s.started_at)), el("td", {}, s.operator_id), el("td", {}, s.ticket_number),
        el("td", {}, el("span", { class: "pill" }, s.status)), el("td", {}, fmt(s.ended_at || s.expires_at)),
        el("td", { class: "row" },
          el("button", { class: "secondary", onclick: async () => {
            const a = await api(`/api/app/orgs/${org.id}/support-access/sessions/${s.id}/activity`);
            activity.replaceChildren(el("div", { class: "card" }, el("h3", {}, "Aktywnosc sesji ", s.id), el("table", {},
              ...a.events.map((e) => el("tr", {}, el("td", {}, fmt(e.occurred_at)), el("td", {}, e.action),
                el("td", {}, e.method || ""), el("td", {}, e.route || ""), el("td", {}, e.outcome))))));
          } }, "Aktywnosc"),
          s.status === "active" ? el("button", { class: "danger", onclick: async () => {
            await api(`/api/app/orgs/${org.id}/support-access/sessions/${s.id}/terminate`, { method: "POST" }).catch((e) => alert(e.message));
            reload();
          } }, "Zakoncz") : "")));

      content.replaceChildren(
        el("div", { class: "card" }, el("h2", {}, "Dostep serwisowy Forvium"),
          el("p", { class: "muted" }, "Operator Forvium moze zobaczyc Twoja organizacje wylacznie w trybie tylko do odczytu, w zakresie i czasie, ktore zatwierdzisz. Zgode mozna cofnac w kazdej chwili.")),
        ...(pendingCards.length ? pendingCards : [el("div", { class: "card muted" }, "Brak oczekujacych prosb.")]),
        el("div", { class: "card" }, el("h3", {}, "Zgody"), el("table", {},
          el("tr", {}, ...["Zgloszenie", "Operator", "Podstawa", "Zakres", "Wazna do", "Status", ""].map((t) => el("th", {}, t))), ...consentRows)),
        standingSection(org, h.standing_consents || [], units, reload),
        el("div", { class: "card" }, el("h3", {}, "Historia sesji"), el("table", {},
          el("tr", {}, ...["Start", "Operator", "Zgloszenie", "Status", "Koniec", ""].map((t) => el("th", {}, t))), ...sessionRows)),
        activity);
    });
  }

  // ------------------------------------------------------ zgody stale (klient)
  const ROLE_LABELS = { support_l1: "Support L1", support_l2: "Support L2", support_lead: "Kierownik supportu" };

  function standingSection(org, standing, units, reload) {
    const rows = standing.map((st) => el("tr", {},
      el("td", {}, st.scopes.map((x) => SCOPE_LABELS[x] || x).join(", ")),
      el("td", {}, st.max_session_minutes, " min"),
      el("td", {}, st.allowed_platform_roles ? st.allowed_platform_roles.map((r) => ROLE_LABELS[r] || r).join(", ") : "kazda"),
      el("td", {}, fmt(st.valid_until)),
      el("td", {}, st.revoked_at ? "cofnieta" : st.active ? "aktywna" : "wygasla"),
      el("td", {}, st.active ? el("button", { class: "danger", onclick: async () => {
        await api(`/api/app/orgs/${org.id}/support-access/standing-consents/${st.id}/revoke`, { method: "POST" }).catch((e) => alert(e.message));
        reload();
      } }, "Cofnij") : "")));
    const box = (value, label, checked = false) => el("label", {}, el("input", { type: "checkbox", value, checked }), " ", label);
    const scopeBoxes = Object.entries(SCOPE_LABELS).map(([k, l]) => box(k, l, k === "dashboard" || k === "diagnostics"));
    const roleBoxes = Object.entries(ROLE_LABELS).map(([k, l]) => box(k, l));
    const unitBoxes = units.map((u) => box(u.id, u.name));
    const checked = (labels) => labels.map((l) => l.querySelector("input")).filter((i) => i.checked).map((i) => i.value);
    const minutes = el("input", { type: "number", min: 1, max: 15, value: 15 });
    const days = el("input", { type: "number", min: 1, max: 365, value: 90 });
    const note = el("input", { placeholder: "Notatka (opcjonalnie)" });
    const mfa = el("input", { inputmode: "numeric", autocomplete: "one-time-code", placeholder: "Kod MFA" });
    const msg = el("p", { class: "error" });
    return el("div", { class: "card" },
      el("h3", {}, "Zgody stale"),
      el("p", { class: "muted" }, "Zgoda stala pozwala supportowi Forvium otwierac sesje tylko do odczytu bez kazdorazowego pytania - w granicach ponizej. O kazdym takim dostepie dostaniesz powiadomienie, a zgode mozna cofnac w kazdej chwili (konczy to tez trwajace sesje)."),
      el("table", {}, el("tr", {}, ...["Zakres", "Sesja do", "Role supportu", "Wazna do", "Status", ""].map((t) => el("th", {}, t))), ...rows),
      el("details", { class: "spaced" }, el("summary", {}, "Dodaj zgode stala"),
        el("label", {}, "Zakres"), ...scopeBoxes,
        ...(unitBoxes.length ? [el("label", {}, "Ogranicz do jednostek (brak zaznaczenia = wszystkie)"), ...unitBoxes] : []),
        el("label", {}, "Tylko dla rol supportu (brak zaznaczenia = kazda)"), ...roleBoxes,
        el("label", {}, "Maksymalny czas sesji (min)"), minutes,
        el("label", {}, "Wazna przez (dni)"), days,
        el("label", {}, "Notatka"), note,
        el("label", {}, "Potwierdz kodem MFA"), mfa, msg,
        el("button", { onclick: async () => {
          try {
            const roles = checked(roleBoxes), unitIds = checked(unitBoxes);
            await api(`/api/app/orgs/${org.id}/support-access/standing-consents`, { method: "POST", body: {
              scopes: checked(scopeBoxes), unit_ids: unitIds.length ? unitIds : null,
              allowed_platform_roles: roles.length ? roles : null, max_session_minutes: Number(minutes.value),
              valid_days: Number(days.value), note: note.value, mfa_code: mfa.value } });
            reload();
          } catch (e) { msg.textContent = e.message; }
        } }, "Udziel zgody stalej")));
  }

  // ---------------------------------------------------------- powiadomienia
  async function viewNotifications(content) {
    const { notifications } = await api("/api/app/notifications");
    content.replaceChildren(el("div", { class: "card" }, el("h2", {}, "Powiadomienia")),
      ...(notifications.length ? notifications.map((n) => el("div", { class: "card" }, el("h3", {}, n.title),
        el("p", { class: "muted" }, fmt(n.created_at)), el("pre", { class: "body" }, n.body)))
        : [el("div", { class: "card muted" }, "Brak powiadomien.")]));
  }

  if (supportToken) startSupportMode().catch(() => supportEnded());
  else renderHome();
})();
