// admin.forvium.com - panel operatorow Forvium.
// Zakladki zaleza od uprawnien roli: Uzytkownicy / Moje prosby (support), Nadzor sesji i Audyt
// (kierownik supportu, bezpieczenstwo), Break Glass (oficer bezpieczenstwa), Powiadomienia.
(() => {
  const API = window.FORVIUM_API;
  const KEY = "fw_operator_token";
  const root = document.getElementById("root");
  const SCOPE_LABELS = {
    dashboard: "Dashboard organizacji",
    units: "Struktura jednostek",
    technologies_cve: "Technologie i CVE",
    diagnostics: "Błędy i stan konfiguracji",
  };
  const CATEGORY_LABELS = {
    security_incident: "Incydent bezpieczeństwa",
    critical_outage: "Krytyczna awaria",
    data_integrity: "Integralność danych",
  };
  const P = {
    request: "platform.support_access.request",
    oversight: "platform.support_access.oversight",
    audit: "platform.audit.read",
    bgRequest: "platform.break_glass.request",
    bgApprove: "platform.break_glass.approve",
    bgReview: "platform.break_glass.review",
    usersRead: "platform.users.read",
    usersManage: "platform.users.manage",
    orgsManage: "platform.orgs.manage",
    ticketsRead: "platform.tickets.read",
    ticketsManage: "platform.tickets.manage",
    operatorsManage: "platform.operators.manage",
    operatorsApprove: "platform.operators.approve",
  };
  const STATE_LABELS = { active: "aktywne", pending_activation: "czeka na aktywację", blocked: "zablokowane", inactive: "nieaktywne" };
  const TICKET_LABELS = { open: "otwarte", in_progress: "w toku", closed: "zamknięte" };
  const PRIORITY_LABELS = { low: "niski", normal: "normalny", high: "wysoki", critical: "krytyczny" };
  let me = null;

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
    const t = sessionStorage.getItem(KEY);
    if (t) headers.Authorization = "Bearer " + t;
    const r = await fetch(API + path, { ...opts, headers, body: opts.body ? JSON.stringify(opts.body) : undefined });
    if (opts.raw) {
      if (!r.ok) throw new Error("Błąd " + r.status);
      return r;
    }
    const data = await r.json().catch(() => ({}));
    if (!r.ok) throw Object.assign(new Error(data.message || "Błąd " + r.status), { status: r.status, code: data.error });
    return data;
  }
  const fmt = (iso) => (iso ? new Date(iso).toLocaleString("pl-PL") : "—");
  const can = (perm) => me && me.permissions.includes(perm);
  const table = (headers, rows) => el("table", {}, el("tr", {}, ...headers.map((h) => el("th", {}, h))), ...rows);
  const card = (...children) => el("div", { class: "card" }, ...children);
  const errorCard = (e) => card(el("p", { class: "error" }, e.message));

  // ---------------------------------------------------------------- WebAuthn
  let myKeys = [];
  const b64uToBuf = (s) => Uint8Array.from(atob(s.replace(/-/g, "+").replace(/_/g, "/") + "===".slice((s.length + 3) % 4)), (c) => c.charCodeAt(0)).buffer;
  const bufToB64u = (b) => btoa(String.fromCharCode(...new Uint8Array(b))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");

  async function createKey(options) {
    const pk = { ...options, challenge: b64uToBuf(options.challenge),
      user: { ...options.user, id: b64uToBuf(options.user.id) },
      excludeCredentials: (options.excludeCredentials || []).map((c) => ({ ...c, id: b64uToBuf(c.id) })) };
    const cred = await navigator.credentials.create({ publicKey: pk });
    return { id: cred.id, rawId: bufToB64u(cred.rawId), type: cred.type, clientExtensionResults: {},
      response: { clientDataJSON: bufToB64u(cred.response.clientDataJSON),
        attestationObject: bufToB64u(cred.response.attestationObject),
        transports: cred.response.getTransports ? cred.response.getTransports() : [] } };
  }

  async function getAssertion(options) {
    const pk = { ...options, challenge: b64uToBuf(options.challenge),
      allowCredentials: (options.allowCredentials || []).map((c) => ({ ...c, id: b64uToBuf(c.id) })) };
    const cred = await navigator.credentials.get({ publicKey: pk });
    return { id: cred.id, rawId: bufToB64u(cred.rawId), type: cred.type, clientExtensionResults: {},
      response: { clientDataJSON: bufToB64u(cred.response.clientDataJSON),
        authenticatorData: bufToB64u(cred.response.authenticatorData),
        signature: bufToB64u(cred.response.signature),
        userHandle: cred.response.userHandle ? bufToB64u(cred.response.userHandle) : null } };
  }

  // Ponowna weryfikacja: klucz bezpieczenstwa (jesli zarejestrowany) albo kod TOTP.
  // Zwraca fragment body zadania albo null, gdy uzytkownik zrezygnowal.
  async function stepUp(what, { requireKey = false } = {}) {
    if (myKeys.length) {
      const { options } = await api("/api/admin/webauthn/assertion/options", { method: "POST" });
      return { webauthn: await getAssertion(options) };
    }
    if (requireKey) throw new Error("Ta operacja wymaga klucza bezpieczeństwa (WebAuthn). Dodaj klucz w zakładce Konto.");
    const code = prompt(`${what}\nPonowna weryfikacja MFA - podaj kod z aplikacji uwierzytelniającej:`);
    return code ? { mfa_code: code } : null;
  }

  // Podglad/nagranie widoku operatora: iframe w piaskownicy bez skryptow.
  function snapshotFrame() {
    const frame = el("iframe", { class: "snapshot", sandbox: "", title: "Zrzut widoku sesji", referrerpolicy: "no-referrer" });
    frame.show = (html) => {
      frame.srcdoc = `<!doctype html><html><head><link rel="stylesheet" href="${location.origin}/styles.css"></head>` +
        `<body class="snapshot-body"><main>${html}</main></body></html>`;
    };
    return frame;
  }

  // ---------------------------------------------------------------- logowanie
  // Drugi skladnik: kod TOTP albo klucz bezpieczenstwa (haslo jest sprawdzane przed wydaniem wyzwania).
  function renderLogin(error) {
    const finish = async (body) => {
      try {
        const r = await api("/api/admin/auth/login", { method: "POST", body });
        sessionStorage.setItem(KEY, r.token);
        start();
      } catch (err) { renderLogin(err.message); }
    };
    const credentials = () => {
      if (!form.reportValidity()) return null;
      const { email, password } = Object.fromEntries(new FormData(form));
      return { email, password };
    };
    const form = el("form", { class: "card", onsubmit: (e) => {
      e.preventDefault();
      const base = credentials();
      if (!base) return;
      const code = form.elements.mfa_code.value.trim();
      if (!code) { renderLogin("Podaj kod MFA albo użyj klucza bezpieczeństwa."); return; }
      finish({ ...base, mfa_code: code });
    } },
      el("h2", {}, "Logowanie operatora"),
      el("label", {}, "E-mail"), el("input", { name: "email", type: "email", required: true, autocomplete: "username" }),
      el("label", {}, "Hasło"), el("input", { name: "password", type: "password", required: true, autocomplete: "current-password" }),
      el("label", {}, "Kod MFA"), el("input", { name: "mfa_code", inputmode: "numeric", autocomplete: "one-time-code" }),
      el("p", { class: "error" }, error || ""),
      el("div", { class: "row" },
        el("button", { type: "submit" }, "Zaloguj kodem MFA"),
        el("button", { type: "button", class: "secondary", onclick: async () => {
          const base = credentials();
          if (!base) return;
          try {
            const { options } = await api("/api/admin/auth/login/webauthn/options", { method: "POST", body: base });
            finish({ ...base, webauthn: await getAssertion(options) });
          } catch (err) { renderLogin(err.message); }
        } }, "Zaloguj kluczem bezpieczeństwa")));
    root.replaceChildren(form);
  }

  // -------------------------------------------------------------- nawigacja
  const content = el("div");
  // Kazdy widok bierze "bilet"; wynik wolniejszego, nieaktualnego widoku nie nadpisze nowszego.
  let viewSeq = 0;
  const begin = () => {
    const seq = ++viewSeq;
    return (...nodes) => { if (seq === viewSeq) content.replaceChildren(...nodes); };
  };
  function tabs() {
    const items = [];
    if (can(P.usersRead)) items.push(["Użytkownicy", () => renderUsers()]);
    if (can(P.request)) items.push(["Moje prośby", () => renderMyRequestsPage()]);
    if (can(P.usersRead)) items.push(["Organizacje", () => renderOrganizations()]);
    if (can(P.ticketsRead)) items.push(["Zgłoszenia", () => renderTickets()]);
    if (can(P.operatorsManage) || can(P.operatorsApprove)) items.push(["Operatorzy", () => renderOperators()]);
    if (can(P.oversight)) items.push(["Nadzór sesji", () => renderOversight()], ["Alerty", () => renderAlerts()]);
    if (can(P.audit)) items.push(["Audyt", () => renderAudit()], ["Raporty", () => renderReports()]);
    if (can(P.bgApprove) || can(P.bgReview)) items.push(["Break Glass", () => renderBreakGlass()]);
    items.push(["Powiadomienia", () => renderNotifications()], ["Konto", () => renderAccount()]);
    const nav = el("nav", { class: "card tabs" });
    for (const [label, fn] of items) {
      nav.append(el("a", { onclick: () => {
        nav.querySelectorAll("a").forEach((a) => a.classList.remove("active"));
        link.classList.add("active");
        fn();
      } }, label));
      const link = nav.lastChild;
    }
    nav.append(el("a", { onclick: async () => {
      await api("/api/admin/auth/logout", { method: "POST" }).catch(() => {});
      sessionStorage.removeItem(KEY);
      location.reload();
    } }, "Wyloguj"));
    return { nav, first: items[0][1] };
  }

  async function start() {
    try { me = await api("/api/admin/me"); } catch (_) { return renderLogin(); }
    document.getElementById("who").textContent = `${me.user.display_name} (${me.platform_role}) · ID ${me.user.id}`;
    myKeys = (await api("/api/admin/webauthn/credentials")).credentials;
    if (me.password_change_required) return root.replaceChildren(passwordCard(true));
    const { nav, first } = tabs();
    root.replaceChildren(nav, content);
    nav.querySelector("a").classList.add("active");
    first();
  }

  // ---------------------------------------------------------------- uzytkownicy
  async function renderUsers(q = "") {
    const show = begin();
    const { users } = await api("/api/admin/users?q=" + encodeURIComponent(q));
    const search = el("input", { placeholder: "Szukaj po e-mailu lub nazwie", value: q });
    search.onchange = () => renderUsers(search.value);
    show(
      card(el("h2", {}, "Użytkownicy"), search),
      card(table(["E-mail", "Nazwa", "Konto", ""], users.map((u) => el("tr", {}, el("td", {}, u.email), el("td", {}, u.display_name),
        el("td", {}, el("span", { class: "pill" + (u.state === "blocked" ? " sev-high" : "") }, STATE_LABELS[u.state] || u.state)),
        el("td", {}, el("button", { class: "secondary", onclick: () => renderUserDetail(u.id) }, "Szczegóły")))))));
  }

  async function renderUserDetail(userId) {
    const show = begin();
    const [detail, policy] = await Promise.all([api("/api/admin/users/" + userId), api("/api/admin/support-access/policy")]);
    const u = detail.user;
    const orgSel = el("select", { name: "organization_id", required: true },
      ...detail.organizations.map((o) => el("option", { value: o.id }, `${o.name} (${o.role})`)));
    const ticketSel = el("select", { name: "ticket_number", required: true });
    const loadTickets = async () => {
      const { tickets } = await api("/api/admin/tickets?organization_id=" + encodeURIComponent(orgSel.value));
      ticketSel.replaceChildren(...tickets.filter((t) => t.status !== "closed").map((t) => el("option", { value: t.number }, `${t.number} – ${t.subject}`)));
    };
    orgSel.onchange = loadTickets;
    const scopeBoxes = policy.operator_allowed_scopes.map((s) => el("label", {},
      el("input", { type: "checkbox", value: s, checked: true }), " ", SCOPE_LABELS[s] || s));
    const msg = el("p");

    // Tryb awaryjny widoczny tylko, gdy polityka go wlacza i rola ma uprawnienie.
    const bgAvailable = policy.break_glass_enabled && can(P.bgRequest);
    const modeSel = el("select", { name: "mode" }, el("option", { value: "standard" }, "Standardowy (zgoda klienta)"),
      ...(bgAvailable ? [el("option", { value: "break_glass" }, "AWARYJNY – Break Glass (bez zgody klienta)")] : []));
    const reason = el("textarea", { name: "reason", required: true, minlength: 15, rows: 3 });
    const counter = el("span", { class: "muted" });
    const duration = el("input", { name: "duration_minutes", type: "number", min: 1, max: policy.max_session_minutes, value: policy.default_session_minutes });
    const bgFields = el("div", { hidden: true },
      el("p", { class: "danger-text" }, "Procedura awaryjna: wymaga zatwierdzenia przez oficera bezpieczeństwa, klient i zespół bezpieczeństwa zostaną powiadomieni, a sesja podlega obowiązkowemu przeglądowi."),
      el("label", {}, "Kategoria incydentu"),
      el("select", { name: "incident_category" }, ...(policy.incident_categories || []).map((c) => el("option", { value: c }, CATEGORY_LABELS[c] || c))));
    const updateMode = () => {
      const bg = modeSel.value === "break_glass";
      bgFields.hidden = !bg;
      const min = bg ? policy.break_glass_min_justification : 15;
      reason.setAttribute("minlength", min);
      duration.max = bg ? policy.break_glass_max_session_minutes : policy.max_session_minutes;
      counter.textContent = `${reason.value.length} / min. ${min} znaków`;
    };
    modeSel.onchange = updateMode;
    reason.oninput = updateMode;
    updateMode();

    const form = el("form", { class: "card", onsubmit: async (e) => {
      e.preventDefault();
      const f = Object.fromEntries(new FormData(form));
      try {
        const proof = await stepUp("Wysłanie prośby o dostęp.", { requireKey: f.mode === "break_glass" && policy.break_glass_requires_webauthn });
        if (!proof) return;
        const r = await api("/api/admin/support-access/requests", { method: "POST", body: {
          ...proof,
          organization_id: f.organization_id, reference_user_id: u.id, reason: f.reason, ticket_number: f.ticket_number,
          duration_minutes: Number(f.duration_minutes), mode: f.mode, incident_category: f.incident_category || null,
          scopes: scopeBoxes.map((l) => l.querySelector("input")).filter((i) => i.checked).map((i) => i.value),
        } });
        msg.className = "";
        msg.textContent = {
          approved: "Prośba zatwierdzona automatycznie (zgoda stała klienta). Możesz uruchomić sesję w zakładce Moje prośby.",
          pending_second_approval: "Wniosek awaryjny wysłany do oficerów bezpieczeństwa.",
        }[r.request.status] || "Prośba wysłana. Klient otrzymał powiadomienie w aplikacji i e-mail.";
        form.reset();
        updateMode();
      } catch (err) { msg.className = "error"; msg.textContent = err.message; }
    } },
      el("h3", {}, "Dostęp serwisowy"),
      el("p", { class: "muted" }, "Sesja w trybie READ_ONLY, wymaga zgody klienta. Maksymalny czas: ", policy.max_session_minutes, " min."),
      el("label", {}, "Tryb"), modeSel, bgFields,
      el("label", {}, "Organizacja"), orgSel,
      el("label", {}, "Użytkownik referencyjny"), el("input", { value: `${u.display_name} <${u.email}>`, disabled: true }),
      el("label", {}, "Powód dostępu / uzasadnienie"), reason, counter,
      el("label", {}, "Numer zgłoszenia"), ticketSel,
      el("label", {}, "Czas dostępu (min)"), duration,
      el("label", {}, "Zakres"), ...scopeBoxes,
      el("p", { class: "muted" }, myKeys.length ? "Wysłanie potwierdzisz kluczem bezpieczeństwa." : "Wysłanie potwierdzisz kodem MFA."),
      msg,
      el("button", { type: "submit" }, "Wyślij prośbę o dostęp"));

    show(
      card(el("a", { onclick: () => renderUsers() }, "← Użytkownicy"),
        el("h2", {}, u.display_name), el("p", { class: "muted" }, u.email, " · ID ", u.id),
        el("p", {}, "Konto: ", el("strong", {}, STATE_LABELS[u.state] || u.state), u.blocked_reason ? ` (powód: ${u.blocked_reason})` : "")),
      accountCard(u, () => renderUserDetail(userId)),
      !can(P.request) ? "" : u.state !== "active" ? el("div", { class: "card muted" }, "Konto nie jest aktywne - dostęp serwisowy niedostępny.")
        : detail.organizations.length ? form : el("div", { class: "card muted" }, "Użytkownik nie należy do żadnej organizacji."));
    if (detail.organizations.length && can(P.request) && u.state === "active") await loadTickets();
  }

  // Wspolne wywolanie operacji wymagajacej ponownej weryfikacji (klucz albo kod MFA).
  async function guarded(what, path, method, body, done) {
    try {
      const proof = await stepUp(what);
      if (!proof) return null;
      const r = await api(path, { method, body: { ...body, ...proof } });
      if (done) done(r);
      return r;
    } catch (e) { alert(e.message); return null; }
  }

  // Blokada / odblokowanie / ponowna aktywacja konta klienta (platform.users.manage).
  function accountCard(u, reload) {
    if (!can(P.usersManage)) return "";
    const actions = el("div", { class: "row" });
    if (u.state === "blocked") {
      actions.append(el("button", { class: "secondary", onclick: () => guarded("Odblokowanie konta " + u.email,
        `/api/admin/users/${u.id}/unblock`, "POST", {}, reload) }, "Odblokuj konto"));
    } else {
      actions.append(el("button", { class: "danger", onclick: () => {
        const reason = prompt("Powód blokady (zobaczą go administratorzy organizacji klienta):");
        if (reason) guarded("Blokada konta " + u.email, `/api/admin/users/${u.id}/block`, "POST", { reason }, reload);
      } }, "Zablokuj konto"));
    }
    if (u.state === "active") {
      actions.append(el("button", { class: "secondary", onclick: () => {
        const reason = prompt("Powód resetu dostępu (np. zgubiony telefon jedynego właściciela). Nowy link trafi na e-mail tej osoby:");
        if (reason) guarded("Reset dostępu " + u.email, `/api/admin/users/${u.id}/reset-access`, "POST", { reason }, reload);
      } }, "Resetuj dostęp"));
    }
    if (u.state === "pending_activation") {
      actions.append(el("button", { class: "secondary", onclick: () => guarded("Nowy link aktywacyjny dla " + u.email,
        `/api/admin/users/${u.id}/resend-activation`, "POST", {}, () => alert("Wysłano nowy link na adres " + u.email)) }, "Wyślij ponownie link aktywacyjny"));
    }
    return card(el("h3", {}, "Konto"),
      el("p", { class: "muted" }, "Blokada wylogowuje użytkownika i kończy sesje wsparcia, w których jest użytkownikiem referencyjnym. Forvium nie zmienia haseł ani MFA klientów."),
      actions);
  }

  // ---------------------------------------------------------------- organizacje
  async function renderOrganizations(q = "") {
    const show = begin();
    try {
      const { organizations, plans } = await api("/api/admin/organizations?q=" + encodeURIComponent(q));
      const search = el("input", { placeholder: "Szukaj po nazwie", value: q });
      search.onchange = () => renderOrganizations(search.value);
      const rows = organizations.map((o) => el("tr", {}, el("td", {}, o.name), el("td", {}, o.subscription_plan),
        el("td", {}, String(o.members)), el("td", {}, String(o.open_tickets)), el("td", {}, o.dual_approval ? "tak" : "nie"),
        el("td", {}, el("button", { class: "secondary", onclick: () => renderOrganizationDetail(o.id) }, "Szczegóły"))));
      let createCard = "";
      if (can(P.orgsManage)) {
        const form = el("form", { onsubmit: async (e) => {
          e.preventDefault();
          const f = Object.fromEntries(new FormData(form));
          const r = await guarded(`Utworzenie organizacji ${f.name}`, "/api/admin/organizations", "POST", f);
          if (r) {
            alert(r.owner.state === "pending_activation"
              ? `Utworzono organizację. Link aktywacyjny wysłano na ${r.owner.email} (ważny 72 h).`
              : `Utworzono organizację. ${r.owner.email} został właścicielem.`);
            renderOrganizationDetail(r.organization.id);
          }
        } },
          el("label", {}, "Nazwa"), el("input", { name: "name", required: true, minlength: 2, maxlength: 200 }),
          el("label", {}, "Plan"), el("select", { name: "subscription_plan" }, ...plans.map((p) => el("option", { value: p }, p))),
          el("label", {}, "E-mail właściciela"), el("input", { name: "owner_email", type: "email", required: true }),
          el("label", {}, "Imię i nazwisko właściciela"), el("input", { name: "owner_name", required: true, minlength: 2 }),
          el("p", { class: "muted" }, "Właściciel sam ustawi hasło i MFA (link w e-mailu). Forvium nie poznaje jego hasła."),
          el("button", { type: "submit" }, "Utwórz organizację"));
        createCard = card(el("h3", {}, "Nowa organizacja"), form);
      }
      show(card(el("h2", {}, "Organizacje"), search),
        card(table(["Nazwa", "Plan", "Członkowie", "Otwarte zgłoszenia", "2 osoby", ""], rows)), createCard);
    } catch (e) { show(errorCard(e)); }
  }

  async function renderOrganizationDetail(orgId) {
    const show = begin();
    try {
      const d = await api("/api/admin/organizations/" + orgId);
      const o = d.organization;
      let editCard = "";
      if (can(P.orgsManage)) {
        const { plans } = await api("/api/admin/organizations?q=");
        const form = el("form", { onsubmit: (e) => {
          e.preventDefault();
          const f = Object.fromEntries(new FormData(form));
          guarded(`Zmiana danych organizacji ${o.name}`, "/api/admin/organizations/" + o.id, "PUT", f, () => renderOrganizationDetail(o.id));
        } },
          el("label", {}, "Nazwa"), el("input", { name: "name", value: o.name, required: true, minlength: 2 }),
          el("label", {}, "Plan"), el("select", { name: "subscription_plan" }, ...plans.map((p) => el("option", { value: p, selected: p === o.subscription_plan }, p))),
          el("p", { class: "muted" }, "Administratorzy organizacji dostaną powiadomienie o zmianie."),
          el("button", { type: "submit" }, "Zapisz"));
        editCard = card(el("h3", {}, "Dane organizacji"), form);
      }
      show(
        card(el("a", { onclick: () => renderOrganizations() }, "← Organizacje"), el("h2", {}, o.name),
          el("p", { class: "muted" }, "Plan: ", o.subscription_plan, " · utworzona ", fmt(o.created_at), " · zatwierdzanie przez dwie osoby: ", o.dual_approval ? "tak" : "nie")),
        card(el("h3", {}, "Członkowie"), el("p", { class: "muted" }, "Członkami zarządza klient (zaproszenia w app). Forvium może zablokować konto."),
          table(["E-mail", "Nazwa", "Rola", "Konto", ""], d.members.map((m) => el("tr", {}, el("td", {}, m.email), el("td", {}, m.display_name),
            el("td", {}, m.role), el("td", {}, STATE_LABELS[m.state] || m.state),
            el("td", {}, el("button", { class: "secondary", onclick: () => renderUserDetail(m.user_id) }, "Konto")))))),
        card(el("h3", {}, "Jednostki"), el("ul", {}, ...d.units.map((u) => el("li", {}, u.name)))),
        card(el("h3", {}, "Zgłoszenia"), table(["Numer", "Temat", "Status", "Utworzono"], d.tickets.map((t) => el("tr", {},
          el("td", {}, t.number), el("td", {}, t.subject), el("td", {}, TICKET_LABELS[t.status] || t.status), el("td", {}, fmt(t.created_at))))),
          can(P.ticketsManage) ? el("button", { class: "secondary", onclick: () => renderTickets(o.id) }, "Nowe zgłoszenie") : ""),
        editCard);
    } catch (e) { show(errorCard(e)); }
  }

  // ----------------------------------------------------------------- zgloszenia
  async function renderTickets(newForOrg = null, status = "") {
    const show = begin();
    try {
      const { tickets } = await api("/api/admin/tickets/all?status=" + encodeURIComponent(status));
      const sel = el("select", {}, ...[["", "Wszystkie"], ["open", "Otwarte"], ["in_progress", "W toku"], ["closed", "Zamknięte"]]
        .map(([v, l]) => el("option", { value: v, selected: v === status }, l)));
      sel.onchange = () => renderTickets(null, sel.value);
      const setStatus = (t, st) => async () => {
        if (st === "closed" && !confirm(`Zamknąć ${t.number}? Aktywne sesje wsparcia na tym zgłoszeniu zostaną zakończone.`)) return;
        try {
          const r = await api(`/api/admin/tickets/${t.id}/status`, { method: "PUT", body: { status: st } });
          if (r.support_sessions_ended) alert(`Zakończono sesje wsparcia: ${r.support_sessions_ended}.`);
          renderTickets(null, status);
        } catch (e) { alert(e.message); }
      };
      const rows = tickets.map((t) => el("tr", {}, el("td", {}, t.number), el("td", {}, t.organization_name || t.organization_id),
        el("td", {}, t.subject, t.created_by_customer ? el("div", { class: "muted" }, "od klienta: ", t.reporter_email || "") : ""),
        el("td", { class: t.priority === "critical" || t.priority === "high" ? "sev-high" : "" }, PRIORITY_LABELS[t.priority] || t.priority),
        el("td", {}, el("span", { class: "pill" }, TICKET_LABELS[t.status] || t.status)), el("td", {}, fmt(t.updated_at)),
        el("td", { class: "row" }, el("button", { class: "secondary", onclick: () => renderTicketDetail(t.id) }, "Otwórz"),
          ...(!can(P.ticketsManage) ? [] : t.status === "closed"
          ? [el("button", { class: "secondary", onclick: setStatus(t, "open") }, "Otwórz ponownie")]
          : [t.status === "open" ? el("button", { class: "secondary", onclick: setStatus(t, "in_progress") }, "W toku") : "",
             el("button", { class: "danger", onclick: setStatus(t, "closed") }, "Zamknij")]))));
      let createCard = "";
      if (can(P.ticketsManage)) {
        const { organizations } = await api("/api/admin/organizations?q=");
        const form = el("form", { onsubmit: async (e) => {
          e.preventDefault();
          const f = Object.fromEntries(new FormData(form));
          const r = await guarded("Nowe zgłoszenie", "/api/admin/tickets", "POST", f);
          if (r) { alert(`Utworzono zgłoszenie ${r.ticket.number}.`); renderTickets(); }
        } },
          el("label", {}, "Organizacja"), el("select", { name: "organization_id", required: true },
            ...organizations.map((o) => el("option", { value: o.id, selected: o.id === newForOrg }, o.name))),
          el("label", {}, "Temat"), el("input", { name: "subject", required: true, minlength: 3, maxlength: 300 }),
          el("p", { class: "muted" }, "Dostęp serwisowy zawsze wymaga otwartego zgłoszenia danej organizacji. Zamknięcie zgłoszenia kończy powiązane sesje."),
          el("button", { type: "submit" }, "Utwórz zgłoszenie"));
        createCard = card(el("h3", {}, "Nowe zgłoszenie"), form);
      }
      show(card(el("h2", {}, "Zgłoszenia"), el("label", {}, "Status"), sel),
        card(table(["Numer", "Organizacja", "Temat", "Priorytet", "Status", "Aktualizacja", ""], rows)), createCard);
    } catch (e) { show(errorCard(e)); }
  }

  async function renderTicketDetail(ticketId) {
    const show = begin();
    try {
      const d = await api("/api/admin/tickets/" + ticketId);
      const t = d.ticket;
      const reload = () => renderTicketDetail(ticketId);
      const internal = el("input", { type: "checkbox", name: "internal" });
      const reply = el("form", { onsubmit: async (e) => {
        e.preventDefault();
        try {
          await api(`/api/admin/tickets/${t.id}/messages`, { method: "POST", body: { body: reply.elements.body.value, internal: internal.checked } });
          reload();
        } catch (err) { alert(err.message); }
      } }, el("label", {}, "Wiadomość"), el("textarea", { name: "body", required: true, rows: 4 }),
        el("label", {}, internal, " notatka wewnętrzna (klient jej nie zobaczy)"),
        el("button", { type: "submit" }, "Wyślij"));
      const setStatus = async (st) => {
        if (st === "closed" && !confirm(`Zamknąć ${t.number}? Aktywne sesje wsparcia na tym zgłoszeniu zostaną zakończone.`)) return;
        try {
          const r = await api(`/api/admin/tickets/${t.id}/status`, { method: "PUT", body: { status: st } });
          if (r.support_sessions_ended) alert(`Zakończono sesje wsparcia: ${r.support_sessions_ended}.`);
          reload();
        } catch (err) { alert(err.message); }
      };
      show(
        card(el("a", { onclick: () => renderTickets() }, "← Zgłoszenia"), el("h2", {}, t.number, " · ", t.subject),
          el("p", { class: "muted" }, t.organization_name, " · priorytet: ", PRIORITY_LABELS[t.priority] || t.priority,
            " · status: ", TICKET_LABELS[t.status] || t.status, " · zgłosił(a): ", t.reporter_email || "Forvium", " · ", fmt(t.created_at)),
          t.description ? el("p", { class: "pre" }, t.description) : "",
          can(P.ticketsManage) ? el("div", { class: "row" }, ...Object.entries(TICKET_LABELS).filter(([v]) => v !== t.status)
            .map(([v, l]) => el("button", { class: v === "closed" ? "danger" : "secondary", onclick: () => setStatus(v) }, "Status: " + l))) : ""),
        card(el("h3", {}, "Rozmowa z klientem"), d.messages.length ? el("div", {}, ...d.messages.map((m) => el("div", { class: "msg " + m.author_side + (m.internal ? " internal" : "") },
          el("div", { class: "muted" }, m.author_email || "—", m.internal ? " · NOTATKA WEWNĘTRZNA" : "", " · ", fmt(m.created_at)),
          el("p", { class: "pre" }, m.body)))) : el("p", { class: "muted" }, "Brak wiadomości."), reply),
        card(el("h3", {}, "Prośby o dostęp w tym zgłoszeniu"), d.access_requests.length ? table(["Data", "Operator", "Tryb", "Status"],
          d.access_requests.map((a) => el("tr", {}, el("td", {}, fmt(a.created_at)), el("td", {}, a.operator_email || "—"),
            el("td", {}, a.mode), el("td", {}, a.status)))) : el("p", { class: "muted" }, "Brak.")));
    } catch (e) { show(errorCard(e)); }
  }

  // ------------------------------------------------------------------ operatorzy
  async function renderOperators() {
    const show = begin();
    try {
      const { operators, roles, privileged_roles: privileged } = await api("/api/admin/operators");
      const reload = () => renderOperators();
      const roleSelect = (current) => el("select", {}, ...Object.entries(roles).map(([v, l]) =>
        el("option", { value: v, selected: v === current }, l + (privileged.includes(v) ? " (wymaga zatwierdzenia)" : ""))));
      const rows = operators.map((o) => {
        const actions = el("td", { class: "row" });
        const self = o.id === me.user.id;
        if (can(P.operatorsManage) && !self) {
          const sel = roleSelect(o.role);
          actions.append(sel, el("button", { class: "secondary", onclick: () => guarded(`Zmiana roli ${o.email}`,
            `/api/admin/operators/${o.id}/role`, "PUT", { role: sel.value },
            (r) => { if (r.status === "pending_approval") alert("Rola uprzywilejowana czeka na zatwierdzenie przez oficera bezpieczeństwa."); reload(); }) }, "Zmień rolę"));
          actions.append(o.state === "blocked"
            ? el("button", { class: "secondary", onclick: () => guarded(`Odblokowanie ${o.email}`, `/api/admin/operators/${o.id}/unblock`, "POST", {}, reload) }, "Odblokuj")
            : el("button", { class: "danger", onclick: () => {
              const reason = prompt("Powód blokady operatora:");
              if (reason) guarded(`Blokada ${o.email}`, `/api/admin/operators/${o.id}/block`, "POST", { reason }, reload);
            } }, "Zablokuj"));
          if (o.state === "pending_activation") {
            actions.append(el("button", { class: "secondary", onclick: () => guarded(`Nowy link aktywacyjny dla ${o.email}`,
              `/api/admin/users/${o.id}/resend-activation`, "POST", {}, () => alert("Wysłano nowy link.")) }, "Wyślij link ponownie"));
          }
        }
        if (o.pending_role && can(P.operatorsApprove) && !self && o.pending_role_requested_by !== me.user.id) {
          actions.append(
            el("button", { onclick: () => guarded(`Zatwierdzenie roli ${roles[o.pending_role]} dla ${o.email}`, `/api/admin/operators/${o.id}/role/approve`, "POST", {}, reload) }, "Zatwierdź rolę"),
            el("button", { class: "danger", onclick: () => {
              const reason = prompt("Powód odrzucenia (opcjonalnie):");
              if (reason !== null) guarded(`Odrzucenie roli dla ${o.email}`, `/api/admin/operators/${o.id}/role/reject`, "POST", { reason }, reload);
            } }, "Odrzuć"));
        }
        return el("tr", {}, el("td", {}, o.email, self ? " (Ty)" : ""), el("td", {}, o.display_name), el("td", {}, o.role_label),
          el("td", {}, o.pending_role ? el("span", { class: "danger-text" }, "→ ", roles[o.pending_role], " (czeka)") : "—"),
          el("td", {}, el("span", { class: "pill" + (o.state === "blocked" ? " sev-high" : "") }, STATE_LABELS[o.state] || o.state)),
          el("td", {}, o.has_security_key ? "tak" : "nie"), actions);
      });
      let createCard = "";
      if (can(P.operatorsManage)) {
        const form = el("form", { onsubmit: async (e) => {
          e.preventDefault();
          const f = Object.fromEntries(new FormData(form));
          const r = await guarded(`Nowy operator ${f.email}`, "/api/admin/operators", "POST", f);
          if (r) { alert(`Link aktywacyjny wysłano na ${r.operator.email}.`); reload(); }
        } },
          el("label", {}, "E-mail"), el("input", { name: "email", type: "email", required: true }),
          el("label", {}, "Imię i nazwisko"), el("input", { name: "display_name", required: true, minlength: 2 }),
          el("label", {}, "Rola"), el("select", { name: "role" }, ...Object.entries(roles).filter(([v]) => !privileged.includes(v)).map(([v, l]) => el("option", { value: v }, l))),
          el("p", { class: "muted" }, "Operator sam ustawi hasło i MFA. Role uprzywilejowane nadaje się później - wymagają zatwierdzenia przez oficera bezpieczeństwa."),
          el("button", { type: "submit" }, "Dodaj operatora"));
        createCard = card(el("h3", {}, "Nowy operator"), form);
      }
      show(card(el("h2", {}, "Operatorzy Forvium"),
          el("p", { class: "muted" }, "Każda zmiana wymaga ponownej weryfikacji i trafia do audytu. Nie możesz zmienić własnej roli ani zablokować własnego konta.")),
        card(table(["E-mail", "Nazwa", "Rola", "Zmiana roli", "Konto", "Klucz", ""], rows)), createCard);
    } catch (e) { show(errorCard(e)); }
  }

  // ------------------------------------------------------------ moje prosby
  async function renderMyRequestsPage() {
    const show = begin();
    const { requests } = await api("/api/admin/support-access/requests");
    const rows = requests.map((r) => {
      const actions = el("td", { class: "row" });
      if (r.status === "pending" || r.status === "pending_second_approval") {
        actions.append(el("button", { class: "secondary", onclick: async () => {
          await api(`/api/admin/support-access/requests/${r.id}/cancel`, { method: "POST" }).catch((e) => alert(e.message));
          renderMyRequestsPage();
        } }, "Anuluj"));
      }
      if (r.active_session) {
        actions.append(el("button", { class: "secondary", onclick: async () => {
          const minutes = prompt("O ile minut przedłużyć sesję? (maks. 15)", "15");
          if (!minutes) return;
          const reason = prompt("Powód przedłużenia (klient zobaczy go w powiadomieniu):");
          if (!reason) return;
          try {
            const proof = await stepUp("Przedłużenie sesji.", { requireKey: r.mode === "break_glass" });
            if (!proof) return;
            await api(`/api/admin/support-access/sessions/${r.active_session.id}/extend`, { method: "POST",
              body: { minutes: Number(minutes), reason, ...proof } });
          } catch (e) { alert(e.message); }
          renderMyRequestsPage();
        } }, "Przedłuż"));
        actions.append(el("button", { class: "danger", onclick: async () => {
          await api(`/api/admin/support-access/sessions/${r.active_session.id}/end`, { method: "POST" }).catch((e) => alert(e.message));
          renderMyRequestsPage();
        } }, "Zakończ sesję"));
      } else if (r.status === "approved" && r.consent && !r.consent.revoked_at && new Date(r.consent.valid_until) > new Date()) {
        actions.append(el("button", { onclick: async () => {
          try {
            const proof = await stepUp("Uruchomienie sesji wsparcia.", { requireKey: r.mode === "break_glass" });
            if (!proof) return;
            const s = await api(`/api/admin/support-access/requests/${r.id}/sessions`, { method: "POST", body: proof });
            // Osobna karta app.forvium.com (noopener izoluje ja od panelu admin). Link zamiast window.open,
            // bo po ceremonii WebAuthn przegladarka zablokowalaby automatycznie otwierane okno.
            actions.replaceChildren(el("a", { class: "button-link", href: s.launch_url, target: "_blank",
              rel: "noopener noreferrer" }, "Otwórz sesję wsparcia (kod ważny 60 s)"));
          } catch (e) { alert(e.message); renderMyRequestsPage(); }
        } }, "Uruchom sesję"));
      }
      const status = r.consent && r.consent.revoked_at ? "zgoda cofnięta" : r.status;
      return el("tr", {}, el("td", {}, fmt(r.created_at)), el("td", {}, r.ticket_number),
        el("td", {}, r.mode === "break_glass" ? el("span", { class: "danger-text" }, "BREAK GLASS") : "standardowy"),
        el("td", {}, el("span", { class: "pill" }, status)),
        el("td", {}, (r.consent ? r.consent.scopes : r.scopes).map((s) => SCOPE_LABELS[s] || s).join(", ")),
        el("td", {}, r.consent ? fmt(r.consent.valid_until) : "—"), actions);
    });
    show(card(el("h3", {}, "Moje prośby o dostęp"),
      table(["Data", "Zgłoszenie", "Tryb", "Status", "Zakres", "Zgoda do", ""], rows)));
  }

  // ------------------------------------------------------------ nadzor sesji
  async function renderOversight(status = "active") {
    const show = begin();
    const sel = el("select", {}, ...[["active", "Aktywne"], ["", "Wszystkie"], ["ended", "Zakończone"], ["expired", "Wygasłe"], ["revoked", "Cofnięte"]]
      .map(([v, l]) => el("option", { value: v, selected: v === status }, l)));
    sel.onchange = () => renderOversight(sel.value);
    try {
      const { sessions } = await api("/api/admin/support-access/oversight/sessions" + (status ? "?status=" + status : ""));
      const rows = sessions.map((s) => el("tr", {},
        el("td", {}, fmt(s.started_at)), el("td", {}, s.operator_email), el("td", {}, s.organization_name),
        el("td", {}, s.ticket_number), el("td", {}, s.mode === "break_glass" ? el("span", { class: "danger-text" }, "BREAK GLASS") : "standardowy"),
        el("td", {}, el("span", { class: "pill" }, s.status)), el("td", {}, fmt(s.ended_at || s.expires_at)),
        el("td", { class: "row" },
          el("button", { class: "secondary", onclick: () => renderAudit({ support_session_id: s.id }) }, "Audyt"),
          can(P.audit) ? el("button", { class: "secondary", onclick: () => renderRecording(s) }, "Nagranie") : "",
          s.status === "active" ? el("button", { class: "danger", onclick: async () => {
            if (!confirm("Zakończyć tę sesję wsparcia?")) return;
            await api(`/api/admin/support-access/oversight/sessions/${s.id}/terminate`, { method: "POST" }).catch((e) => alert(e.message));
            renderOversight(status);
          } }, "Zakończ") : "")));
      show(card(el("h2", {}, "Nadzór sesji wsparcia"), el("label", {}, "Status"), sel),
        card(table(["Start", "Operator", "Organizacja", "Zgłoszenie", "Tryb", "Status", "Koniec", ""], rows)));
    } catch (e) { show(errorCard(e)); }
  }

  // ------------------------------------------------------------------ audyt
  async function renderAudit(initial = {}, offset = 0) {
    const show = begin();
    const fields = [["operator_id", "ID operatora"], ["organization_id", "ID organizacji"], ["ticket", "Zgłoszenie"],
      ["support_session_id", "ID sesji"], ["action_prefix", "Akcja (prefiks)"], ["since", "Od (RRRR-MM-DD)"], ["until", "Do (RRRR-MM-DD)"]];
    const inputs = Object.fromEntries(fields.map(([k]) => [k, el("input", { value: initial[k] || "" })]));
    const outcome = el("select", {}, ...[["", "Każdy wynik"], ["success", "Sukces"], ["denied", "Odmowa"]].map(([v, l]) => el("option", { value: v, selected: v === (initial.outcome || "") }, l)));
    const bg = el("select", {}, ...[["", "Wszystkie"], ["true", "Tylko Break Glass"]].map(([v, l]) => el("option", { value: v, selected: v === (initial.break_glass || "") }, l)));
    const params = () => {
      const p = new URLSearchParams();
      for (const [k, i] of Object.entries(inputs)) if (i.value.trim()) p.set(k, i.value.trim());
      if (outcome.value) p.set("outcome", outcome.value);
      if (bg.value) p.set("break_glass", bg.value);
      return p;
    };
    const current = () => Object.fromEntries([...params().entries()]);
    const results = el("div");
    const form = el("form", { class: "card", onsubmit: (e) => { e.preventDefault(); renderAudit(current(), 0); } },
      el("h2", {}, "Audyt"),
      el("div", { class: "filters" }, ...fields.map(([k, label]) => el("div", {}, el("label", {}, label), inputs[k])),
        el("div", {}, el("label", {}, "Wynik"), outcome), el("div", {}, el("label", {}, "Tryb"), bg)),
      el("div", { class: "row spaced" }, el("button", { type: "submit" }, "Szukaj"),
        el("button", { type: "button", class: "secondary", onclick: async () => {
          try {
            const r = await api("/api/admin/audit/export.csv?" + params(), { raw: true });
            const url = URL.createObjectURL(await r.blob());
            el("a", { href: url, download: "forvium-audit.csv" }).click();
            URL.revokeObjectURL(url);
          } catch (e) { alert(e.message); }
        } }, "Eksport CSV")));
    show(form, results);
    try {
      const p = params();
      p.set("limit", "50");
      p.set("offset", String(offset));
      const data = await api("/api/admin/audit?" + p);
      const rows = data.events.map((e) => el("tr", {},
        el("td", {}, fmt(e.occurred_at)), el("td", {}, e.is_break_glass ? el("span", { class: "danger-text" }, e.action) : e.action),
        el("td", {}, el("span", { class: "pill" }, e.outcome)), el("td", {}, e.actor_type, " ", e.actor_user_id || ""),
        el("td", {}, e.on_behalf_of_user_id || ""), el("td", {}, e.method ? `${e.method} ${e.route} → ${e.status_code}` : ""),
        el("td", {}, e.details && e.details.reason ? e.details.reason : "")));
      results.replaceChildren(card(
        el("p", { class: "muted" }, `Wyniki ${data.total ? offset + 1 : 0}–${offset + data.events.length} z ${data.total}`),
        table(["Czas", "Akcja", "Wynik", "Wykonawca", "W imieniu", "Operacja API", "Powód"], rows),
        el("div", { class: "pager" },
          el("button", { class: "secondary", disabled: offset === 0, onclick: () => renderAudit(current(), Math.max(0, offset - 50)) }, "← Poprzednie"),
          el("button", { class: "secondary", disabled: offset + 50 >= data.total, onclick: () => renderAudit(current(), offset + 50) }, "Następne →"))));
    } catch (e) { results.replaceChildren(errorCard(e)); }
  }

  // ------------------------------------------------------------ Break Glass
  async function renderBreakGlass() {
    const show = begin();
    try {
      const [pending, reviews] = await Promise.all([
        can(P.bgApprove) ? api("/api/admin/break-glass/requests?status=pending_second_approval") : { requests: [] },
        can(P.bgApprove) ? api("/api/admin/break-glass/requests?review_pending=true") : { requests: [] },
      ]);
      const pendingCards = pending.requests.map((r) => card(
        el("h3", { class: "danger-text" }, "Wniosek Break Glass · ", r.ticket_number),
        el("p", {}, "Operator: ", r.operator_id, " · Organizacja: ", r.organization_id),
        el("p", {}, "Kategoria: ", CATEGORY_LABELS[r.incident_category] || r.incident_category, " · Czas: ", r.duration_minutes, " min · Wygasa: ", fmt(r.decision_deadline)),
        el("p", {}, "Zakres: ", r.scopes.map((s) => SCOPE_LABELS[s] || s).join(", ")),
        el("pre", { class: "body" }, r.reason),
        el("div", { class: "row spaced" },
          el("button", { class: "danger", onclick: async () => {
            try {
              const proof = await stepUp("Zatwierdzenie Break Glass.", { requireKey: true });
              if (!proof) return;
              await api(`/api/admin/break-glass/requests/${r.id}/approve`, { method: "POST", body: proof });
            } catch (e) { alert(e.message); }
            renderBreakGlass();
          } }, "Zatwierdź (4 oczy)"),
          el("button", { class: "secondary", onclick: async () => {
            const note = prompt("Powód odrzucenia:");
            if (note === null) return;
            await api(`/api/admin/break-glass/requests/${r.id}/reject`, { method: "POST", body: { note } }).catch((e) => alert(e.message));
            renderBreakGlass();
          } }, "Odrzuć"))));
      const reviewCards = reviews.requests.map((r) => {
        const notes = el("textarea", { rows: 3, placeholder: "Ustalenia przeglądu (min. 50 znaków)" });
        return card(
          el("h3", {}, "Przegląd po incydencie · ", r.ticket_number),
          el("p", {}, "Wnioskowal: ", r.operator_id, " · Zatwierdził: ", r.decided_by_user_id || "—"),
          el("p", {}, "Sesje: ", r.sessions.map((s) => `${fmt(s.started_at)} (${s.status})`).join(", ") || "brak"),
          el("button", { class: "secondary", onclick: () => renderAudit({ break_glass: "true" }) }, "Zdarzenia Break Glass w audycie"),
          ...(can(P.bgReview) ? [notes, el("button", { class: "spaced", onclick: async () => {
            await api(`/api/admin/break-glass/requests/${r.id}/review`, { method: "POST", body: { notes: notes.value } })
              .then(() => renderBreakGlass()).catch((e) => alert(e.message));
          } }, "Zakończ przegląd i wyślij raport klientowi")] : []));
      });
      show(
        card(el("h2", {}, "Break Glass"), el("p", { class: "muted" }, "Wnioski awaryjne wymagają zatwierdzenia przez innego oficera bezpieczeństwa niż wnioskujący, a każde użycie - niezależnego przeglądu.")),
        card(el("h3", {}, "Oczekujące na zatwierdzenie")), ...(pendingCards.length ? pendingCards : [card(el("p", { class: "muted" }, "Brak wniosków."))]),
        card(el("h3", {}, "Do przeglądu")), ...(reviewCards.length ? reviewCards : [card(el("p", { class: "muted" }, "Brak."))]));
    } catch (e) { show(errorCard(e)); }
  }

  // ------------------------------------------------------------ nagrania
  async function renderRecording(sess) {
    const show = begin();
    const base = `/api/admin/support-access/sessions/${sess.id}/recording`;
    const { frames } = await api(base);
    if (!frames.length) return show(card(el("p", { class: "muted" }, "Brak nagrania tej sesji.")));
    const frame = snapshotFrame();
    const caption = el("p", { class: "muted" });
    const slider = el("input", { type: "range", min: 1, max: frames.length, value: 1, class: "slider" });
    const load = async () => {
      const f = frames[Number(slider.value) - 1];
      frame.show((await api(`${base}/${f.seq}`)).html);  // kazde otwarcie klatki trafia do audytu
      caption.textContent = `Klatka ${slider.value}/${frames.length} · ${fmt(f.captured_at)} · widok: ${f.view}`;
    };
    slider.onchange = load;
    show(card(el("h2", {}, "Nagranie sesji ", sess.ticket_number),
      el("p", { class: "danger-text" }, "Nagranie zawiera dane klienta. Otwarcie każdej klatki jest rejestrowane w audycie."),
      caption, slider, frame));
    load();
  }

  // -------------------------------------------------------------- alerty
  async function renderAlerts(status = "open") {
    const show = begin();
    const sel = el("select", {}, ...[["open", "Otwarte"], ["acknowledged", "Przyjęte"], ["resolved", "Rozwiązane"], ["", "Wszystkie"]]
      .map(([v, l]) => el("option", { value: v, selected: v === status }, l)));
    sel.onchange = () => renderAlerts(sel.value);
    try {
      const [{ alerts }, jobs] = await Promise.all([api("/api/admin/security/alerts?status=" + status), api("/api/admin/security/jobs")]);
      const act = (a, action) => async () => {
        const notes = action === "resolve" ? prompt("Jak rozwiązano alert?") : "";
        if (notes === null) return;
        await api(`/api/admin/security/alerts/${a.id}/${action}`, { method: "POST", body: { notes } }).catch((e) => alert(e.message));
        renderAlerts(status);
      };
      const rows = alerts.map((a) => el("tr", {},
        el("td", {}, fmt(a.created_at)), el("td", { class: "sev-" + a.severity }, a.severity),
        el("td", {}, a.title, a.auto_action ? el("div", { class: "muted" }, "akcja automatyczna: ", a.auto_action) : ""),
        el("td", {}, a.operator_user_id || "—"), el("td", {}, el("span", { class: "pill" }, a.status)),
        el("td", { class: "row" },
          a.support_session_id && can(P.audit) ? el("button", { class: "secondary", onclick: () => renderAudit({ support_session_id: a.support_session_id }) }, "Audyt") : "",
          a.status === "open" ? el("button", { class: "secondary", onclick: act(a, "acknowledge") }, "Przyjmij") : "",
          a.status !== "resolved" ? el("button", { onclick: act(a, "resolve") }, "Rozwiąż") : "")));
      // Zatrzymany worker = brak wygaszania sesji, e-maili i wykrywania anomalii.
      const jobsCard = card(el("h3", {}, "Zadania w tle"),
        jobs.stale.length ? el("p", { class: "danger-text" }, "Zadania nie działają: ", jobs.stale.join(", "), ". Sprawdź kontener worker.") : "",
        table(["Zadanie", "Ostatni udany przebieg", "Przebiegi / błędy", "Ostatni błąd", "Stan"], jobs.jobs.map((j) => el("tr", {},
          el("td", {}, j.job), el("td", {}, fmt(j.last_success_at)), el("td", {}, `${j.runs} / ${j.failures}`),
          el("td", {}, j.last_error ? `${fmt(j.last_error_at)}: ${j.last_error}` : "—"),
          el("td", {}, el("span", { class: "pill" + (j.stale ? " sev-high" : "") }, j.stale ? "zatrzymane" : "działa"))))));
      show(card(el("h2", {}, "Alerty bezpieczeństwa"), el("label", {}, "Status"), sel),
        card(table(["Czas", "Waga", "Alert", "Operator", "Status", ""], rows)), jobsCard);
    } catch (e) { show(errorCard(e)); }
  }

  // ------------------------------------------------- raporty dostepu (PDF)
  async function downloadPdf(path, fallbackName) {
    const r = await api(path, { raw: true });
    const name = (r.headers.get("Content-Disposition") || "").match(/filename="([^"]+)"/);
    const url = URL.createObjectURL(await r.blob());
    const a = el("a", { href: url, download: name ? name[1] : fallbackName });
    document.body.append(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 10000);
  }

  async function renderReports() {
    const show = begin();
    try {
      const { reports } = await api("/api/admin/access-reports");
      const rows = reports.map((r) => el("tr", {},
        el("td", {}, r.period_label), el("td", {}, r.kind === "auditor" ? "audytor (cała platforma)" : "klient"),
        el("td", {}, r.organization_name || "—"),
        el("td", {}, fmt(r.created_at)), el("td", { class: "mono", title: r.sha256 }, r.sha256.slice(0, 16) + "…"),
        el("td", {}, el("button", { class: "secondary", onclick: () => downloadPdf(`/api/admin/access-reports/${r.id}/pdf`, `raport-${r.period_start}.pdf`).catch((e) => alert(e.message)) }, "Pobierz PDF"))));
      const month = el("input", { type: "month" });
      show(card(el("h2", {}, "Raporty dostępu serwisowego"),
          el("p", { class: "muted" }, "Raporty miesięczne tworzą się automatycznie po zakończeniu miesiąca: dla każdej organizacji (wysyłany klientowi) i zbiorczy dla audytorów. Każde pobranie trafia do audytu."),
          el("div", { class: "row" }, month, el("button", { onclick: async () => {
            if (!month.value) return;
            const [year, m] = month.value.split("-").map(Number);
            try {
              await api("/api/admin/access-reports", { method: "POST", body: { kind: "auditor", year, month: m } });
              renderReports();
            } catch (e) { alert(e.message); }
          } }, "Utwórz raport audytora za miesiąc"))),
        card(table(["Okres", "Rodzaj", "Organizacja", "Utworzono", "SHA-256", ""], rows)));
    } catch (e) { show(errorCard(e)); }
  }

  // ------------------------------------------------------- konto (klucze)
  // Zmiana hasla operatora: obecne haslo + ponowna weryfikacja (klucz albo kod MFA).
  function passwordCard(forced) {
    const msg = el("p");
    const form = el("form", { onsubmit: async (e) => {
      e.preventDefault();
      const f = Object.fromEntries(new FormData(form));
      if (f.new_password !== f.repeat) { msg.className = "error"; msg.textContent = "Hasła nie są takie same."; return; }
      try {
        const proof = await stepUp("Zmiana hasła.");
        if (!proof) return;
        await api("/api/admin/account/password", { method: "POST", body: { current_password: f.current_password, new_password: f.new_password, ...proof } });
        if (forced) return start();
        msg.className = ""; msg.textContent = "Hasło zmienione. Pozostałe sesje zostały wylogowane.";
        form.reset();
      } catch (err) { msg.className = "error"; msg.textContent = err.message; }
    } },
      el("label", {}, "Obecne hasło"), el("input", { name: "current_password", type: "password", required: true, autocomplete: "current-password" }),
      el("label", {}, "Nowe hasło (min. 12 znaków)"), el("input", { name: "new_password", type: "password", required: true, minlength: 12, autocomplete: "new-password" }),
      el("label", {}, "Powtórz nowe hasło"), el("input", { name: "repeat", type: "password", required: true, autocomplete: "new-password" }),
      msg, el("button", { type: "submit" }, "Zmień hasło"));
    return card(el("h2", {}, forced ? "Wymagana zmiana hasła" : "Zmiana hasła"),
      el("p", { class: forced ? "danger-text" : "muted" }, forced
        ? "Twoje hasło nie spełnia polityki bezpieczeństwa (np. wystąpiło w znanym wycieku danych). Ustaw nowe, aby kontynuować."
        : "Hasło nie może pochodzić ze znanych wycieków ani zawierać Twojego adresu e-mail lub imienia."),
      form);
  }

  async function renderAccount() {
    const show = begin();
    myKeys = (await api("/api/admin/webauthn/credentials")).credentials;
    const msg = el("p");
    const rows = myKeys.map((k) => el("tr", {}, el("td", {}, k.name), el("td", {}, fmt(k.created_at)), el("td", {}, fmt(k.last_used_at)),
      el("td", {}, el("button", { class: "danger", onclick: async () => {
        if (!confirm(`Usunąć klucz "${k.name}"?`)) return;
        try {
          const proof = await stepUp("Usunięcie klucza.");
          if (!proof) return;
          await api(`/api/admin/webauthn/credentials/${k.id}/remove`, { method: "POST", body: proof });
        } catch (e) { alert(e.message); }
        renderAccount();
      } }, "Usuń"))));
    const name = el("input", { value: "Klucz bezpieczeństwa", maxlength: 100 });
    show(card(el("h2", {}, "Klucze bezpieczeństwa (WebAuthn / passkeys)"),
      el("p", { class: "muted" }, "Klucz sprzętowy FIDO2 lub passkey z weryfikacja (PIN / biometria). Zastępuje kod TOTP przy ponownej weryfikacji i jest wymagany w procedurze Break Glass."),
      table(["Nazwa", "Dodany", "Ostatnio użyty", ""], rows),
      el("label", {}, "Nazwa nowego klucza"), name, msg,
      el("button", { class: "spaced", onclick: async () => {
        try {
          const proof = await stepUp("Dodanie klucza bezpieczeństwa.");
          if (!proof) return;
          const { options } = await api("/api/admin/webauthn/register/options", { method: "POST", body: proof });
          const credential = await createKey(options);
          await api("/api/admin/webauthn/register/verify", { method: "POST", body: { credential, name: name.value } });
          renderAccount();
        } catch (e) { msg.className = "error"; msg.textContent = e.message; }
      } }, "Dodaj klucz")), passwordCard(false));
  }

  // --------------------------------------------------------- powiadomienia
  async function renderNotifications() {
    const show = begin();
    const { notifications } = await api("/api/admin/notifications");
    show(card(el("h2", {}, "Powiadomienia")),
      ...(notifications.length ? notifications.map((n) => card(el("h3", {}, n.title), el("p", { class: "muted" }, fmt(n.created_at)), el("pre", { class: "body" }, n.body)))
        : [card(el("p", { class: "muted" }, "Brak powiadomień."))]));
  }

  start();
})();
