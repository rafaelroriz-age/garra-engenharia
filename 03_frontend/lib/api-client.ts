/**
 * Cliente HTTP fino para consumir a API FastAPI (`00_docs/arquitetura.md` Seção 4).
 *
 * Responsabilidades:
 * - Montar a URL base (`NEXT_PUBLIC_API_URL`, default `http://localhost:8000/api/v1`).
 * - Anexar o token de autenticação (BL-06) quando presente em `localStorage`.
 * - Converter erros 4xx/5xx no formato RFC 7807 (`application/problem+json`, DEC-11)
 *   em uma exceção tipada `ApiError`, para tratamento consistente nas telas.
 *
 * Não contém regra de negócio — apenas transporte e parsing de erro.
 */

import type {
  ConteudoDados,
  Foto,
  FotoUpdateInput,
  FotoUploadResult,
  FormatoRelatorio,
  LegendaIAGerarInput,
  RelatorioConteudo,
  RelatorioDownload,
  RelatorioEmitido,
  RelatorioVersao,
  Responsavel,
  ResponsavelInput,
} from "@/lib/types";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

const AUTH_TOKEN_STORAGE_KEY = "garra:access_token";

/** Campo a campo de violação de validação, conforme o contrato RFC 7807 (Seção 10.7). */
export interface ProblemFieldError {
  field: string;
  message: string;
}

/** Corpo de erro `application/problem+json` retornado pela API. */
export interface ProblemDetails {
  type?: string;
  title: string;
  status: number;
  detail?: string;
  instance?: string;
  errors?: ProblemFieldError[];
}

/** Exceção lançada pelo cliente HTTP para qualquer resposta de erro da API. */
export class ApiError extends Error {
  readonly status: number;
  readonly title: string;
  readonly detail?: string;
  readonly errors: ProblemFieldError[];

  constructor(problem: ProblemDetails) {
    super(problem.detail ?? problem.title);
    this.name = "ApiError";
    this.status = problem.status;
    this.title = problem.title;
    this.detail = problem.detail;
    this.errors = problem.errors ?? [];
  }

  /** Retorna a mensagem de erro do campo informado, se existir. */
  fieldError(field: string): string | undefined {
    return this.errors.find((error) => error.field === field)?.message;
  }
}

function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(AUTH_TOKEN_STORAGE_KEY);
}

/** Persiste o token de acesso (BL-06) após um login bem-sucedido. */
export function setAuthToken(token: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, token);
}

/** Remove o token de acesso (logout). */
export function clearAuthToken(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
  // Limpa o cache de leitura do Service Worker (DEC-26); ver components/sw-register.tsx.
  window.dispatchEvent(new Event("garra:clear-sw-cache"));
}

/** Indica se há um token de acesso armazenado (não valida expiração/assinatura). */
export function isAuthenticated(): boolean {
  return getAuthToken() !== null;
}

interface ApiFetchOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  /** Quando `true`, envia `body` como `FormData`/`Blob` em vez de serializar em JSON. */
  raw?: boolean;
}

async function parseErrorResponse(response: Response): Promise<ApiError> {
  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("json")) {
    try {
      const data = (await response.json()) as Partial<ProblemDetails>;
      return new ApiError({
        title: data.title ?? "Erro inesperado",
        status: data.status ?? response.status,
        detail: data.detail,
        type: data.type,
        instance: data.instance,
        errors: data.errors,
      });
    } catch {
      // resposta não era JSON válido apesar do content-type — cai no fallback abaixo
    }
  }
  return new ApiError({
    title: response.statusText || "Erro inesperado",
    status: response.status,
    detail: "Não foi possível se comunicar com o servidor. Tente novamente.",
  });
}

/** Executa uma requisição à API e retorna o corpo já desserializado como `T`. */
export async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const { body, raw, headers, ...rest } = options;
  const token = getAuthToken();

  const finalHeaders = new Headers(headers);
  if (!raw && body !== undefined) {
    finalHeaders.set("Content-Type", "application/json");
  }
  if (token) {
    finalHeaders.set("Authorization", `Bearer ${token}`);
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...rest,
      headers: finalHeaders,
      body: body === undefined ? undefined : raw ? (body as BodyInit) : JSON.stringify(body),
    });
  } catch {
    throw new ApiError({
      title: "Falha de conexão",
      status: 0,
      detail: "Não foi possível conectar ao servidor. Verifique sua internet e tente novamente.",
    });
  }

  if (!response.ok) {
    throw await parseErrorResponse(response);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("json")) {
    return (await response.json()) as T;
  }
  return undefined as T;
}

