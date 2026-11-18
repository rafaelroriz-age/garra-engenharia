// Executa com `npm run test:unit` (node:test, sem dependências novas).
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";

import {
  ALLOWLIST,
  NEVER_CACHE_PATTERNS,
  NEVER_INTERCEPT_HOSTS,
  cacheKeyUrl,
  isCacheableRequest,
  isNeverIntercepted,
  isCacheableResponse,
  isFresh,
  isLogoutStorageEvent,
  matchCacheRule,
} from "./sw-cache.ts";

const API = "http://localhost:8000/api/v1";

test("GET nas rotas de dados mestre e contratos é cacheável", () => {
  for (const p of [
    "/sistemas-prediais",
    "/gabarito/tipos-anomalia",
    "/gabarito/tipos-falha",
    "/gabarito/localizacoes",
    "/contratos",
    "/contratos?status=em_andamento&page=1",
    "/contratos/12",
  ]) {
    assert.equal(isCacheableRequest({ method: "GET", url: API + p }), true, p);
  }
});

test("qualquer método diferente de GET nunca é cacheável", () => {
  for (const m of ["POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]) {
    assert.equal(isCacheableRequest({ method: m, url: `${API}/contratos` }), false, m);
  }
});

test("auth, portal, fotos, downloads e relatórios nunca são cacheáveis", () => {
  for (const p of [
    "/auth/me",
    "/portal/edificacoes",
    "/portal/documentos",
    "/fotos/3",
    "/visitas/3/fotos",
    "/inspecoes/3/relatorio/download",
    "/contratos/1/documentos",
  ]) {
    assert.equal(isCacheableRequest({ method: "GET", url: API + p }), false, p);
  }
});

test("rotas fora da allowlist e esquemas não-http não são cacheáveis", () => {
  for (const p of ["/inspecoes/1", "/dashboard/resumo", "/ocorrencias/9", "/edificacoes"]) {
    assert.equal(isCacheableRequest({ method: "GET", url: API + p }), false, p);
  }
  assert.equal(isCacheableRequest({ method: "GET", url: "chrome-extension://x/api/v1/contratos" }), false);
  assert.equal(isCacheableRequest({ method: "GET", url: "não é url" }), false);
});

test("contratos são por usuário (TTL curto); dados mestre não", () => {
  const c = matchCacheRule({ method: "GET", url: `${API}/contratos` });
  const m = matchCacheRule({ method: "GET", url: `${API}/sistemas-prediais` });
  assert.ok(c && m);
  assert.equal(c.perUser, true);
  assert.equal(m.perUser, false);
  assert.ok(c.ttlMs < m.ttlMs);
});

test("chave de cache de contratos exige token e isola usuários", () => {
  const c = matchCacheRule({ method: "GET", url: `${API}/contratos` })!;
  const m = matchCacheRule({ method: "GET", url: `${API}/sistemas-prediais` })!;
  assert.equal(cacheKeyUrl(c, `${API}/contratos`, null), null);
  const a = cacheKeyUrl(c, `${API}/contratos`, "aaa");
  const b = cacheKeyUrl(c, `${API}/contratos`, "bbb");
  assert.notEqual(a, b);
  assert.equal(cacheKeyUrl(m, `${API}/sistemas-prediais`, null), `${API}/sistemas-prediais`);
});

test("somente respostas 200 sem no-store/private são gravadas", () => {
  assert.equal(isCacheableResponse(200, null), true);
  assert.equal(isCacheableResponse(200, "max-age=60"), true);
  assert.equal(isCacheableResponse(200, "no-store"), false);
  assert.equal(isCacheableResponse(200, "private, max-age=0"), false);
  for (const s of [201, 204, 304, 401, 404, 500]) assert.equal(isCacheableResponse(s, null), false, String(s));
});

test("TTL", () => {
  assert.equal(isFresh(1000, 1500, 1000), true);
  assert.equal(isFresh(1000, 2000, 1000), false);
  assert.equal(isFresh(2000, 1000, 1000), false);
});

test("api.json e snapshot.enc (raw.githubusercontent.com) nunca são interceptados nem cacheados", () => {
  const raw = "https://raw.githubusercontent.com/rafaelroriz-age/garra-engenharia/snapshot";
  for (const arq of ["api.json", "snapshot.enc", "api.json?t=1"]) {
    assert.equal(isNeverIntercepted(`${raw}/${arq}`), true, arq);
    assert.equal(isCacheableRequest({ method: "GET", url: `${raw}/${arq}` }), false, arq);
  }
  // Mesmo um caminho que casaria a allowlist não é cacheado nesse host.
  assert.equal(isCacheableRequest({ method: "GET", url: "https://raw.githubusercontent.com/api/v1/contratos" }), false);
  assert.equal(isNeverIntercepted(`${API}/contratos`), false);
});

test("public/sw.js duplica exatamente as regras deste módulo", () => {
  const sw = readFileSync(new URL("../public/sw.js", import.meta.url), "utf8");
  const swPatterns = (sw.match(/pattern: "[^"]*"/g) ?? []).map((s) => s.slice(10, -1));
  const swNever = (sw.match(/never: "[^"]*"/g) ?? []).map((s) => s.slice(8, -1));
  const swHosts = (sw.match(/host: "[^"]*"/g) ?? []).map((s) => s.slice(7, -1));
  assert.deepEqual(swPatterns, ALLOWLIST.map((r) => r.pattern));
  assert.deepEqual(swNever, [...NEVER_CACHE_PATTERNS]);
  assert.deepEqual(swHosts, [...NEVER_INTERCEPT_HOSTS]);
});

test("public/sw.js resolve a página offline pelo scope (basePath do Pages)", () => {
  const sw = readFileSync(new URL("../public/sw.js", import.meta.url), "utf8");
  assert.match(sw, /new URL\("offline\.html", self\.registration\.scope\)/);
  assert.doesNotMatch(sw, /OFFLINE_URL = "\//);
});

const TOKEN_KEY = "garra:access_token";

test("logout em outra aba: token removido limpa o cache", () => {
  assert.equal(isLogoutStorageEvent({ key: TOKEN_KEY, newValue: null }, TOKEN_KEY), true);
});

test("logout em outra aba: storage.clear() (key null) limpa o cache", () => {
  assert.equal(isLogoutStorageEvent({ key: null, newValue: null }, TOKEN_KEY), true);
});

test("logout em outra aba: outra chave é ignorada", () => {
  assert.equal(isLogoutStorageEvent({ key: "outra", newValue: null }, TOKEN_KEY), false);
});

test("logout em outra aba: token trocado por outro não limpa", () => {
  assert.equal(isLogoutStorageEvent({ key: TOKEN_KEY, newValue: "novo.jwt" }, TOKEN_KEY), false);
});

test("logout em outra aba: evento ausente (ambiente sem API) não lança", () => {
  assert.equal(isLogoutStorageEvent(undefined, TOKEN_KEY), false);
  assert.equal(isLogoutStorageEvent(null, TOKEN_KEY), false);
});
