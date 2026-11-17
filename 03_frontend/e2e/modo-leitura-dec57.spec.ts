import { execFileSync, execSync } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, statSync, writeFileSync } from "node:fs";
import { createServer, type Server } from "node:http";
import { tmpdir } from "node:os";
import path from "node:path";

import { expect, test, type Page } from "@playwright/test";

import { BASE_PATH_MODO_LEITURA, PORTA_MODO_LEITURA } from "../playwright.modo-leitura.config";
import { cnpjUnico, criarResponsavel, nomeUnico, registrarUsuario, type AuthContext } from "./helpers";

/**
 * E2E do modo leitura com snapshot cifrado (DEC-57, T86) — rodar com
 * `npx playwright test -c playwright.modo-leitura.config.ts`.
 *
 * O build estático (`out/`, basePath de produção) é servido numa porta própria junto de um
 * diretório de dados (`/dados/api.json`, `/dados/snapshot.enc`) controlado pelo teste, no lugar
 * da branch `snapshot` do GitHub. Prova, em sequência:
 *  1. api.json online → login e criação de ocorrência contra o backend local;
 *  2. api.json `online:false` + snapshot gerado por `gerar_snapshot` depois da criação → ao
 *     recarregar: faixa, pedido de senha, ocorrência criada visível, gravação desabilitada;
 *  3. escrita forçada → "Servidor desligado — modo leitura".
 *
 * Pré-requisito: backend em E2E_API_BASE_URL (padrão http://localhost:8000/api/v1) com CORS para
 * a origem http://localhost:3100 e o mesmo banco usado pelo `gerar_snapshot` (variáveis
 * POSTGRES_* do ambiente deste processo). Esses ambiente herdado pelo `gerar_snapshot`.
 */
const FRONT_DIR = path.resolve(__dirname, "..");
const BACKEND_DIR = path.resolve(FRONT_DIR, "..", "04_backend");
const OUT_DIR = path.join(FRONT_DIR, "out");
const ORIGEM = `http://localhost:${PORTA_MODO_LEITURA}`;
const SNAPSHOT_SENHA = "senha-e2e-modo-leitura-t86";
const API_RAIZ = (process.env.E2E_API_BASE_URL ?? "http://localhost:8000/api/v1").replace(/\/api\/v1$/, "");

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

let dados: string;
let servidor: Server;

function escreverApiJson(online: boolean): void {
  const corpo = online
    ? { url: API_RAIZ, api_base: `${API_RAIZ}/api/v1`, online: true, desde: new Date().toISOString(), heartbeat: new Date().toISOString() }
    : { online: false };
  writeFileSync(path.join(dados, "api.json"), JSON.stringify(corpo));
}

/** Resolve um arquivo estático dentro de `raiz` (índice de diretório; sem escapar da raiz). */
function arquivo(raiz: string, relativo: string): string | null {
  const alvo = path.normalize(path.join(raiz, decodeURIComponent(relativo)));
  if (!alvo.startsWith(raiz)) return null;
  for (const candidato of [alvo, path.join(alvo, "index.html"), `${alvo}.html`]) {
    if (existsSync(candidato) && statSync(candidato).isFile()) return candidato;
  }
  return null;
}

function iniciarServidor(): Promise<Server> {
  const srv = createServer((req, res) => {
    const url = new URL(req.url ?? "/", ORIGEM);
    let destino: string | null = null;
    if (url.pathname.startsWith("/dados/")) destino = arquivo(dados, url.pathname.slice("/dados/".length));
    else if (url.pathname === BASE_PATH_MODO_LEITURA || url.pathname.startsWith(`${BASE_PATH_MODO_LEITURA}/`)) {
      destino = arquivo(OUT_DIR, url.pathname.slice(BASE_PATH_MODO_LEITURA.length));
    }
    if (!destino) {
      res.writeHead(404).end("nao encontrado");
      return;
    }
    res.writeHead(200, {
      "Content-Type": TIPOS[path.extname(destino)] ?? "application/octet-stream",
      "Cache-Control": "no-store",
    });
    res.end(readFileSync(destino));
  });
  return new Promise((resolve, reject) => {
    srv.once("error", reject);
    srv.listen(PORTA_MODO_LEITURA, () => resolve(srv));
  });
}

