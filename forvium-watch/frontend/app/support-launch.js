// Jednorazowy kod przychodzi we fragmencie URL (nie trafia do logow serwera).
// Usuwamy go z paska adresu przed wymiana.
(async () => {
  const code = new URLSearchParams(location.hash.slice(1)).get("code");
  history.replaceState(null, "", location.pathname);
  const msg = document.getElementById("msg");
  if (!code) { msg.textContent = "Brak kodu uruchomienia."; return; }
  try {
    const r = await fetch(window.FORVIUM_API + "/api/app/support/launch", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ code }),
    });
    if (!r.ok) throw new Error((await r.json()).message || "Blad");
    const data = await r.json();
    // Token wsparcia tylko w sessionStorage tej karty i pod osobnym kluczem -
    // nie nadpisuje sesji klienta i znika po zamknieciu karty.
    sessionStorage.setItem("fw_support_token", data.token);
    location.replace("index.html");
  } catch (e) {
    msg.textContent = "Nie udalo sie uruchomic sesji wsparcia: " + e.message;
  }
})();
