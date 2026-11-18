import { expect, test, type BrowserContext, type Page } from "@playwright/test";

import { API_OFFLINE as API, PORTA_OFFLINE } from "../playwright.offline.config";

/**
 * E2E offline online-first (DEC-26, DEC-56; R-22; T78) — rodar com
 * `npx playwright test -c playwright.offline.config.ts` (build de produção: o SW só registra assim).
 * API 100% mockada via `context.route` (o SW só enxerga rotas de contexto). Mockado: /auth/me
 * (auditor), GET /sistemas-prediais, GET /contratos, GET /edificacoes (lista vazia) e POST
 * /edificacoes. Quando `rede.cortada`, o mock aborta (além de `context.setOffline(true)`).
 */
const ORIGEM = `http://localhost:${PORTA_OFFLINE}`;
const TOKEN = "token-falso-e2e-offline";
const DATA_CACHE = "garra-sw-data-v2"; // CACHE_VERSION em public/sw.js

const rede = { cortada: false, versao: 1, posts: 0 };

async function mockarApi(context: BrowserContext): Promise<void> {
  await context.route(`${API}/**`, async (route) => {
    if (rede.cortada) return route.abort("internetdisconnected");
    const req = route.request();
    const cors = {
      "Access-Control-Allow-Origin": ORIGEM,
      "Access-Control-Allow-Headers": "authorization, content-type",
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    };
    if (req.method() === "OPTIONS") return route.fulfill({ status: 204, headers: cors });
    const p = new URL(req.url()).pathname;
    let corpo: unknown = { versao: rede.versao, rota: p };
    if (p.endsWith("/auth/me")) corpo = { id: 1, nome: "Auditor E2E", email: "e2e@garra.test", role: "auditor" };
    else if (p.endsWith("/edificacoes") && req.method() === "GET") corpo = [];
    else if (p.endsWith("/edificacoes") && req.method() === "POST") rede.posts += 1;
    await route.fulfill({ status: 200, contentType: "application/json", headers: cors, body: JSON.stringify(corpo) });
  });
}

async function chamar(page: Page, rota: string, auth = false): Promise<{ versao: number }> {
  return page.evaluate(
    async ({ url, auth, token }) => (await fetch(url, { headers: auth ? { Authorization: `Bearer ${token}` } : {} })).json(),
    { url: `${API}${rota}`, auth, token: TOKEN },
  );
}

async function chavesDoCache(page: Page): Promise<string[]> {
  return page.evaluate(async (nome) => {
    if (!(await caches.keys()).includes(nome)) return [];
    return (await (await caches.open(nome)).keys()).map((r) => new URL(r.url).pathname);
  }, DATA_CACHE);
}

test.describe.configure({ mode: "serial" });

test.describe("Offline online-first (DEC-26)", () => {
  test.beforeEach(async ({ context, page }) => {
    rede.cortada = false;
    rede.versao = 1;
    rede.posts = 0;
    await mockarApi(context);
    await page.addInitScript((t) => {
      if (!window.localStorage.getItem("garra:access_token")) window.localStorage.setItem("garra:access_token", t);
    }, TOKEN);
  });

  test("(1) leitura da allowlist segue dentro do TTL sem rede; fora da allowlist cai no offline.html", async ({ page, context }) => {
    await page.goto("/login/");
    await page.evaluate(async () => (await navigator.serviceWorker.ready).scope);
    await page.waitForFunction(() => !!navigator.serviceWorker.controller);

    // dados mestre e contratos carregados online (gravam no cache do SW)
    expect((await chamar(page, "/sistemas-prediais")).versao).toBe(1);
    expect((await chamar(page, "/contratos", true)).versao).toBe(1);
    await expect.poll(() => chavesDoCache(page)).toEqual(expect.arrayContaining(["/api/v1/sistemas-prediais", "/api/v1/contratos"]));

    // corta a rede
    rede.cortada = true;
    rede.versao = 2;
    await context.setOffline(true);

    // dentro do TTL: servido do cache
    expect((await chamar(page, "/sistemas-prediais")).versao).toBe(1);
    expect((await chamar(page, "/contratos", true)).versao).toBe(1);

    // fora da allowlist (GET de API) falha com erro de rede; sem fallback silencioso
    await expect(chamar(page, "/edificacoes", true)).rejects.toThrow();

    // navegação (fora da allowlist) cai no offline.html pré-cacheado
    await page.goto("/edificacoes/");
    await expect(page).toHaveTitle(/Sem conexão/);
    await expect(page.getByRole("heading", { name: "Você está sem conexão" })).toBeVisible();
    await expect(page.getByText(/exige conexão com a internet/)).toBeVisible();
  });

  test("(2) escrita sem rede mostra erro explícito e não cria fila local", async ({ page, context }) => {
    await page.goto("/edificacoes/");
    await page.waitForFunction(() => !!navigator.serviceWorker.controller);
    await page.getByRole("button", { name: "Nova edificação" }).click();
    const dialog = page.getByRole("dialog");
    await dialog.getByLabel("Nome").fill("Ed. Offline E2E");
    await dialog.getByLabel("Endereço").fill("Rua Offline, 1");

    rede.cortada = true;
    await context.setOffline(true);
    await dialog.getByRole("button", { name: "Criar edificação" }).click();

    // erro explícito (ApiError "Falha de conexão"); o diálogo permanece aberto
    await expect(dialog.getByText(/Falha de conexão|Não foi possível conectar ao servidor/).first()).toBeVisible();
    await expect(dialog).toBeVisible();
    expect(rede.posts).toBe(0);

    // nenhum mecanismo de fila: localStorage só tem o token; IndexedDB sem banco; cache sem POST
    const estado = await page.evaluate(async () => {
      const dbs = "databases" in indexedDB ? await indexedDB.databases() : [];
      const ls = Object.keys(window.localStorage);
      const nomes = await caches.keys();
      const reqs: { method: string; url: string }[] = [];
      for (const n of nomes) for (const r of await (await caches.open(n)).keys()) reqs.push({ method: r.method, url: r.url });
      const valores = ls.map((k) => window.localStorage.getItem(k) ?? "").join("|");
      return { dbs: dbs.map((d) => d.name), ls, reqs, valores };
    });
    expect(estado.dbs).toEqual([]);
    expect(estado.ls.filter((k) => /fila|queue|pend|outbox|sync/i.test(k))).toEqual([]);
    expect(estado.valores).not.toContain("Ed. Offline E2E");
    expect(estado.reqs.filter((r) => r.method !== "GET")).toEqual([]);
    expect(estado.reqs.some((r) => /edificacoes/.test(r.url))).toBe(false);

    // ao voltar a rede nada é reenviado automaticamente
    rede.cortada = false;
    await context.setOffline(false);
    await page.waitForTimeout(1500);
    expect(rede.posts).toBe(0);
  });
});
