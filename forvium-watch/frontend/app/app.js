// app.forvium.com - panel klienta (tryb zwykly i tryb wsparcia Forvium).
(() => {
  const { t: tr, fmtDate, switcher, header: LANG_HEADER } = window.FW_I18N;
  const API = window.FORVIUM_API;
  const SUPPORT_KEY = "fw_support_token";
  const USER_KEY = "fw_user_token";
  const root = document.getElementById("root");
  const banner = document.getElementById("support-banner");

  const supportToken = sessionStorage.getItem(SUPPORT_KEY);
  const token = () => supportToken || sessionStorage.getItem(USER_KEY);
  const SCOPE_LABELS = {
    dashboard: tr("Dashboard organizacji"),
    units: tr("Struktura jednostek"),
    technologies_cve: tr("Technologie i CVE"),
    diagnostics: tr("Błędy i stan konfiguracji"),
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
    const headers = { "Content-Type": "application/json", ...LANG_HEADER };
    if (token()) headers.Authorization = "Bearer " + token();
    const r = await fetch(API + path, { ...opts, headers, body: opts.body ? JSON.stringify(opts.body) : undefined });
    const data = await r.json().catch(() => ({}));
    if (r.status === 401 && supportToken) supportEnded();
    if (!r.ok) throw Object.assign(new Error(data.message || tr("Błąd ") + r.status), { status: r.status, code: data.error });
    return data;
  }

  const fmt = fmtDate;
  // Wybor jezyka zalogowany klient zapisuje tez na koncie (powiadomienia, e-maile); operator w trybie wsparcia - nie.
  document.querySelector("header.top").append(switcher((lang) => (!supportToken && sessionStorage.getItem(USER_KEY)
    ? api("/api/app/account/locale", { method: "PUT", body: { locale: lang } }) : null)));
  const card = (...children) => el("div", { class: "card" }, ...children);
  const checkedValues = (labels) => labels.map((l) => l.querySelector("input")).filter((i) => i.checked).map((i) => i.value);
  const askMfa = (what) => prompt(what + "\n" + tr("Potwierdź kodem MFA z aplikacji uwierzytelniającej:"));

  // Podglad zrzutu widoku operatora: iframe w piaskownicy BEZ skryptow (tresc i tak jest sanityzowana na serwerze).
  function snapshotFrame() {
    const frame = el("iframe", { class: "snapshot", sandbox: "", title: tr("Widok operatora Forvium"), referrerpolicy: "no-referrer" });
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
    banner.replaceChildren(el("span", { class: "title" }, tr("Sesja wsparcia Forvium zakończona")));
    root.replaceChildren(card(tr("Dostęp serwisowy wygasł lub został zakończony. Możesz zamknąć tę kartę.")));
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
      timeEl.textContent = tr("Pozostały czas: {time}", { time: `${m}:${s}` });
      remaining -= 1;
    };
    banner.hidden = false;
    banner.replaceChildren(
      el("span", { class: "title" }, info.banner),
      el("span", { class: "meta" },
        el("span", {}, tr("Organizacja: "), info.organization.name),
        el("span", {}, tr("Operator: "), info.operator_id),
        el("span", {}, tr("Zgłoszenie: "), info.ticket_number),
        el("span", {}, tr("Klient widzi ten ekran na żywo")),
        timeEl),
      el("button", { onclick: async () => {
        try { await api("/api/app/support/session/end", { method: "POST" }); } catch (_) {}
        supportEnded();
      } }, tr("Zakończ dostęp")),
    );
    tick();
    bannerTimer = setInterval(tick, 1000);
    // Rewalidacja co 15 s: przedluzenie sesji, cofniecie zgody, zakonczenie przez klienta.
    setInterval(() => api("/api/app/support/session").then((i) => { remaining = i.remaining_seconds; }).catch(() => {}), 15000);
    document.getElementById("who").textContent = tr("Widok użytkownika: ") + info.reference_user.display_name;
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
      el("h2", {}, tr("Logowanie")),
      el("label", {}, tr("E-mail")), el("input", { name: "email", type: "email", required: true, autocomplete: "username" }),
      el("label", {}, tr("Hasło")), el("input", { name: "password", type: "password", required: true, autocomplete: "current-password" }),
      el("label", {}, tr("Kod MFA")), el("input", { name: "mfa_code", inputmode: "numeric", autocomplete: "one-time-code" }),
      el("p", { class: "error" }, error || ""),
      el("button", { type: "submit" }, tr("Zaloguj")));
    root.replaceChildren(form);
  }

  let currentUserId = null;
  async function renderHome() {
    let me;
    try { me = await api("/api/app/me"); } catch (_) { return renderLogin(); }
    currentUserId = me.user.id;
    document.getElementById("who").textContent = me.user.display_name;
    if (me.password_change_required) return root.replaceChildren(passwordCard(true));
    if (me.organizations.length === 1) return renderOrg(me.organizations[0]);
    root.replaceChildren(card(el("h2", {}, tr("Organizacje")),
      ...me.organizations.map((o) => el("p", {}, el("a", { href: "#", onclick: (e) => { e.preventDefault(); renderOrg(o); } }, o.name)))));
  }

  // Zmiana hasla (takze wymuszona, gdy haslo pojawilo sie w wycieku albo nie spelnia polityki).
  function passwordCard(forced) {
    const msg = el("p");
    const form = el("form", { onsubmit: async (e) => {
      e.preventDefault();
      const f = Object.fromEntries(new FormData(form));
      if (f.new_password !== f.repeat) { msg.className = "error"; msg.textContent = tr("Hasła nie są takie same."); return; }
      try {
        await api("/api/app/account/password", { method: "POST", body: { current_password: f.current_password, new_password: f.new_password } });
        if (forced) return renderHome();
        msg.className = ""; msg.textContent = tr("Hasło zmienione. Pozostałe sesje zostały wylogowane.");
        form.reset();
      } catch (err) { msg.className = "error"; msg.textContent = err.message; }
    } },
      el("label", {}, tr("Obecne hasło")), el("input", { name: "current_password", type: "password", required: true, autocomplete: "current-password" }),
      el("label", {}, tr("Nowe hasło (min. 12 znaków)")), el("input", { name: "new_password", type: "password", required: true, minlength: 12, autocomplete: "new-password" }),
      el("label", {}, tr("Powtórz nowe hasło")), el("input", { name: "repeat", type: "password", required: true, autocomplete: "new-password" }),
      msg, el("button", { type: "submit" }, tr("Zmień hasło")));
    return card(el("h2", {}, forced ? tr("Wymagana zmiana hasła") : tr("Zmiana hasła")),
      el("p", { class: forced ? "danger-text" : "muted" }, forced
        ? tr("Twoje hasło nie spełnia polityki bezpieczeństwa (np. wystąpiło w znanym wycieku danych). Ustaw nowe, aby kontynuować.")
        : tr("Hasło nie może pochodzić ze znanych wycieków ani zawierać Twojego adresu e-mail lub imienia. Najlepsze są długie frazy, np. kilka słów.")),
      form);
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
      views["Zgłoszenia"] = (pane) => viewTickets(org, pane);
      views["Członkowie"] = (pane) => viewMembers(org, pane);
      views["Konto"] = (pane) => pane.replaceChildren(passwordCard(false));
      views["Dostęp serwisowy"] = (pane) => viewSupportAccess(org, pane);
      views["Powiadomienia"] = (pane) => viewNotifications(pane);
    }
    const nav = el("nav", { class: "card" }, el("strong", {}, org.name, " "),
      ...Object.entries(views).map(([label, fn]) => el("a", { onclick: () => show(label, fn) }, tr(label))));
    root.replaceChildren(nav, content);
    show("Dashboard", views["Dashboard"]);
  }

  async function guarded(content, fn) {
    try { await fn(); } catch (e) {
      content.replaceChildren(el("div", { class: "card error" },
        e.code === "forbidden_in_support_mode" ? tr("Ta sekcja nie jest objęta zgodą na dostęp serwisowy.") : e.message));
    }
  }

  const STATE_LABELS = { active: tr("aktywne"), pending_activation: tr("czeka na aktywację"), blocked: tr("zablokowane przez Forvium"), inactive: tr("nieaktywne") };
  const ORG_ROLE_LABELS = { owner: tr("właściciel"), admin: tr("administrator"), member: tr("członek"), viewer: tr("podgląd") };

  const TICKET_STATUS = { open: tr("otwarte"), in_progress: tr("w toku"), closed: tr("zamknięte") };
  const PRIORITY = { low: tr("niski"), normal: tr("normalny"), high: tr("wysoki"), critical: tr("krytyczny") };
  const REQUEST_STATUS = { pending: tr("czeka na decyzję"), pending_customer_confirmation: tr("czeka na drugą osobę"), approved: tr("zatwierdzona"),
    rejected: tr("odrzucona"), cancelled: tr("anulowana"), expired: tr("wygasła"), pending_second_approval: tr("procedura awaryjna") };

  // Zgloszenia do supportu Forvium: lista, nowe zgloszenie, rozmowa, zamkniecie.
  function viewTickets(org, content) {
    return guarded(content, async () => {
      const { tickets, can_create: canCreate } = await api(`/api/app/orgs/${org.id}/tickets`);
      const msg = el("p");
      const form = el("form", { onsubmit: async (e) => {
        e.preventDefault();
        try {
          const r = await api(`/api/app/orgs/${org.id}/tickets`, { method: "POST", body: Object.fromEntries(new FormData(form)) });
          viewTicket(org, content, r.ticket.id);
        } catch (err) { msg.className = "error"; msg.textContent = err.message; }
      } },
        el("label", {}, tr("Temat")), el("input", { name: "subject", required: true, minlength: 3, maxlength: 300 }),
        el("label", {}, tr("Opis problemu")), el("textarea", { name: "description", required: true, minlength: 10, rows: 5 }),
        el("label", {}, tr("Priorytet")), el("select", { name: "priority" },
          ...Object.entries(PRIORITY).map(([v, l]) => el("option", { value: v, selected: v === "normal" }, l))),
        el("p", { class: "muted" }, tr("Jeśli support będzie potrzebował wglądu w Twoje dane, poprosi o zgodę na dostęp tylko do odczytu, przypiętą do tego zgłoszenia.")),
        msg, el("button", { type: "submit" }, tr("Wyślij zgłoszenie")));
      content.replaceChildren(
        card(el("h2", {}, tr("Zgłoszenia do supportu Forvium")), el("table", {},
          el("tr", {}, ...[tr("Numer"), tr("Temat"), tr("Priorytet"), tr("Status"), tr("Zgłosił(a)"), tr("Aktualizacja"), ""].map((t) => el("th", {}, t))),
          ...tickets.map((t) => el("tr", {}, el("td", {}, t.number), el("td", {}, t.subject), el("td", {}, PRIORITY[t.priority] || t.priority),
            el("td", {}, el("span", { class: "pill" }, TICKET_STATUS[t.status] || t.status)), el("td", {}, t.reporter_email || "Forvium"),
            el("td", {}, fmt(t.updated_at)),
            el("td", {}, el("button", { class: "secondary", onclick: () => viewTicket(org, content, t.id) }, tr("Otwórz"))))))),
        canCreate ? card(el("h3", {}, tr("Nowe zgłoszenie")), form) : "");
    });
  }

  function viewTicket(org, content, ticketId) {
    return guarded(content, async () => {
      const d = await api(`/api/app/orgs/${org.id}/tickets/${ticketId}`);
      const t = d.ticket;
      const reply = el("form", { onsubmit: async (e) => {
        e.preventDefault();
        try {
          await api(`/api/app/orgs/${org.id}/tickets/${t.id}/messages`, { method: "POST", body: Object.fromEntries(new FormData(reply)) });
          viewTicket(org, content, t.id);
        } catch (err) { alert(err.message); }
      } }, el("label", {}, tr("Odpowiedź")), el("textarea", { name: "body", required: true, rows: 3 }),
        el("div", { class: "row" }, el("button", { type: "submit" }, tr("Wyślij")),
          el("button", { type: "button", class: "secondary", onclick: async () => {
            if (!confirm(tr("Zamknąć {ticket}? Trwające sesje wsparcia oparte na tym zgłoszeniu zostaną zakończone.", { ticket: t.number }))) return;
            await api(`/api/app/orgs/${org.id}/tickets/${t.id}/close`, { method: "POST" }).catch((e) => alert(e.message));
            viewTicket(org, content, t.id);
          } }, tr("Zamknij zgłoszenie"))));
      content.replaceChildren(
        card(el("a", { onclick: () => viewTickets(org, content) }, tr("← Zgłoszenia")),
          el("h2", {}, t.number, " · ", t.subject),
          el("p", { class: "muted" }, tr("Priorytet: "), PRIORITY[t.priority] || t.priority, tr(" · status: "), TICKET_STATUS[t.status] || t.status,
            tr(" · zgłosił(a): "), t.reporter_email || "Forvium", " · ", fmt(t.created_at)),
          t.description ? el("p", { class: "pre" }, t.description) : ""),
        card(el("h3", {}, tr("Rozmowa")), d.messages.length ? el("div", {}, ...d.messages.map((m) => el("div", { class: "msg " + m.author_side },
          el("div", { class: "muted" }, m.author_side === "forvium" ? tr("Support Forvium") : m.author_email, " · ", fmt(m.created_at)),
          el("p", { class: "pre" }, m.body)))) : el("p", { class: "muted" }, tr("Brak wiadomości.")),
          d.can_reply ? reply : ""),
        card(el("h3", {}, tr("Dostęp serwisowy w tym zgłoszeniu")), d.access_requests.length ? el("table", {},
          el("tr", {}, ...[tr("Data"), tr("Operator"), tr("Zakres"), tr("Status")].map((x) => el("th", {}, x))),
          ...d.access_requests.map((a) => el("tr", {}, el("td", {}, fmt(a.created_at)), el("td", {}, a.operator_email || "—"),
            el("td", {}, (a.scopes || []).join(", ")), el("td", {}, REQUEST_STATUS[a.status] || a.status))))
          : el("p", { class: "muted" }, tr("Forvium nie prosiło o dostęp w ramach tego zgłoszenia."))));
    });
  }

  // Czlonkowie organizacji i zaproszenia (nowa osoba aktywuje konto linkiem z e-maila).
  function viewMembers(org, content) {
    return guarded(content, async () => {
      const { members } = await api(`/api/app/orgs/${org.id}/members`);
      const manage = org.role === "owner" || org.role === "admin";
      const msg = el("p");
      const form = el("form", { onsubmit: async (e) => {
        e.preventDefault();
        const f = Object.fromEntries(new FormData(form));
        try {
          const r = await api(`/api/app/orgs/${org.id}/members`, { method: "POST", body: f });
          msg.className = "";
          msg.textContent = r.member.state === "pending_activation"
            ? tr("Wysłano zaproszenie na {email}. Link aktywacyjny jest ważny 72 godziny.", { email: r.member.email })
            : tr("Dodano {email} do organizacji.", { email: r.member.email });
          viewMembers(org, content);
        } catch (err) { msg.className = "error"; msg.textContent = err.message; }
      } },
        el("label", {}, tr("E-mail")), el("input", { name: "email", type: "email", required: true }),
        el("label", {}, tr("Imię i nazwisko")), el("input", { name: "display_name", required: true, minlength: 2 }),
        el("label", {}, tr("Rola")), el("select", { name: "role" },
          ...["member", "viewer", "admin", ...(org.role === "owner" ? ["owner"] : [])].map((r) => el("option", { value: r }, ORG_ROLE_LABELS[r]))),
        msg, el("button", { type: "submit" }, tr("Zaproś")));
      content.replaceChildren(
        card(el("h2", {}, tr("Członkowie")), el("table", {},
          el("tr", {}, ...[tr("E-mail"), tr("Nazwa"), tr("Rola"), tr("Konto"), ""].map((t) => el("th", {}, t))),
          ...members.map((m) => el("tr", {}, el("td", {}, m.email), el("td", {}, m.display_name),
            el("td", {}, ORG_ROLE_LABELS[m.role] || m.role), el("td", {}, STATE_LABELS[m.state] || m.state || "—"),
            el("td", {}, manage && m.state === "active" && m.user_id !== currentUserId ? el("button", { class: "secondary", onclick: async () => {
              if (!confirm(tr("Zresetować dostęp {email}? Hasło i aplikacja uwierzytelniająca tej osoby przestaną działać, a na jej adres wyślemy nowy link aktywacyjny.", { email: m.email }))) return;
              const code = askMfa(tr("Reset dostępu ") + m.email + ".");
              if (code === null) return;
              try {
                await api(`/api/app/orgs/${org.id}/members/${m.user_id}/reset-access`, { method: "POST", body: { mfa_code: code } });
                viewMembers(org, content);
              } catch (err) { alert(err.message); }
            } }, tr("Resetuj dostęp")) : ""))))),
        manage ? card(el("h3", {}, tr("Zaproś osobę")),
          el("p", { class: "muted" }, tr("Nowa osoba dostanie e-mail z linkiem, ustawi hasło i aplikację uwierzytelniającą. Konta pracowników Forvium nie da się dodać.")),
          form) : "");
    });
  }

  function viewDashboard(org, content) {
    return guarded(content, async () => {
      const d = await api(`/api/app/orgs/${org.id}/dashboard`);
      const tiles = [[tr("Jednostki"), d.units], [tr("Technologie"), d.technologies]];
      if (d.cves) tiles.push(["CVE", d.cves.total], [tr("Krytyczne"), d.cves.critical], [tr("Wysokie"), d.cves.high]);
      content.replaceChildren(card(el("h2", {}, tr("Dashboard")),
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
        card(el("h3", {}, tr("Stan konfiguracji")),
          el("p", {}, tr("SMTP skonfigurowany: "), cfg.smtp_configured ? tr("tak") : tr("nie")),
          el("p", {}, tr("Webhooki: "), cfg.webhooks_count, tr(" · Sekrety: "), cfg.secrets_count, tr(" · Plan: "), cfg.subscription_plan)),
        card(el("h3", {}, tr("Błędy")), el("table", {},
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
          (c.unit_ids ? tr(" · jednostki: ") + c.unit_ids.map((id) => unitName[id] || id).join(", ") : "");
        const basis = { customer: c.second_approver_user_id ? tr("decyzja klienta (2 osoby)") : tr("decyzja klienta"),
          standing: tr("zgoda stała"), break_glass: el("span", { class: "danger-text" }, "BREAK GLASS") }[c.basis] || c.basis;
        return el("tr", {}, el("td", {}, r.ticket_number), el("td", {}, r.operator_id), el("td", {}, basis), el("td", {}, scopeText),
          el("td", {}, fmt(c.valid_until)), el("td", {}, c.revoked_at ? tr("cofnięta ") + fmt(c.revoked_at) : active ? tr("aktywna") : tr("wygasła")),
          el("td", {}, active ? el("button", { class: "danger", onclick: async () => {
            await api(`/api/app/orgs/${org.id}/support-access/consents/${c.id}/revoke`, { method: "POST" }).catch((e) => alert(e.message));
            reload();
          } }, tr("Cofnij zgodę")) : ""));
      });

      const panel = el("div");
      const sessionRows = h.sessions.map((s) => el("tr", {},
        el("td", {}, fmt(s.started_at)), el("td", {}, s.operator_id), el("td", {}, s.ticket_number),
        el("td", {}, el("span", { class: "pill" }, s.status), s.extensions_count ? " " + tr("(przedłużona {n}x)", { n: s.extensions_count }) : ""),
        el("td", {}, fmt(s.ended_at || s.expires_at)),
        el("td", { class: "row" },
          s.status === "active" ? el("button", { onclick: () => livePanel(org, s, panel, reload) }, tr("Podgląd na żywo")) : "",
          el("button", { class: "secondary", onclick: () => replayPanel(org, s, panel) }, tr("Nagranie")),
          el("button", { class: "secondary", onclick: async () => {
            const a = await api(`/api/app/orgs/${org.id}/support-access/sessions/${s.id}/activity`);
            panel.replaceChildren(card(el("h3", {}, tr("Aktywność sesji "), s.id), el("table", {},
              ...a.events.map((e) => el("tr", {}, el("td", {}, fmt(e.occurred_at)), el("td", {}, e.action),
                el("td", {}, e.method || ""), el("td", {}, e.route || ""), el("td", {}, e.outcome))))));
          } }, tr("Aktywność")),
          s.status === "active" ? el("button", { class: "danger", onclick: async () => {
            await api(`/api/app/orgs/${org.id}/support-access/sessions/${s.id}/terminate`, { method: "POST" }).catch((e) => alert(e.message));
            reload();
          } }, tr("Zakończ")) : "")));

      content.replaceChildren(
        card(el("h2", {}, tr("Dostęp serwisowy Forvium")),
          el("p", { class: "muted" }, tr("Operator Forvium może zobaczyć Twoją organizację wyłącznie w trybie tylko do odczytu, w zakresie i czasie, które zatwierdzisz. Trwającą sesję możesz oglądać na żywo i przerwać w każdej chwili."))),
        settingsCard(org, settings, reload),
        ...(decisionCards.length ? decisionCards : [el("div", { class: "card muted" }, tr("Brak oczekujących próśb."))]),
        card(el("h3", {}, tr("Zgody")), el("table", {},
          el("tr", {}, ...[tr("Zgłoszenie"), tr("Operator"), tr("Podstawa"), tr("Zakres"), tr("Ważna do"), tr("Status"), ""].map((t) => el("th", {}, t))), ...consentRows)),
        standingSection(org, h.standing_consents || [], units, reload, settings.dual_approval),
        card(el("h3", {}, tr("Historia sesji")), el("table", {},
          el("tr", {}, ...[tr("Start"), tr("Operator"), tr("Zgłoszenie"), tr("Status"), tr("Koniec"), ""].map((t) => el("th", {}, t))), ...sessionRows)),
        reportsCard(org),
        panel);
    });
  }

  // Pobranie pliku z API (naglowek Authorization, wiec nie zwykly link).
  async function download(path, fallbackName) {
    const r = await fetch(API + path, { headers: { Authorization: "Bearer " + token() } });
    if (!r.ok) throw new Error(tr("Nie udało się pobrać pliku (") + r.status + ")");
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
    const body = el("div", {}, el("p", { class: "muted" }, tr("Ładowanie…")));
    const load = async () => {
      try {
        const { reports } = await api(`/api/app/orgs/${org.id}/access-reports`);
        body.replaceChildren(reports.length ? el("table", {},
          el("tr", {}, ...[tr("Okres"), tr("Utworzono"), "SHA-256", ""].map((t) => el("th", {}, t))),
          ...reports.map((r) => el("tr", {}, el("td", {}, r.period_label), el("td", {}, fmt(r.created_at)),
            el("td", { class: "mono", title: r.sha256 }, r.sha256.slice(0, 16) + "…"),
            el("td", {}, el("button", { class: "secondary", onclick: () => download(
              `/api/app/orgs/${org.id}/access-reports/${r.id}/pdf`, `raport-${r.period_start}.pdf`).catch((e) => alert(e.message)) }, tr("Pobierz PDF"))))))
          : el("p", { class: "muted" }, tr("Pierwszy raport pojawi się po zakończeniu miesiąca.")));
      } catch (e) { body.replaceChildren(el("p", { class: "error" }, e.message)); }
    };
    const month = el("input", { type: "month" });
    load();
    return card(el("h3", {}, tr("Raporty dostępu")),
      el("p", { class: "muted" }, tr("Co miesiąc: wszystkie prośby Forvium o dostęp, decyzje, sesje wsparcia (czas, zakres, oglądane widoki, zablokowane próby) i zmiany zgód. Skrót SHA-256 pozwala sprawdzić, że plik nie został zmieniony.")),
      body,
      el("div", { class: "row" }, month, el("button", { class: "secondary", onclick: async () => {
        if (!month.value) return;
        const [year, m] = month.value.split("-").map(Number);
        try {
          await api(`/api/app/orgs/${org.id}/access-reports`, { method: "POST", body: { year, month: m } });
          load();
        } catch (e) { alert(e.message); }
      } }, tr("Utwórz raport za wybrany miesiąc"))));
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
    const note = el("input", { placeholder: tr("Notatka (opcjonalnie)") });
    return el("div", { class: "card" + (confirming ? " highlight" : "") },
      el("h3", {}, confirming ? tr("Potwierdź dostęp (druga osoba) · ") : tr("Prośba o dostęp · "), r.ticket_number),
      confirming ? el("p", { class: "danger-text" }, tr("Pierwsze zatwierdzenie: "), r.first_approved_by_user_id, tr(". Twoja organizacja wymaga drugiej osoby - możesz tylko potwierdzić lub zawęzić zakres.")) : "",
      el("p", {}, tr("Operator Forvium: "), r.operator_id),
      el("p", {}, tr("Powód: "), r.reason),
      el("p", {}, tr("Tryb: "), el("span", { class: "pill" }, r.access_level), tr(" · Czas sesji: "), r.duration_minutes, " min"),
      el("label", {}, tr("Zakres zgody")), ...scopes,
      ...(unitBoxes.length ? [el("label", {}, tr("Ogranicz do jednostek (brak zaznaczenia = wszystkie dozwolone)")), ...unitBoxes] : []),
      el("label", {}, tr("Zgoda ważna (godziny)")), hours,
      el("label", {}, tr("Notatka")), note,
      el("div", { class: "row spaced" },
        el("button", { onclick: async () => {
          const unitIds = checkedValues(unitBoxes);
          try {
            const res = await api(`/api/app/orgs/${org.id}/support-access/requests/${r.id}/approve`, { method: "POST",
              body: { scopes: checkedValues(scopes), unit_ids: unitIds.length ? unitIds : null,
                      valid_hours: Number(hours.value), note: note.value } });
            if (res.status === "pending_customer_confirmation") alert(tr("Zapisano. Dostęp zacznie obowiązywać po potwierdzeniu przez drugą osobę."));
          } catch (e) { alert(e.message); }
          reload();
        } }, confirming ? tr("Potwierdź") : tr("Zatwierdź")),
        el("button", { class: "danger", onclick: async () => {
          await api(`/api/app/orgs/${org.id}/support-access/requests/${r.id}/reject`, { method: "POST", body: { note: note.value } }).catch((e) => alert(e.message));
          reload();
        } }, tr("Odrzuć"))));
  }

  function settingsCard(org, settings, reload) {
    const put = async (enabled) => {
      const code = askMfa(enabled ? tr("Włączenie zatwierdzania przez dwie osoby.") : tr("Wyłączenie zatwierdzania przez dwie osoby."));
      if (code === null) return;
      await api(`/api/app/orgs/${org.id}/support-access/settings`, { method: "PUT", body: { dual_approval: enabled, mfa_code: code } })
        .catch((e) => alert(e.message));
      reload();
    };
    return card(el("h3", {}, tr("Zatwierdzanie przez dwie osoby")),
      el("p", { class: "muted" }, tr("Gdy włączone, każdy dostęp serwisowy (i każda zgoda stała) wymaga zatwierdzenia przez dwie różne osoby z Twojej organizacji. Wyłączenie też wymaga drugiej osoby.")),
      el("p", {}, tr("Status: "), el("strong", {}, settings.dual_approval ? tr("włączone") : tr("wyłączone")),
        settings.dual_approval_disable_requested_by ? el("span", { class: "danger-text" }, tr(" · zgłoszono wyłączenie ("), settings.dual_approval_disable_requested_by, tr(") - czeka na drugą osobę")) : ""),
      settings.dual_approval
        ? el("button", { class: "secondary", onclick: () => put(false) }, settings.dual_approval_disable_requested_by ? tr("Potwierdź wyłączenie") : tr("Wyłącz"))
        : el("button", { onclick: () => put(true) }, tr("Włącz")));
  }

  // ---------------------------------------------------- podglad na zywo / nagranie
  function livePanel(org, s, panel, reload) {
    const frame = snapshotFrame();
    const status = el("p", { class: "muted" }, tr("Łączenie…"));
    const feed = el("table");
    let latest = 0;
    let timer;
    const poll = async () => {
      if (!panel.contains(frame)) return clearInterval(timer);
      try {
        const live = await api(`/api/app/orgs/${org.id}/support-access/sessions/${s.id}/live?after=${latest}`);
        if (live.snapshot) { frame.show(live.snapshot.html); latest = live.snapshot.seq; }
        status.textContent = live.active
          ? tr("Operator {operator} ogląda teraz: {view} · pozostało {minutes} min", { operator: live.operator_id, view: live.current_view ? tr(live.current_view) : "—", minutes: Math.ceil(live.remaining_seconds / 60) })
          : tr("Sesja zakończona.");
        feed.replaceChildren(...live.activity.map((e) => el("tr", {}, el("td", {}, fmt(e.occurred_at)),
          el("td", {}, e.method, " ", e.route), el("td", {}, el("span", { class: "pill" }, e.outcome)))));
        if (!live.active) clearInterval(timer);
      } catch (e) { status.textContent = e.message; }
    };
    panel.replaceChildren(card(
      el("h3", {}, tr("Podgląd na żywo · sesja "), s.ticket_number),
      status,
      el("div", { class: "row" }, el("button", { class: "danger", onclick: async () => {
        await api(`/api/app/orgs/${org.id}/support-access/sessions/${s.id}/terminate`, { method: "POST" }).catch((e) => alert(e.message));
        clearInterval(timer);
        reload();
      } }, tr("Przerwij sesję"))),
      frame,
      el("h3", { class: "spaced" }, tr("Ostatnie operacje operatora")), feed));
    poll();
    timer = setInterval(poll, 2000);
  }

  async function replayPanel(org, s, panel) {
    const base = `/api/app/orgs/${org.id}/support-access/sessions/${s.id}/recording`;
    const { frames } = await api(base);
    if (!frames.length) return panel.replaceChildren(card(el("p", { class: "muted" }, tr("Brak nagrania tej sesji."))));
    const frame = snapshotFrame();
    const caption = el("p", { class: "muted" });
    const slider = el("input", { type: "range", min: 1, max: frames.length, value: 1, class: "slider" });
    const load = async () => {
      const f = frames[Number(slider.value) - 1];
      const data = await api(`${base}/${f.seq}`);
      frame.show(data.html);
      caption.textContent = tr("Klatka {n}/{total} · {at} · widok: {view}", { n: slider.value, total: frames.length, at: fmt(f.captured_at), view: tr(f.view) });
    };
    slider.oninput = load;
    panel.replaceChildren(card(el("h3", {}, tr("Nagranie sesji · "), s.ticket_number), caption, slider, frame));
    load();
  }

  // ------------------------------------------------------ zgody stale (klient)
  const ROLE_LABELS = { support_l1: tr("Support L1"), support_l2: tr("Support L2"), support_lead: tr("Kierownik supportu") };

  function standingSection(org, standing, units, reload, dual) {
    const rows = standing.map((st) => el("tr", {},
      el("td", {}, st.scopes.map((x) => SCOPE_LABELS[x] || x).join(", ")),
      el("td", {}, st.max_session_minutes, " min"),
      el("td", {}, st.allowed_platform_roles ? st.allowed_platform_roles.map((r) => ROLE_LABELS[r] || r).join(", ") : tr("każda")),
      el("td", {}, fmt(st.valid_until)),
      el("td", {}, st.revoked_at ? tr("cofnięta") : st.pending_confirmation ? tr("czeka na drugą osobę") : st.active ? tr("aktywna") : tr("wygasła")),
      el("td", { class: "row" },
        st.pending_confirmation ? el("button", { onclick: async () => {
          const code = askMfa(tr("Potwierdzenie zgody stałej."));
          if (code === null) return;
          await api(`/api/app/orgs/${org.id}/support-access/standing-consents/${st.id}/confirm`, { method: "POST", body: { mfa_code: code } })
            .catch((e) => alert(e.message));
          reload();
        } }, tr("Potwierdź")) : "",
        st.active || st.pending_confirmation ? el("button", { class: "danger", onclick: async () => {
          await api(`/api/app/orgs/${org.id}/support-access/standing-consents/${st.id}/revoke`, { method: "POST" }).catch((e) => alert(e.message));
          reload();
        } }, tr("Cofnij")) : "")));
    const box = (value, label, checked = false) => el("label", {}, el("input", { type: "checkbox", value, checked }), " ", label);
    const scopeBoxes = Object.entries(SCOPE_LABELS).map(([k, l]) => box(k, l, k === "dashboard" || k === "diagnostics"));
    const roleBoxes = Object.entries(ROLE_LABELS).map(([k, l]) => box(k, l));
    const unitBoxes = units.map((u) => box(u.id, u.name));
    const minutes = el("input", { type: "number", min: 1, max: 15, value: 15 });
    const days = el("input", { type: "number", min: 1, max: 365, value: 90 });
    const note = el("input", { placeholder: tr("Notatka (opcjonalnie)") });
    const mfa = el("input", { inputmode: "numeric", autocomplete: "one-time-code", placeholder: tr("Kod MFA") });
    const msg = el("p", { class: "error" });
    return card(
      el("h3", {}, tr("Zgody stałe")),
      el("p", { class: "muted" }, tr("Zgoda stała pozwala supportowi Forvium otwierać sesje tylko do odczytu bez każdorazowego pytania - w granicach poniżej. O każdym takim dostępie dostaniesz powiadomienie, a zgodę można cofnąć w każdej chwili (kończy to też trwające sesje)."),
        dual ? tr(" Przy zatwierdzaniu przez dwie osoby nowa zgoda stała zacznie działać po potwierdzeniu przez drugą osobę.") : ""),
      el("table", {}, el("tr", {}, ...[tr("Zakres"), tr("Sesja do"), tr("Role supportu"), tr("Ważna do"), tr("Status"), ""].map((t) => el("th", {}, t))), ...rows),
      el("details", { class: "spaced" }, el("summary", {}, tr("Dodaj zgodę stałą")),
        el("label", {}, tr("Zakres")), ...scopeBoxes,
        ...(unitBoxes.length ? [el("label", {}, tr("Ogranicz do jednostek (brak zaznaczenia = wszystkie)")), ...unitBoxes] : []),
        el("label", {}, tr("Tylko dla ról supportu (brak zaznaczenia = każda)")), ...roleBoxes,
        el("label", {}, tr("Maksymalny czas sesji (min)")), minutes,
        el("label", {}, tr("Ważna przez (dni)")), days,
        el("label", {}, tr("Notatka")), note,
        el("label", {}, tr("Potwierdź kodem MFA")), mfa, msg,
        el("button", { onclick: async () => {
          try {
            const roles = checkedValues(roleBoxes), unitIds = checkedValues(unitBoxes);
            await api(`/api/app/orgs/${org.id}/support-access/standing-consents`, { method: "POST", body: {
              scopes: checkedValues(scopeBoxes), unit_ids: unitIds.length ? unitIds : null,
              allowed_platform_roles: roles.length ? roles : null, max_session_minutes: Number(minutes.value),
              valid_days: Number(days.value), note: note.value, mfa_code: mfa.value } });
            reload();
          } catch (e) { msg.textContent = e.message; }
        } }, tr("Udziel zgody stałej"))));
  }

  // ---------------------------------------------------------- powiadomienia
  async function viewNotifications(content) {
    const { notifications } = await api("/api/app/notifications");
    content.replaceChildren(card(el("h2", {}, tr("Powiadomienia"))),
      ...(notifications.length ? notifications.map((n) => card(el("h3", {}, n.title),
        el("p", { class: "muted" }, fmt(n.created_at)), el("pre", { class: "body" }, n.body)))
        : [el("div", { class: "card muted" }, tr("Brak powiadomień."))]));
  }

  if (supportToken) startSupportMode().catch(() => supportEnded());
  else renderHome();
})();
