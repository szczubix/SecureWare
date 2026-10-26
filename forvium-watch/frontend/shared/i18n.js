// Tlumaczenia paneli (pl - jezyk zrodlowy, en - slownik w i18n-en.js).
// Tekst zrodlowy jest kluczem: t("Zapisz") albo t("Dodano {email}.", { email }).
// Jezyk: ?lang= w adresie (link aktywacyjny z e-maila), wybor zapamietany w przegladarce,
// w koncu jezyk przegladarki. Wybor wysylany jest do API (Accept-Language), wiec komunikaty
// bledow wracaja w tym samym jezyku, a zalogowanemu uzytkownikowi zapisywany jest na koncie
// (powiadomienia i e-maile).
(() => {
  const KEY = "fw_lang";
  const LANGS = ["pl", "en"];
  const DICTS = { en: window.FW_DICT_EN || {} };
  const store = {
    get: () => { try { return localStorage.getItem(KEY); } catch (_) { return null; } },
    set: (v) => { try { localStorage.setItem(KEY, v); } catch (_) { /* tryb prywatny */ } },
  };
  const pick = (v) => (LANGS.includes(v) ? v : null);
  const fromUrl = pick(new URLSearchParams(location.search).get("lang"));
  if (fromUrl) store.set(fromUrl);
  const lang = fromUrl || pick(store.get()) || ((navigator.language || "").toLowerCase().startsWith("pl") ? "pl" : "en");
  document.documentElement.lang = lang;

  function t(text, params) {
    let out = (DICTS[lang] && DICTS[lang][text]) || text;
    if (params) out = out.replace(/\{(\w+)\}/g, (m, k) => (k in params ? String(params[k] ?? "") : m));
    return out;
  }

  const locale = lang === "en" ? "en-GB" : "pl-PL";
  const fmtDate = (iso) => (iso ? new Date(iso).toLocaleString(locale) : "—");

  // Przelacznik PL | EN. onPersist(lang) - zapis wyboru na koncie (gdy zalogowany).
  function switcher(onPersist) {
    const box = document.createElement("span");
    box.className = "lang-switch";
    for (const l of LANGS) {
      const b = document.createElement("button");
      b.type = "button";
      b.className = l === lang ? "active" : "secondary";
      b.textContent = l.toUpperCase();
      b.setAttribute("aria-pressed", String(l === lang));
      b.onclick = async () => {
        if (l === lang) return;
        store.set(l);
        try { if (onPersist) await onPersist(l); } catch (_) { /* wybor i tak zostaje w przegladarce */ }
        location.reload();
      };
      box.append(b);
    }
    return box;
  }

  // Teksty statyczne w HTML (tytul strony, elementy z atrybutem data-i18n).
  function translateStatic() {
    document.title = t(document.title);
    document.querySelectorAll("[data-i18n]").forEach((n) => { n.textContent = t(n.textContent.trim()); });
  }
  translateStatic();

  window.FW_I18N = { lang, t, fmtDate, locale, switcher, header: { "Accept-Language": lang } };
})();
