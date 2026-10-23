// Adres wspolnego backendu FastAPI. Mozna nadpisac, ustawiajac window.FORVIUM_API przed tym skryptem.
// Na *.forvium.com -> https://api.forvium.com, lokalnie -> http://localhost:8000.
window.FORVIUM_API = window.FORVIUM_API ||
  (location.hostname === "forvium.com" || location.hostname.endsWith(".forvium.com")
    ? "https://api.forvium.com"
    : `${location.protocol}//${location.hostname}:8000`);
