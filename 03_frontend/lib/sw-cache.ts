/**
 * Regras puras do cache de leitura do Service Worker (DEC-26, ADR-03/ADR-15).
 *
 * Sem acesso a `self`/DOM: é a fonte testável (`sw-cache.test.ts`). O arquivo
 * `public/sw.js` não pode importar TypeScript e DUPLICA as constantes abaixo;
 * o teste confere que os padrões de `sw.js` e deste módulo continuam idênticos.
 *
 * Política: só GET de dados de leitura de baixa volatilidade. Escritas nunca
 * passam pelo cache (falham com o erro nativo de rede, sem fila local).
 */

export type CacheKind = "mestre" | "contratos";

export interface CacheRule {
  kind: CacheKind;
  /** Fonte de uma RegExp aplicada ao `pathname` (independente da origem da API). */
  pattern: string;
  /** Tempo máximo (ms) em que uma entrada ainda pode ser servida do cache. */
  ttlMs: number;
  /** Dado dependente do usuário: a chave de cache inclui o fingerprint do token. */
  perUser: boolean;
}

/** Dados mestre (gabarito) são públicos na API e mudam raramente: 24 h. */
export const MESTRE_TTL_MS = 24 * 60 * 60 * 1000;
/** Contratos dependem do token (Authorization): cache curto, 5 min. */
export const CONTRATOS_TTL_MS = 5 * 60 * 1000;

export const ALLOWLIST: readonly CacheRule[] = [
  { kind: "mestre", pattern: "^/api/v1/sistemas-prediais/?$", ttlMs: MESTRE_TTL_MS, perUser: false },
  {
    kind: "mestre",
    pattern: "^/api/v1/gabarito/(tipos-anomalia|tipos-falha|localizacoes)/?$",
    ttlMs: MESTRE_TTL_MS,
    perUser: false,
  },
  { kind: "contratos", pattern: "^/api/v1/contratos/?$", ttlMs: CONTRATOS_TTL_MS, perUser: true },
  { kind: "contratos", pattern: "^/api/v1/contratos/[0-9]+/?$", ttlMs: CONTRATOS_TTL_MS, perUser: true },
];

/** Caminhos que nunca entram no cache, mesmo que casassem a allowlist. */
export const NEVER_CACHE_PATTERNS: readonly string[] = [
  "/auth(/|$)",
  "/portal(/|$)",
  "/fotos?(/|$)",
  "/download",
  "/relatorios?(/|$)",
  "/documentos?(/|$)",
  "/upload",
];

export interface RequestInfo {
  method: string;
  url: string;
}

function pathnameOf(url: string): string | null {
  try {
    const u = new URL(url);
    if (u.protocol !== "http:" && u.protocol !== "https:") return null;
    return u.pathname;
  } catch {
    return null;
  }
}

export function isNeverCacheable(url: string): boolean {
  const path = pathnameOf(url);
  if (path === null) return true;
  return NEVER_CACHE_PATTERNS.some((p) => new RegExp(p).test(path));
}

/** Regra da allowlist aplicável à requisição, ou `null` se não for cacheável. */
export function matchCacheRule(req: RequestInfo): CacheRule | null {
  if (req.method.toUpperCase() !== "GET") return null;
  if (isNeverCacheable(req.url)) return null;
  const path = pathnameOf(req.url);
  if (path === null) return null;
  return ALLOWLIST.find((r) => new RegExp(r.pattern).test(path)) ?? null;
}

export function isCacheableRequest(req: RequestInfo): boolean {
  return matchCacheRule(req) !== null;
}

/** Só respostas 200 e sem `no-store`/`private` podem ser gravadas no cache. */
export function isCacheableResponse(status: number, cacheControl: string | null): boolean {
  if (status !== 200) return false;
  return !/\b(no-store|private)\b/i.test(cacheControl ?? "");
}

/** A entrada ainda está dentro do TTL da regra? */
export function isFresh(storedAtMs: number, nowMs: number, ttlMs: number): boolean {
  return nowMs - storedAtMs >= 0 && nowMs - storedAtMs < ttlMs;
}

/**
 * URL usada como chave de cache. Para dados por usuário, anexa o fingerprint do
 * token (hash, nunca o token) para que outro usuário no mesmo navegador não receba
 * a resposta alheia. Sem Authorization em dado por usuário, devolve `null` (não cachear).
 */
export function cacheKeyUrl(rule: CacheRule, url: string, authFingerprint: string | null): string | null {
  if (!rule.perUser) return url;
  if (!authFingerprint) return null;
  const u = new URL(url);
  u.searchParams.set("__sw_u", authFingerprint);
  return u.toString();
}
