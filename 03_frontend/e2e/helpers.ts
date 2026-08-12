import type { APIRequestContext, Page } from "@playwright/test";
import { expect } from "@playwright/test";

/**
 * Helpers compartilhados pelos testes E2E dos Fluxos 1 (RFO) e 2 (LTIP)
 * (BL-21, `estudo-do-contexto.md` Seção 8).
 */

export const API_BASE_URL = process.env.E2E_API_BASE_URL ?? "http://localhost:8000/api/v1";

/** PNG 1x1 válido (magic bytes reais) — aceito pela validação Pillow do backend (mitigação A08, BL-11). */
export const PNG_1X1_BASE64 =
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=";

export function pngBuffer(): Buffer {
  return Buffer.from(PNG_1X1_BASE64, "base64");
}

export function nomeUnico(prefixo: string): string {
  return `${prefixo} E2E ${Date.now()}-${Math.floor(Math.random() * 100000)}`;
}

export function cnpjUnico(): string {
  // 14 dígitos — a validação client-side (`onlyDigits(cnpj).length === 14`) não checa dígito verificador.
  return String(Date.now()).padStart(14, "0").slice(-14);
}

export interface AuthContext {
  email: string;
  senha: string;
  token: string;
}

/**
 * Registra um usuário novo (BL-06) via API e retorna o access_token — evita repetir o formulário
 * de registro (que nem existe na UI) em cada teste.
 *
 * Desde o hardening de segurança (BL-23), `POST /auth/register` exige um auditor autenticado:
 * o helper primeiro loga com o admin de bootstrap (`app.scripts.seed_admin`, executado no setup
 * do ambiente/CI) e usa esse token para criar o usuário do teste.
 */
export async function registrarUsuario(request: APIRequestContext): Promise<AuthContext> {
  const email = `e2e-${Date.now()}-${Math.floor(Math.random() * 100000)}@garra-engenharia.com.br`;
  const senha = "Senha@Teste123";

  const adminToken = await obterTokenAdmin(request);
  const registerResponse = await request.post(`${API_BASE_URL}/auth/register`, {
    data: { nome: "Usuário E2E", email, senha },
    headers: { Authorization: `Bearer ${adminToken}` },
  });
  if (!registerResponse.ok()) {
    throw new Error(
      `Falha ao registrar usuário de teste: ${registerResponse.status()} ${await registerResponse.text()}`
    );
  }

  const loginResponse = await request.post(`${API_BASE_URL}/auth/login`, { data: { email, senha } });
  if (!loginResponse.ok()) {
    throw new Error(`Falha ao logar usuário de teste recém-criado: ${loginResponse.status()}`);
  }
  const { access_token } = (await loginResponse.json()) as { access_token: string };
  return { email, senha, token: access_token };
}

const ADMIN_EMAIL = process.env.E2E_ADMIN_EMAIL ?? "admin@garra-engenharia.com.br";
const ADMIN_SENHA = process.env.E2E_ADMIN_SENHA ?? "Admin@Garra123";

/** Token do auditor de bootstrap. Se não existir, tenta criá-lo (só funciona em banco vazio). */
async function obterTokenAdmin(request: APIRequestContext): Promise<string> {
  const login = await request.post(`${API_BASE_URL}/auth/login`, {
    data: { email: ADMIN_EMAIL, senha: ADMIN_SENHA },
  });
  if (login.ok()) {
    return ((await login.json()) as { access_token: string }).access_token;
  }

  const bootstrap = await request.post(`${API_BASE_URL}/auth/register`, {
    data: { nome: "Administrador", email: ADMIN_EMAIL, senha: ADMIN_SENHA },
  });
  if (!bootstrap.ok()) {
    throw new Error(
      `Nenhum usuário administrativo disponível para os testes E2E. Rode ` +
        `\`docker compose exec backend python -m app.scripts.seed_admin\` antes. ` +
        `(login=${login.status()}, bootstrap=${bootstrap.status()})`
    );
  }
  const login2 = await request.post(`${API_BASE_URL}/auth/login`, {
    data: { email: ADMIN_EMAIL, senha: ADMIN_SENHA },
  });
  return ((await login2.json()) as { access_token: string }).access_token;
}

/** Faz login pela UI (valida o fluxo real de `POST /auth/login` + guarda de rota, BL-06). */
export async function loginPelaUI(page: Page, auth: AuthContext): Promise<void> {
  await page.goto("/login");
  await page.getByLabel("E-mail").fill(auth.email);
  await page.getByLabel("Senha").fill(auth.senha);
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(page).toHaveURL(/\/dashboard/);
}

/** Cria um Responsável (fiscal/executor/contratante) via API (DEC-23) — sem essa rota, o formulário de Contrato não tem como referenciar um UUID válido. */
export async function criarResponsavel(
  request: APIRequestContext,
  token: string,
  payload: { nome: string; tipo: string; crea?: string }
): Promise<string> {
  const response = await request.post(`${API_BASE_URL}/responsaveis`, {
    data: payload,
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok()) {
    throw new Error(`Falha ao criar Responsavel de teste: ${response.status()} ${await response.text()}`);
  }
  const body = (await response.json()) as { id: string };
  return body.id;
}

/**
 * Faz upload de uma foto através do editor de anotação (Fabric.js, DEC-19) que
 * abre automaticamente após selecionar um arquivo. `scope` restringe a busca
 * do botão/input a uma seção específica da página (várias seções de upload
 * de foto podem coexistir na mesma tela, ex.: múltiplas Visitas).
 */
export async function enviarFotoViaEditor(page: Page, scope: ReturnType<Page["locator"]>): Promise<void> {
  await scope.getByRole("button", { name: "Enviar arquivo" }).click();
  await scope.locator('input[type="file"]').setInputFiles({
    name: "foto-e2e.png",
    mimeType: "image/png",
    buffer: pngBuffer(),
  });

  const dialog = page.getByRole("dialog").filter({ hasText: "Editar e marcar foto" });
  // Fabric.js renderiza 2 elementos <canvas> empilhados (camada de imagem +
  // camada de interação "upper-canvas") — `.first()` evita "strict mode violation".
  await expect(dialog.locator("canvas").first()).toBeVisible({ timeout: 15_000 });

  const uploadResponse = page.waitForResponse(
    (response) => response.url().includes("/fotos/upload") && response.request().method() === "POST"
  );
  await dialog.getByRole("button", { name: "Salvar marcação" }).click();
  await uploadResponse;
  await expect(dialog).toBeHidden();
}
