// Test obciazeniowy Forvium Watch (k6). Uruchomienie: deploy/loadtest/README.md
//
// Trzy rownolegle scenariusze o stalym tempie (arrival rate - liczba zadan/s nie spada,
// gdy serwer zwalnia, wiec widac prawdziwe opoznienia):
//   customers - klienci przegladaja panel (dashboard, CVE, jednostki, powiadomienia, zgloszenia)
//   support   - operator w sesji wsparcia (kazde zadanie: walidacja sesji + RLS + wpis audytu)
//   operators - panel admin (lista prosb, audyt)
// Tempo: RATE (zadania/s lacznie, podzial 70/15/15), czas: DURATION.
import http from "k6/http";
import { check } from "k6";

const T = JSON.parse(open(__ENV.TOKENS || "/data/tokens.json"));
const BASE = __ENV.BASE || "http://api:8000";
const RATE = Number(__ENV.RATE || 50);
const DURATION = __ENV.DURATION || "60s";

const scenario = (fn, share) => ({
  executor: "constant-arrival-rate", exec: fn, duration: DURATION, timeUnit: "1s",
  rate: Math.max(1, Math.round(RATE * share)), preAllocatedVUs: Math.max(5, Math.round(RATE * share)), maxVUs: 400,
});

export const options = {
  dns: { select: "roundRobin", ttl: "1m" },   // obie repliki API
  discardResponseBodies: true,
  scenarios: {
    customers: scenario("customers", 0.70),
    support: scenario("support", 0.15),
    operators: scenario("operators", 0.15),
  },
  thresholds: {
    http_req_failed: ["rate<0.01"],
    "http_req_duration{scenario:customers}": ["p(95)<300"],
    "http_req_duration{scenario:support}": ["p(95)<500"],
    "http_req_duration{scenario:operators}": ["p(95)<500"],
  },
  summaryTrendStats: ["avg", "med", "p(90)", "p(95)", "p(99)", "max"],
};

const pick = (arr) => arr[Math.floor(Math.random() * arr.length)];
const auth = (token) => ({ headers: { Authorization: "Bearer " + token } });

const CUSTOMER_PATHS = ["/dashboard", "/cves", "/units", "/technologies", "/errors", "/tickets", "/support-access"];

export function customers() {
  const c = pick(T.customers);
  const path = Math.random() < 0.15 ? "/api/app/notifications" : `/api/app/orgs/${c.org}${pick(CUSTOMER_PATHS)}`;
  const r = http.get(BASE + path, Object.assign(auth(c.token), { tags: { name: "app " + path.replace(c.org, "{org}") } }));
  check(r, { "200": (res) => res.status === 200 });
}

export function support() {
  const s = T.support;
  const path = pick(["/dashboard", "/cves", "/units", "/technologies"]);
  const r = http.get(`${BASE}/api/app/orgs/${s.org}${path}`, Object.assign(auth(s.token), { tags: { name: "support " + path } }));
  check(r, { "200": (res) => res.status === 200 });
}

export function operators() {
  const path = pick(["/api/admin/support-access/requests", "/api/admin/audit?limit=50", "/api/admin/me", "/api/admin/tickets/all"]);
  const r = http.get(BASE + path, Object.assign(auth(pick(T.operators)), { tags: { name: "admin " + path.split("?")[0] } }));
  check(r, { "200": (res) => res.status === 200 });
}