export const api = {
  get: <T>(path: string, options?: ApiFetchOptions) => apiFetch<T>(path, { ...options, method: "GET" }),
  post: <T>(path: string, body?: unknown, options?: ApiFetchOptions) =>
    apiFetch<T>(path, { ...options, method: "POST", body }),
  put: <T>(path: string, body?: unknown, options?: ApiFetchOptions) =>
    apiFetch<T>(path, { ...options, method: "PUT", body }),
  delete: <T>(path: string, options?: ApiFetchOptions) => apiFetch<T>(path, { ...options, method: "DELETE" }),
};

/**
 * Chamadas de legenda de foto assistida por IA (BL-34/BL-35; RF-15, RN-16, RN-17).
 * Contrato em `00_docs/backlog-auto/legenda-ia-endpoints.md` §2. Ambas devolvem `FotoRead`.
 *
 * - `gerar`: grava só a sugestão (`legenda_ia_sugerida`, alertas, pendências) com
 *   `status_validacao_ia = "rascunho"`; nunca toca na `legenda` final. Responde 503
 *   (`legenda-ia-indisponivel`) enquanto não houver provedor de LLM configurado.
 * - `aprovar`: `PUT /fotos/{id}` com `aprovar_legenda_ia: true`; aprovador e data vêm do token.
 */
export const legendaIA = {
  gerar: (fotoId: string, input?: LegendaIAGerarInput) =>
    api.post<Foto>(`/fotos/${fotoId}/legenda-ia/gerar`, input ?? {}),
  aprovar: (fotoId: string, legenda: string) =>
    api.put<Foto>(`/fotos/${fotoId}`, { legenda, aprovar_legenda_ia: true } satisfies FotoUpdateInput),
};

/**
 * Emissão, versões e download de relatórios por inspeção (V1-02).
 * Contrato em `00_docs/backlog-auto/v1-emissao-generica.md`.
 *
 * - `listar`: auditor e auxiliar; mais recente primeiro.
 * - `emitir`: só auditor. Pode levar dezenas de segundos (PDF + DOCX). 422 traz em
 *   `errors[]` os campos faltantes (`{tipo}-contexto-incompleto`) ou o tipo não emitível.
 * - `download`: devolve URL pré-assinada de curta duração (mesmo formato do portal).
 */
export const relatorios = {
  listar: (inspecaoId: string) => api.get<RelatorioVersao[]>(`/inspecoes/${inspecaoId}/relatorios`),
  emitir: (inspecaoId: string, tipo: string) =>
    api.post<RelatorioEmitido>(`/inspecoes/${inspecaoId}/relatorios/${encodeURIComponent(tipo.toLowerCase())}`, {}),
  download: (inspecaoId: string, relatorioId: string, formato: FormatoRelatorio) =>
    api.get<RelatorioDownload>(`/inspecoes/${inspecaoId}/relatorios/${relatorioId}/download/${formato}`),
};

/**
 * Conteúdo narrativo do relatório por (inspeção, tipo) (V1-01).
 * Contrato em `00_docs/backlog-auto/v1-fundacao-dados.md`.
 *
 * - `obter`: auditor e auxiliar; `dados` já vem com os textos padrão mesclados.
 * - `salvar`: só auditor; SUBSTITUI o conteúdo salvo (o que não for enviado volta ao padrão).
 */
export const conteudo = {
  obter: (inspecaoId: string, tipo: string) =>
    api.get<RelatorioConteudo>(`/inspecoes/${inspecaoId}/conteudo/${encodeURIComponent(tipo.toLowerCase())}`),
  salvar: (inspecaoId: string, tipo: string, dados: ConteudoDados) =>
    api.put<RelatorioConteudo>(`/inspecoes/${inspecaoId}/conteudo/${encodeURIComponent(tipo.toLowerCase())}`, {
      dados,
    }),
};

/** Responsáveis (fiscal, RTE, responsável legal). A API não tem rota de edição (só criar/listar/obter). */
export const responsaveis = {
  listar: () => api.get<Responsavel[]>("/responsaveis"),
  criar: (input: ResponsavelInput) => api.post<Responsavel>("/responsaveis", input),
};

/** Upload bruto de imagem (`POST /fotos/upload`, multipart): devolve a chave no storage, sem vincular. */
export function uploadImagem(arquivo: File): Promise<FotoUploadResult> {
  const formData = new FormData();
  formData.append("arquivo", arquivo);
  return api.post<FotoUploadResult>("/fotos/upload", formData, { raw: true });
}
