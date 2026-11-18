import { execSync } from "node:child_process";
import { existsSync, readFileSync, statSync } from "node:fs";
import { createServer, type Server } from "node:http";
import path from "node:path";

import { expect, test, type BrowserContext, type Page } from "@playwright/test";

import { BASE_PATH_SW, PORTA_SW } from "../playwright.sw.config";

/**
 * E2E do Service Worker no export estático sob o basePath do Pages (R-22, T90) — rodar com
 * `npx playwright test -c playwright.sw.config.ts`. API 100% mockada via `context.route`
 * (requisições feitas pelo SW só são vistas por rotas do contexto, não da página).
 */
const FRONT_DIR = path.resolve(__dirname, "..");
const OUT_DIR = path.join(FRONT_DIR, "out");
const ORIGEM = `http://localhost:${PORTA_SW}`;
const API = "http://api.e2e.test:8000/api/v1";
const TOKEN = "token-falso-e2e-sw";
const DATA_CACHE = "garra-sw-data-v2"; // CACHE_VERSION em public/sw.js

const TIPOS: Record<string, string> = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".png": "image/png",
  ".svg": "image/svg+xml",
  ".ico": "image/x-icon",
  ".woff2": "font/woff2",
  ".txt": "text/plain; charset=utf-8",
};

function arquivo(relativo: string): string | null {
  const alvo = path.normalize(path.join(OUT_DIR, decodeURIComponent(relativo)));
  if (!alvo.startsWith(OUT_DIR)) return null;
  for (const c of [alvo, path.join(alvo, "index.html"), `${alvo}.html`]) {
    if (existsSync(c) && statSync(c).isFile()) return c;
  }
  return null;
}

function iniciarServidor(): Promise<Server> {
  const srv = createServer((req, res) => {
    const url = new URL(req.url ?? "/", ORIGEM);
    const ok = url.pathname === BASE_PATH_SW || url.pathname.startsWith(`${BASE_PATH_SW}/`);
    const destino = ok ? arquivo(url.pathname.slice(BASE_PATH_SW.length)) : null;
    if (!destino) {
      res.writeHead(404).end("nao encontrado");
      return;
    }
    res.writeHead(200, { "Content-Type": TIPOS[path.extname(destino)] ?? "application/octet-stream", "Cache-Control": "no-store" });
    res.end(readFileSync(destino));
  });
  return new Promise((resolve, reject) => {
    srv.once("error", reject);
    srv.listen(PORTA_SW, () => resolve(srv));
  });
}

/** Contadores de acesso à "rede" (mock) por `METODO pathname`; `versao` muda o corpo servido. */
const acessos = new Map<string, number>();
let versao = 1;

async function mockarApi(context: BrowserContext): Promise<void> {
  await context.route(`${API}/**`, async (route) => {
    const req = route.request();
    const cors = {
      "Access-Control-Allow-Origin": ORIGEM,
      "Access-Control-Allow-Headers": "authorization, content-type",
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    };
    if (req.method() === "OPTIONS") {
      await route.fulfill({ status: 204, headers: cors });
      return;
    }
    const chave = `${req.method()} ${new URL(req.url()).pathname}`;
    acessos.set(chave, (acessos.get(chave) ?? 0) + 1);
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      headers: cors,
      body: JSON.stringify({ versao, rota: chave }),
    });
  });
}

/** fetch feito pela página (passa pelo SW); devolve o corpo JSON. */
async function chamar(page: Page, rota: string, init: { method?: string; auth?: boolean } = {}): Promise<{ versao: number }> {
  return page.evaluate(
    async ({ url, method, auth, token }) => {
      const r = await fetch(url, { method, headers: auth ? { Authorization: `Bearer ${token}` } : {} });
      return r.json();
    },
    { url: `${API}${rota}`, method: init.method ?? "GET", auth: init.auth ?? false, token: TOKEN },
  );
}

async function chavesDoCache(page: Page): Promise<string[]> {
  return page.evaluate(async (nome) => {
    if (!(await caches.keys()).includes(nome)) return [];
    return (await (await caches.open(nome)).keys()).map((r) => new URL(r.url).pathname);
  }, DATA_CACHE);
}

let servidor: Server;

test.describe.configure({ mode: "serial" });

