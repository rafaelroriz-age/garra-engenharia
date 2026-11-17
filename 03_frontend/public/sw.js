/* Service Worker da PWA — DEC-26 / ADR-03 / ADR-15.
 * Online-first: cacheia SOMENTE leitura de baixa volatilidade. Não-GET nunca é
 * interceptado (falha com o erro nativo de rede, sem fila local).
 * As regras abaixo duplicam lib/sw-cache.ts (fonte testada em sw-cache.test.ts,
 * que confere a igualdade dos padrões). Altere os dois juntos.
 */
const CACHE_VERSION = "v2"; // v2: OFFLINE_URL relativo ao scope (T83)
const CACHE_PREFIX = "garra-sw-";
const DATA_CACHE = CACHE_PREFIX + "data-" + CACHE_VERSION;
const SHELL_CACHE = CACHE_PREFIX + "shell-" + CACHE_VERSION;
// Relativo ao scope: no Pages o app vive em /garra-engenharia/ (registro em sw-register.tsx).
const OFFLINE_URL = new URL("offline.html", self.registration.scope).href;
const STORED_AT_HEADER = "x-sw-stored-at";

const RULES = [
  { pattern: "^/api/v1/sistemas-prediais/?$", ttlMs: 86400000, perUser: false },
  { pattern: "^/api/v1/gabarito/(tipos-anomalia|tipos-falha|localizacoes)/?$", ttlMs: 86400000, perUser: false },
  { pattern: "^/api/v1/contratos/?$", ttlMs: 300000, perUser: true },
  { pattern: "^/api/v1/contratos/[0-9]+/?$", ttlMs: 300000, perUser: true },
];
// DEC-57: api.json/snapshot.enc da branch `snapshot` nunca passam pelo SW.
const NEVER_HOSTS = [{ host: "raw.githubusercontent.com" }];
const NEVER = [
  { never: "/auth(/|$)" },
  { never: "/portal(/|$)" },
  { never: "/fotos?(/|$)" },
  { never: "/download" },
  { never: "/relatorios?(/|$)" },
  { never: "/documentos?(/|$)" },
  { never: "/upload" },
];

function matchRule(request) {
  if (request.method !== "GET") return null;
  const url = new URL(request.url);
  if (url.protocol !== "http:" && url.protocol !== "https:") return null;
  if (NEVER.some((n) => new RegExp(n.never).test(url.pathname))) return null;
  return RULES.find((r) => new RegExp(r.pattern).test(url.pathname)) || null;
}

async function fingerprint(request) {
  const auth = request.headers.get("Authorization");
  if (!auth) return null;
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(auth));
  return Array.from(new Uint8Array(buf).slice(0, 8))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

async function keyFor(rule, request) {
  if (!rule.perUser) return request.url;
  const fp = await fingerprint(request);
  if (!fp) return null;
  const u = new URL(request.url);
  u.searchParams.set("__sw_u", fp);
  return u.toString();
}

function cacheable(response) {
  if (response.status !== 200) return false;
  return !/\b(no-store|private)\b/i.test(response.headers.get("Cache-Control") || "");
}

async function store(cache, key, response) {
  const headers = new Headers(response.headers);
  headers.set(STORED_AT_HEADER, String(Date.now()));
  const body = await response.blob();
  await cache.put(key, new Response(body, { status: 200, statusText: response.statusText, headers }));
}

async function staleWhileRevalidate(event, rule) {
  const request = event.request;
  const key = await keyFor(rule, request);
  if (key === null) return fetch(request);
  const cache = await caches.open(DATA_CACHE);
  const cached = await cache.match(key);
  const storedAt = cached ? Number(cached.headers.get(STORED_AT_HEADER)) : 0;
  const fresh = cached && Date.now() - storedAt >= 0 && Date.now() - storedAt < rule.ttlMs;

  const network = fetch(request).then(async (response) => {
    if (cacheable(response)) await store(cache, key, response.clone());
    else if (response.status === 401 || response.status === 403) await cache.delete(key);
    return response;
  });

  if (fresh) {
    event.waitUntil(network.catch(() => undefined));
    return cached;
  }
  // Vencido ou ausente: rede primeiro; cache expirado nunca é servido.
  return network;
}

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(SHELL_CACHE).then((c) => c.add(OFFLINE_URL)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((names) =>
        Promise.all(
          names
            .filter((n) => n.startsWith(CACHE_PREFIX) && n !== DATA_CACHE && n !== SHELL_CACHE)
            .map((n) => caches.delete(n)),
        ),
      )
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("message", (event) => {
  if (event.data && event.data.type === "CLEAR_DATA_CACHE") {
    event.waitUntil(caches.delete(DATA_CACHE));
  }
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") return; // escritas: não interceptar.
  const host = new URL(request.url).hostname;
  if (NEVER_HOSTS.some((n) => n.host === host)) return; // descoberta/snapshot: sempre rede.

  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request).catch(async () => {
        const cache = await caches.open(SHELL_CACHE);
        return (await cache.match(OFFLINE_URL)) || Response.error();
      }),
    );
    return;
  }

  const rule = matchRule(request);
  if (rule) event.respondWith(staleWhileRevalidate(event, rule));
});
