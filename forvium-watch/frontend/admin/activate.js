// Aktywacja konta: uzytkownik sam ustawia haslo i aplikacje uwierzytelniajaca.
// Token jest we fragmencie URL (nie trafia do logow serwera) i znika z paska adresu.
(async () => {
  const PANEL = "admin";
  const token = new URLSearchParams(location.hash.slice(1)).get("token");
  history.replaceState(null, "", location.pathname);
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
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
    });
    const data = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(data.message || "Błąd " + r.status);
    return data;
  };
  const fail = (text) => root.replaceChildren(el("div", { class: "card" }, el("p", { class: "error" }, text)));
  if (!token) return fail("Brak tokenu aktywacyjnego w linku.");

  let info;
  try { info = await call("/activation/info", { token }); } catch (e) { return fail(e.message); }
  const msg = el("p", { class: "error" });
  const form = el("form", { class: "card", onsubmit: async (ev) => {
    ev.preventDefault();
    const f = Object.fromEntries(new FormData(form));
    if (f.password !== f.password2) { msg.textContent = "Hasła nie są takie same."; return; }
    try {
      await call("/activation/complete", { token, password: f.password, mfa_code: f.mfa_code.trim() });
      root.replaceChildren(el("div", { class: "card" }, el("h2", {}, "Konto aktywne"),
        el("p", {}, "Możesz się zalogować hasłem i kodem z aplikacji uwierzytelniającej."),
        el("a", { href: "index.html" }, "Przejdź do logowania")));
    } catch (e) { msg.textContent = e.message; }
  } },
    el("h2", {}, "Aktywacja konta"),
    el("p", {}, info.display_name, " · ", el("strong", {}, info.email)),
    el("label", {}, "Hasło (min. ", info.min_password_length, " znaków)"),
    el("p", { class: "muted" }, "Najlepsza jest długa fraza z kilku słów. Hasło nie może pochodzić ze znanych wycieków ani zawierać Twojego adresu e-mail lub imienia."),
    el("input", { name: "password", type: "password", required: true, minlength: info.min_password_length, autocomplete: "new-password" }),
    el("label", {}, "Powtórz hasło"),
    el("input", { name: "password2", type: "password", required: true, autocomplete: "new-password" }),
    el("h3", {}, "Aplikacja uwierzytelniająca (MFA)"),
    el("p", { class: "muted" }, "Dodaj konto w aplikacji (np. Google Authenticator, Microsoft Authenticator, Aegis): otwórz link na telefonie albo wpisz klucz ręcznie."),
    el("p", {}, el("a", { href: info.otpauth_uri }, "Dodaj do aplikacji uwierzytelniającej")),
    el("p", {}, "Klucz: ", el("code", { class: "mono" }, info.mfa_secret.match(/.{1,4}/g).join(" "))),
    el("label", {}, "Kod z aplikacji"),
    el("input", { name: "mfa_code", required: true, inputmode: "numeric", autocomplete: "one-time-code", pattern: "[0-9 ]{6,7}" }),
    el("p", { class: "muted" }, "Link jest jednorazowy i ważny do ", new Date(info.expires_at).toLocaleString("pl-PL"), "."),
    msg,
    el("button", { type: "submit" }, "Aktywuj konto"));
  root.replaceChildren(form);
})();