/** Mesmo fluxo de `inspecao-helpers.prepararInspecao` (LTIP), com URLs relativas ao basePath. */
async function loginPelaUIBase(page: Page, auth: AuthContext): Promise<void> {
  await page.goto("login/");
  await page.getByLabel("E-mail").fill(auth.email);
  await page.getByLabel("Senha").fill(auth.senha);
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(page).toHaveURL(/\/dashboard/);
}

test.describe.configure({ mode: "serial" });

test.describe("Modo leitura com snapshot (DEC-57)", () => {
  test.beforeAll(async () => {
    test.setTimeout(600_000);
    dados = mkdtempSync(path.join(tmpdir(), "garra-e2e-ml-"));
    escreverApiJson(true);
    if (!process.env.E2E_ML_SEM_BUILD) {
      execSync("npm run build", {
        cwd: FRONT_DIR,
        stdio: "inherit",
        env: {
          ...process.env,
          NEXT_PUBLIC_BASE_PATH: BASE_PATH_MODO_LEITURA,
          NEXT_PUBLIC_API_DISCOVERY_URL: `${ORIGEM}/dados/api.json`,
          NEXT_PUBLIC_API_URL: "",
        },
      });
    }
    if (!existsSync(path.join(OUT_DIR, "login", "index.html"))) throw new Error("out/ não foi gerado.");
    servidor = await iniciarServidor();
  });

  test.afterAll(async () => {
    await new Promise<void>((resolve) => (servidor ? servidor.close(() => resolve()) : resolve()));
    if (dados) rmSync(dados, { recursive: true, force: true });
  });

  test("online, depois PC desligado: leitura do snapshot com gravação bloqueada", async ({ page, request }) => {
    // ---- (1) api.json online: login e criação de uma ocorrência ----
    const auth = await registrarUsuario(request);
    const fiscalId = await criarResponsavel(request, auth.token, {
      nome: nomeUnico("Eng. Fiscal"),
      tipo: "fiscal",
      crea: "333333-GO",
    });
    const responsavelLegalId = await criarResponsavel(request, auth.token, {
      nome: nomeUnico("Responsável Legal"),
      tipo: "responsavel_legal",
    });

    await loginPelaUIBase(page, auth);
    await expect(page.getByText(/Modo leitura — dados de/)).toHaveCount(0);

    const nomeEdificacao = nomeUnico("Ed. ML");
    await page.goto("edificacoes/");
    await page.getByRole("button", { name: "Nova edificação" }).click();
    const dialogEdificacao = page.getByRole("dialog");
    await dialogEdificacao.getByLabel("Nome").fill(nomeEdificacao);
    await dialogEdificacao.getByLabel("Endereço").fill("Rua do Modo Leitura, 86");
    await dialogEdificacao.getByRole("button", { name: "Criar edificação" }).click();
    await expect(dialogEdificacao).toBeHidden();

    const numeroContrato = `CT-ML-${Date.now()}`;
    await page.goto("contratos/");
    await page.getByRole("button", { name: "Novo contrato" }).click();
    const dialogContrato = page.getByRole("dialog");
    await dialogContrato.getByLabel("Edificação").selectOption({ label: nomeEdificacao });
    await dialogContrato.getByLabel("Número do contrato").fill(numeroContrato);
    await dialogContrato.getByLabel("Tipo de serviço").selectOption("LTIP");
    await dialogContrato.getByLabel("Engenheiro fiscal (ID)").fill(fiscalId);
    await dialogContrato.getByLabel("ART de Fiscalização").fill("ART-FISC-0086");
    await dialogContrato.getByLabel("Razão social").fill("Construtora Exemplo Ltda");
    await dialogContrato.getByLabel("CNPJ").fill(cnpjUnico());
    await dialogContrato.getByLabel("Responsável legal (ID)").fill(responsavelLegalId);
    await dialogContrato.getByLabel("ART de Execução").fill("ART-EXEC-0086");
    await dialogContrato.getByRole("button", { name: "Criar contrato" }).click();
    await expect(dialogContrato).toBeHidden();

    await page.getByLabel("Edificação").selectOption({ label: nomeEdificacao });
    const linkContrato = page.getByRole("link", { name: numeroContrato });
    await expect(linkContrato).toBeVisible();
    await linkContrato.click();
    await page.getByRole("link", { name: "Ocorrências", exact: true }).click();
    await expect(page).toHaveURL(/\/inspecoes\/ocorrencias\/\?id=[0-9a-f-]+$/);
    const urlOcorrencias = page.url();

    const localizacao = `Fachada ML ${Date.now()}`;
    await page.getByRole("button", { name: "Nova ocorrência" }).click();
    const dialog = page.getByRole("dialog");
    await dialog.getByLabel("Sistema predial").selectOption({ index: 1 });
    const subsistema = dialog.getByLabel("Subsistema");
    if ((await subsistema.locator("option").count()) > 1) await subsistema.selectOption({ index: 1 });
    await dialog.getByLabel("Localização").fill(localizacao);
    await dialog.getByLabel("Situação").selectOption({ label: "Não Conforme" });
    await dialog.getByLabel("Classificação").selectOption({ label: "Anomalia" });
    await dialog.getByLabel("Tipo de Anomalia").selectOption({ index: 1 });
    await dialog.getByLabel("Grau de Risco (CMM)").selectOption({ label: "Médio" });
    await dialog.getByLabel("Descrição").fill("Fissura criada pelo E2E do modo leitura.");
    const criada = page.waitForResponse(
      (r) => /\/ocorrencias$/.test(new URL(r.url()).pathname) && r.request().method() === "POST"
    );
    await dialog.getByRole("button", { name: "Criar ocorrência" }).click();
    expect((await criada).status()).toBe(201);
    await dialog.getByRole("button", { name: "Concluir" }).click();
    await expect(dialog).toBeHidden();
    await expect(page.getByRole("row").filter({ hasText: localizacao })).toHaveCount(1);

    // ---- (2) snapshot gerado DEPOIS da criação; api.json passa a offline ----
    const snapshotEnc = path.join(dados, "snapshot.enc");
    mkdirSync(dados, { recursive: true });
    const saida = execFileSync("python", ["-m", "app.scripts.gerar_snapshot", "--saida", snapshotEnc], {
      cwd: BACKEND_DIR,
      env: { ...process.env, SNAPSHOT_SENHA },
      encoding: "utf-8",
    });
    console.log(`gerar_snapshot:\n${saida}`);
    expect(existsSync(snapshotEnc)).toBe(true);
    escreverApiJson(false);

    await page.goto(urlOcorrencias); // recarga completa: descarta o cache de 60 s do api.json
    await expect(page.getByText(/Modo leitura — dados de/)).toBeVisible({ timeout: 20_000 });
    const dialogSenha = page.getByRole("dialog").filter({ hasText: "Senha da equipe" });
    await expect(dialogSenha).toBeVisible();

    // senha errada: continua pedindo
    await dialogSenha.getByLabel("Senha da equipe").fill("senha-errada-xxxxxxxx");
    await dialogSenha.getByRole("button", { name: "Abrir dados" }).click();
    await expect(dialogSenha.getByText("Senha incorreta.")).toBeVisible();

    await dialogSenha.getByLabel("Senha da equipe").fill(SNAPSHOT_SENHA);
    await dialogSenha.getByRole("button", { name: "Abrir dados" }).click();
    await expect(dialogSenha).toBeHidden();

    // a ocorrência criada aparece, vinda do snapshot
    const linha = page.getByRole("row").filter({ hasText: localizacao });
    await expect(linha).toHaveCount(1);
    // botões de gravação desabilitados
    await expect(page.getByRole("button", { name: "Nova ocorrência" })).toBeDisabled();
    await expect(linha.getByRole("button", { name: /^Excluir ocorrência/ })).toBeDisabled();

    // ---- (3) escrita forçada ----
    // O React ignora cliques em botão cuja prop `disabled` é true (remover o atributo não adianta);
    // então o teste chama o `onClick` do botão direto pelas props do React, como faria um bug que
    // deixasse a gravação escapar da UI. A guarda de `apiFetch` tem de recusar.
    page.once("dialog", (d) => void d.accept()); // window.confirm da exclusão
    await linha.getByRole("button", { name: /^Excluir ocorrência/ }).evaluate((el) => {
      const chave = Object.keys(el).find((k) => k.startsWith("__reactProps$"));
      if (!chave) throw new Error("props do React não encontradas no botão");
      (el as unknown as Record<string, { onClick: () => void }>)[chave].onClick();
    });
    await expect(page.getByRole("alert").filter({ hasText: "Servidor desligado — modo leitura" })).toBeVisible();
    // nada foi gravado: a ocorrência segue na lista
    await expect(page.getByRole("row").filter({ hasText: localizacao })).toHaveCount(1);
  });
});
