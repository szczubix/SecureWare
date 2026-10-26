// Adres wspolnego backendu FastAPI. Mozna nadpisac, ustawiajac window.FORVIUM_API przed tym skryptem.
// app.<domena> / admin.<domena>  ->  api.<domena> (ten sam port i protokol), np. app.forvium.com -> api.forvium.com.
// Inaczej (lokalnie bez bramy): http://<host>:8000.
window.FORVIUM_API = window.FORVIUM_API || (/^(app|admin)\./.test(location.hostname)
  ? `${location.protocol}//${location.hostname.replace(/^(app|admin)\./, "api.")}${location.port ? ":" + location.port : ""}`
  : `${location.protocol}//${location.hostname}:8000`);
