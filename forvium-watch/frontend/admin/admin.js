// admin.forvium.com - Uzytkownicy -> Szczegoly uzytkownika -> Dostep serwisowy.
(() => {
  const API = window.FORVIUM_API;
  const KEY = "fw_operator_token";
  const root = document.getElementById("root");
  const SCOPE_LABELS = {
    dashboard: "Dashboard organizacji",
    units: "Struktura jednostek",
    technologies_cve: "Technologie i CVE",
    diagnostics: "Bledy i stan konfiguracji",
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
    const t = sessionStorage.getItem(KEY);
    if (t) headers.Authorization = "Bearer " + t;
    const r = await fetch(API + path, { ...opts, headers, body: opts.body ? JSON.stringify(opts.body) : undefined });
    const data = await r.json().catch(() => ({}));
    if (!r.ok) throw Object.assign(new Error(data.message || "Blad " + r.status), { status: r.status, code: data.error });
    return data;
  }
  const fmt = (iso) => (iso ? new Date(iso).toLocaleString("pl-PL") : "—");
  const askMfa = () => prompt("Ponowna weryfikacja MFA - podaj kod z aplikacji uwierzytelniajacej:");

  function renderLogin(error) {
    const form = el("form", { class: "card", onsubmit: async (e) => {
      e.preventDefault();
      try {
        const r = await api("/api/admin/auth/login", { method: "POST", body: Object.fromEntries(new FormData(form)) });
        sessionStorage.setItem(KEY, r.token);
        renderUsers();
      } catch (err) { renderLogin(err.message); }
    } },
      el("h2", {}, "Logowanie operatora"),
      el("label", {}, "E-mail"), el("input", { name: "email", type: "email", required: true }),
      el("label", {}, "Haslo"), el("input", { name: "password", type: "password", required: true }),
      el("label", {}, "Kod MFA"), el("input", { name: "mfa_code", required: true, inputmode: "numeric" }),
      el("p", { class: "error" }, error || ""),
      el("button", { type: "submit" }, "Zaloguj"));
    root.replaceChildren(form);
  }

  // ---------------------------------------------------------------- uzytkownicy
  async function renderUsers(q = "") {
    let me;
    try { me = await api("/api/admin/me"); } catch (_) { return renderLogin(); }
    document.getElementById("who").textContent = `${me.user.display_name} (${me.platform_role}) · ID ${me.user.id}`;
    const { users } = await api("/api/admin/users?q=" + encodeURIComponent(q));
    const search = el("input", { placeholder: "Szukaj po e-mailu lub nazwie", value: q });
    search.onchange = () => renderUsers(search.value);
    root.replaceChildren(
      el("div", { class: "card" }, el("h2", {}, "Uzytkownicy"), search),
      el("div", { class: "card" }, el("table", {}, el("tr", {}, el("th", {}, "E-mail"), el("th", {}, "Nazwa"), el("th", {}, "")),
        ...users.map((u) => el("tr", {}, el("td", {}, u.email), el("td", {}, u.display_name),
          el("td", {}, el("button", { class: "secondary", onclick: () => renderUserDetail(u.id) }, "Szczegoly")))))),
      el("div", { id: "my-requests" }));
    renderMyRequests(document.getElementById("my-requests"));
  }

  async function renderUserDetail(userId) {
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
      el("input", { type: "checkbox", value: s, checked: true, style: "width:auto" }), " ", SCOPE_LABELS[s] || s));
    const msg = el("p");

    const form = el("form", { class: "card", onsubmit: async (e) => {
      e.preventDefault();
      const f = Object.fromEntries(new FormData(form));
      try {
        await api("/api/admin/support-access/requests", { method: "POST", body: {
          organization_id: f.organization_id, reference_user_id: u.id, reason: f.reason, ticket_number: f.ticket_number,
          duration_minutes: Number(f.duration_minutes),
          scopes: scopeBoxes.map((l) => l.querySelector("input")).filter((i) => i.checked).map((i) => i.value),
          mfa_code: f.mfa_code,
        } });
        msg.className = ""; msg.textContent = "Prosba wyslana. Klient otrzymal powiadomienie w aplikacji i e-mail.";
        form.reset();
        renderMyRequests(document.getElementById("my-requests"));
      } catch (err) { msg.className = "error"; msg.textContent = err.message; }
    } },
      el("h3", {}, "Dostep serwisowy"),
      el("p", { class: "muted" }, "Sesja w trybie READ_ONLY, wymaga zgody klienta. Maksymalny czas: ", policy.max_session_minutes, " min."),
      el("label", {}, "Organizacja"), orgSel,
      el("label", {}, "Uzytkownik referencyjny"), el("input", { value: `${u.display_name} <${u.email}>`, disabled: true }),
      el("label", {}, "Powod dostepu"), el("textarea", { name: "reason", required: true, minlength: 15, rows: 3 }),
      el("label", {}, "Numer zgloszenia"), ticketSel,
      el("label", {}, "Czas dostepu (min)"), el("input", { name: "duration_minutes", type: "number", min: 1, max: policy.max_session_minutes, value: policy.default_session_minutes }),
      el("label", {}, "Zakres"), ...scopeBoxes,
      el("label", {}, "Ponowna weryfikacja MFA"), el("input", { name: "mfa_code", required: true, inputmode: "numeric", autocomplete: "one-time-code" }),
      msg,
      el("button", { type: "submit" }, "Wyslij prosbe o dostep"));

    root.replaceChildren(
      el("div", { class: "card" }, el("a", { onclick: () => renderUsers() }, "← Uzytkownicy"),
        el("h2", {}, u.display_name), el("p", { class: "muted" }, u.email, " · ID ", u.id)),
      detail.organizations.length ? form : el("div", { class: "card muted" }, "Uzytkownik nie nalezy do zadnej organizacji."),
      el("div", { id: "my-requests" }));
    if (detail.organizations.length) await loadTickets();
    renderMyRequests(document.getElementById("my-requests"));
  }

  // ------------------------------------------------------------ moje prosby
  async function renderMyRequests(container) {
    const { requests } = await api("/api/admin/support-access/requests");
    const rows = requests.map((r) => {
      const actions = el("td", { class: "row" });
      if (r.status === "pending") {
        actions.append(el("button", { class: "secondary", onclick: async () => {
          await api(`/api/admin/support-access/requests/${r.id}/cancel`, { method: "POST" }).catch((e) => alert(e.message));
          renderMyRequests(container);
        } }, "Anuluj"));
      }
      if (r.active_session) {
        actions.append(el("button", { class: "danger", onclick: async () => {
          await api(`/api/admin/support-access/sessions/${r.active_session.id}/end`, { method: "POST" }).catch((e) => alert(e.message));
          renderMyRequests(container);
        } }, "Zakoncz sesje"));
      } else if (r.status === "approved" && r.consent && !r.consent.revoked_at && new Date(r.consent.valid_until) > new Date()) {
        actions.append(el("button", { onclick: async () => {
          const code = askMfa();
          if (!code) return;
          try {
            const s = await api(`/api/admin/support-access/requests/${r.id}/sessions`, { method: "POST", body: { mfa_code: code } });
            // Osobna karta app.forvium.com; noopener izoluje ja od sesji panelu admin.
            window.open(s.launch_url, "_blank", "noopener,noreferrer");
          } catch (e) { alert(e.message); }
          renderMyRequests(container);
        } }, "Uruchom sesje"));
      }
      return el("tr", {}, el("td", {}, fmt(r.created_at)), el("td", {}, r.ticket_number), el("td", {}, r.organization_id),
        el("td", {}, el("span", { class: "pill" }, r.consent && r.consent.revoked_at ? "zgoda cofnieta" : r.status)),
        el("td", {}, r.consent ? r.consent.scopes.join(", ") : r.scopes.join(", ")),
        el("td", {}, r.consent ? fmt(r.consent.valid_until) : "—"), actions);
    });
    container.replaceChildren(el("div", { class: "card" }, el("h3", {}, "Moje prosby o dostep"), el("table", {},
      el("tr", {}, ...["Data", "Zgloszenie", "Organizacja", "Status", "Zakres", "Zgoda do", ""].map((t) => el("th", {}, t))), ...rows)));
  }

  renderUsers();
})();
