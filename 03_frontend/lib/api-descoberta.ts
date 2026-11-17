/**
 * Descoberta da URL da API (DEC-57, T83).
 *
 * O backend roda no PC do dono atrás de um `cloudflared tunnel --url`, com URL
 * aleatória a cada boot. O agente do PC (T82) publica `api.json` na branch
 * `snapshot` do repositório público:
 *
 *   {"url": "https://x.trycloudflare.com", "api_base": "https://x.trycloudflare.com/api/v1",
 *    "online": true, "desde": "...", "heartbeat": "..."}
 *
 * O front lê esse arquivo de `NEXT_PUBLIC_API_DISCOVERY_URL` (com cache-buster e
 * cache em memória de 60 s). Sem essa variável (dev/docker-compose), usa
 * `NEXT_PUBLIC_API_URL` fixa e nunca entra em modo leitura.
 *
 * Sem dependências de alias (`@/`) para poder ser testado com `node --test`.
 */

/** Conteúdo de `api.json` publicado pelo agente do PC (T82). */
export interface ApiJson {
  url?: string;
  api_base?: string;
  online?: boolean;
  desde?: string;
  heartbeat?: string;
}

/** Resultado da descoberta usado pelo cliente HTTP. */
export interface ApiDescoberta {
  /** Base da API (termina em `/api/v1`), ou `null` se o servidor está indisponível. */
  apiBase: string | null;
  /** Raiz do servidor (sem `/api/v1`), para `/health`. */
  raiz: string | null;
  /** `true` quando há um servidor a tentar; `false` = entrar em modo leitura. */
  online: boolean;
  /** Motivo legível quando `online` é `false`. */
  motivo: string | null;
  heartbeat: string | null;
  /** `true` se a base veio do `api.json` (produção); `false` = URL fixa de dev. */
  descoberta: boolean;
}

/** Heartbeat mais velho que isso ⇒ PC considerado desligado (o agente bate a cada 10 min). */
export const HEARTBEAT_MAX_MS = 20 * 60 * 1000;
/** Validade do cache em memória do `api.json`. */
export const DESCOBERTA_TTL_MS = 60 * 1000;

const API_URL_FIXA = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
const DISCOVERY_URL = process.env.NEXT_PUBLIC_API_DISCOVERY_URL ?? "";

/** `true` quando o build usa descoberta por `api.json` (Pages de produção). */
export function descobertaConfigurada(): boolean {
  return DISCOVERY_URL !== "";
}

/** URL de `snapshot.enc`: mesmo diretório do `api.json` (branch `snapshot`). */
export function urlSnapshot(): string | null {
  if (!DISCOVERY_URL) return null;
  return DISCOVERY_URL.replace(/[^/]*$/, "snapshot.enc");
}

/** Acrescenta `?t=<agora>` para furar caches HTTP do navegador/CDN. */
export function comCacheBuster(url: string, agoraMs: number = Date.now()): string {
  return `${url}${url.includes("?") ? "&" : "?"}t=${agoraMs}`;
}

function semBarraFinal(s: string): string {
  return s.replace(/\/+$/, "");
}

/** Raiz do servidor a partir da base da API (`.../api/v1` → `...`). */
export function raizDaApi(apiBase: string): string {
  return semBarraFinal(apiBase).replace(/\/api\/v1$/, "");
}

/** Interpreta o `api.json` (função pura, testável). */
export function avaliarApiJson(json: ApiJson | null, agoraMs: number): ApiDescoberta {
  const base: Omit<ApiDescoberta, "online" | "motivo"> = {
    apiBase: null,
    raiz: null,
    heartbeat: json?.heartbeat ?? null,
    descoberta: true,
  };
  if (!json || typeof json !== "object") return { ...base, online: false, motivo: "api.json inválido" };
  if (json.online === false) return { ...base, online: false, motivo: "servidor desligado" };
  const hb = json.heartbeat ? Date.parse(json.heartbeat) : NaN;
  if (Number.isNaN(hb) || agoraMs - hb > HEARTBEAT_MAX_MS) {
    return { ...base, online: false, motivo: "servidor sem sinal há mais de 20 min" };
  }
  const apiBase = json.api_base
    ? semBarraFinal(json.api_base)
    : json.url
      ? `${semBarraFinal(json.url)}/api/v1`
      : null;
  if (!apiBase) return { ...base, online: false, motivo: "api.json sem URL" };
  return { ...base, apiBase, raiz: json.url ? semBarraFinal(json.url) : raizDaApi(apiBase), online: true, motivo: null };
}

let cache: { valor: ApiDescoberta; em: number } | null = null;
let emAndamento: Promise<ApiDescoberta> | null = null;

/** Esquece o `api.json` em memória (após falha de rede no túnel). */
export function invalidarDescoberta(): void {
  cache = null;
}

/**
 * Resolve a base da API. Em dev devolve a URL fixa; em produção lê `api.json`
 * (no máximo uma requisição por minuto, compartilhada entre chamadas simultâneas).
 */
export async function descobrirApi(opcoes: { forcar?: boolean } = {}): Promise<ApiDescoberta> {
  if (!DISCOVERY_URL) {
    const apiBase = semBarraFinal(API_URL_FIXA);
    return { apiBase, raiz: raizDaApi(apiBase), online: true, motivo: null, heartbeat: null, descoberta: false };
  }
  const agora = Date.now();
  if (!opcoes.forcar && cache && agora - cache.em < DESCOBERTA_TTL_MS) return cache.valor;
  if (emAndamento) return emAndamento;

  emAndamento = (async () => {
    let valor: ApiDescoberta;
    try {
      const resp = await fetch(comCacheBuster(DISCOVERY_URL), { cache: "no-store" });
      if (!resp.ok) throw new Error(String(resp.status));
      valor = avaliarApiJson((await resp.json()) as ApiJson, Date.now());
    } catch {
      valor = {
        apiBase: null,
        raiz: null,
        online: false,
        motivo: "não foi possível ler api.json",
        heartbeat: null,
        descoberta: true,
      };
    }
    cache = { valor, em: Date.now() };
    return valor;
  })();
  try {
    return await emAndamento;
  } finally {
    emAndamento = null;
  }
}
