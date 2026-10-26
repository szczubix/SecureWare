// Aktywacja konta: uzytkownik sam ustawia haslo i aplikacje uwierzytelniajaca.
// Token jest we fragmencie URL (nie trafia do logow serwera) i znika z paska adresu.
(async () => {
  const { t: tr, fmtDate, header: LANG_HEADER } = window.FW_I18N;
  const PANEL = "app";
  const token = new URLSearchParams(location.hash.slice(1)).get("token");
  history.replaceState(null, "", location.pathname);  // bez tokenu i ?lang= (jezyk zapamietany w i18n.js)
  const root = document.getElementById("root");
  const el = (tag, attrs = {}, ...children) => {
    const node = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (k.startsWith("on")) node[k] = v;
      else if (v !== false && v != null) node.setAttribute(k, v === true ? "" : v);
    }
    for (const c of children.flat()) node.append(c instanceof Node ? c : document.createTextNode(String(c ?? "")));
    return node;
  };
  const call = async (path, body) => {
    const r = await fetch(window.FORVIUM_API + "/api/" + PANEL + path, {
      method: "POST", headers: { "Content-Type": "application/json", ...LANG_HEADER }, body: JSON.stringify(body),
    });
    const data = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(data.message || tr("Błąd ") + r.status);
    return data;
  };
  const fail = (text) => root.replaceChildren(el("div", { class: "card" }, el("p", { class: "error" }, text)));
  if (!token) return fail(tr("Brak tokenu aktywacyjnego w linku."));

  let info;
  try { info = await call("/activation/info", { token }); } catch (e) { return fail(e.message); }
  const msg = el("p", { class: "error" });
  const form = el("form", { class: "card", onsubmit: async (ev) => {
    ev.preventDefault();
    const f = Object.fromEntries(new FormData(form));
    if (f.password !== f.password2) { msg.textContent = tr("Hasła nie są takie same."); return; }
    try {
      await call("/activation/complete", { token, password: f.password, mfa_code: f.mfa_code.trim() });
      root.replaceChildren(el("div", { class: "card" }, el("h2", {}, tr("Konto aktywne")),
        el("p", {}, tr("Możesz się zalogować hasłem i kodem z aplikacji uwierzytelniającej.")),
        el("a", { href: "index.html" }, tr("Przejdź do logowania"))));
    } catch (e) { msg.textContent = e.message; }
  } },
    el("h2", {}, tr("Aktywacja konta")),
    el("p", {}, info.display_name, " · ", el("strong", {}, info.email)),
    el("label", {}, tr("Hasło (min. {n} znaków)", { n: info.min_password_length })),
    el("p", { class: "muted" }, tr("Najlepsza jest długa fraza z kilku słów. Hasło nie może pochodzić ze znanych wycieków ani zawierać Twojego adresu e-mail lub imienia.")),
    el("input", { name: "password", type: "password", required: true, minlength: info.min_password_length, autocomplete: "new-password" }),
    el("label", {}, tr("Powtórz hasło")),
    el("input", { name: "password2", type: "password", required: true, autocomplete: "new-password" }),
    el("h3", {}, tr("Aplikacja uwierzytelniająca (MFA)")),
    el("p", { class: "muted" }, tr("Dodaj konto w aplikacji (np. Google Authenticator, Microsoft Authenticator, Aegis): otwórz link na telefonie albo wpisz klucz ręcznie.")),
    el("p", {}, el("a", { href: info.otpauth_uri }, tr("Dodaj do aplikacji uwierzytelniającej"))),
    el("p", {}, tr("Klucz: "), el("code", { class: "mono" }, info.mfa_secret.match(/.{1,4}/g).join(" "))),
    el("label", {}, tr("Kod z aplikacji")),
    el("input", { name: "mfa_code", required: true, inputmode: "numeric", autocomplete: "one-time-code", pattern: "[0-9 ]{6,7}" }),
    el("p", { class: "muted" }, tr("Link jest jednorazowy i ważny do {until}.", { until: fmtDate(info.expires_at) })),
    msg,
    el("button", { type: "submit" }, tr("Aktywuj konto")));
  root.replaceChildren(form);
})();