test.describe("Service Worker sob basePath do Pages (R-22)", () => {
  test.beforeAll(async () => {
    test.setTimeout(600_000);
    if (!process.env.E2E_SW_SEM_BUILD) {
      execSync("npm run build", {
        cwd: FRONT_DIR,
        stdio: "inherit",
        env: { ...process.env, NEXT_PUBLIC_BASE_PATH: BASE_PATH_SW, NEXT_PUBLIC_API_URL: API, NEXT_PUBLIC_API_DISCOVERY_URL: "" },
      });
    }
    if (!existsSync(path.join(OUT_DIR, "login", "index.html"))) throw new Error("out/ não foi gerado.");
    servidor = await iniciarServidor();
  });

  test.afterAll(async () => {
    await new Promise<void>((resolve) => (servidor ? servidor.close(() => resolve()) : resolve()));
  });

  test("registra com scope do basePath, cacheia leitura, limpa no logout e nunca cacheia auth/portal/não-GET", async ({ page, context }) => {
    await mockarApi(context);
    await page.addInitScript((t) => window.localStorage.setItem("garra:access_token", t), TOKEN);

    // ---- (1) registro com scope /garra-engenharia/ ----
    await page.goto("login/");
    const scope = await page.evaluate(async () => (await navigator.serviceWorker.ready).scope);
    expect(scope).toBe(`${ORIGEM}${BASE_PATH_SW}/`);
    await page.waitForFunction(() => !!navigator.serviceWorker.controller); // clients.claim()
    const script = await page.evaluate(async () => (await navigator.serviceWorker.ready).active?.scriptURL);
    expect(script).toBe(`${ORIGEM}${BASE_PATH_SW}/sw.js`);
    // install pré-cacheou o offline.html relativo ao scope
    const shell = await page.evaluate(async () => (await (await caches.open("garra-sw-shell-v2")).keys()).map((r) => new URL(r.url).pathname));
    expect(shell).toEqual([`${BASE_PATH_SW}/offline.html`]);

    // ---- (2) allowlist servida do cache dentro do TTL ----
    versao = 1;
    expect((await chamar(page, "/sistemas-prediais")).versao).toBe(1); // rede → grava
    await expect.poll(() => chavesDoCache(page)).toContain("/api/v1/sistemas-prediais");
    versao = 2; // a "rede" agora responderia outra coisa
    expect((await chamar(page, "/sistemas-prediais")).versao).toBe(1); // servido do cache (stale)

    // contratos (por usuário, com Authorization)
    versao = 1;
    await chamar(page, "/contratos", { auth: true });
    versao = 2;
    expect((await chamar(page, "/contratos", { auth: true })).versao).toBe(1);
    // sem Authorization, dado por usuário não é cacheado: vai à rede
    expect((await chamar(page, "/contratos")).versao).toBe(2);

    // ---- (4) auth, portal e não-GET nunca cacheados ----
    versao = 1;
    await chamar(page, "/auth/me", { auth: true });
    await chamar(page, "/portal/contratos", { auth: true });
    await chamar(page, "/sistemas-prediais", { method: "POST", auth: true });
    versao = 2;
    expect((await chamar(page, "/auth/me", { auth: true })).versao).toBe(2);
    expect((await chamar(page, "/portal/contratos", { auth: true })).versao).toBe(2);
    expect(acessos.get("POST /api/v1/sistemas-prediais")).toBe(1); // POST chegou à rede (não interceptado)
    const chaves = await chavesDoCache(page);
    expect(chaves.some((c) => /\/(auth|portal)(\/|$)/.test(c))).toBe(false);
    expect(chaves).toContain("/api/v1/sistemas-prediais"); // só o GET de leitura
    // (a revalidação em segundo plano do SWR regrava o cache com o corpo novo; por isso não se
    // compara o corpo aqui, só as chaves do cache acima)

    // ---- (3) logout: clearAuthToken() dispara garra:clear-sw-cache (lib/api-client.ts) ----
    expect((await chavesDoCache(page)).length).toBeGreaterThan(0);
    await page.evaluate(() => {
      window.localStorage.removeItem("garra:access_token");
      window.dispatchEvent(new Event("garra:clear-sw-cache")); // exatamente o que clearAuthToken() faz
    });
    await expect.poll(() => chavesDoCache(page)).toEqual([]);
    versao = 3;
    expect((await chamar(page, "/sistemas-prediais")).versao).toBe(3); // sem cache: rede de novo
  });
});
