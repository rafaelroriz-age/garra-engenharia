/**
 * Modo leitura com snapshot cifrado (DEC-57 P5, T83).
 *
 * PC do dono desligado ⇒ o site estático responde os GETs de `apiFetch` a partir
 * de `snapshot.enc` (gerado pelo T81, publicado pelo T82 na branch `snapshot`),
 * decifrado no navegador com WebCrypto. Escritas lançam erro tipado.
 *
 * Formato (00_docs/backlog-auto/snapshot-cifrado.md §3): envelope JSON com
 * PBKDF2-SHA256 (600 000 iterações, salt 16 B) → AES-256-GCM (iv 12 B, tag no fim
 * de `ct`, sem AAD); texto claro = gzip de `{"gerado_em", "rotas": {chave: corpo}}`.
 * Chave da rota = `"/api/v1" + path` exatamente como a tela chama `api.get(path)`.
 *
 * Este módulo não importa nada com alias `@/` (testável com `node --test`):
 * o transporte (baixar o envelope, testar o servidor) é injetado por
 * `configurarModoLeitura()` em `lib/api-client.ts`.
 */

import { useSyncExternalStore } from "react";

// ---------------------------------------------------------------------------
// Cifra
// ---------------------------------------------------------------------------

/** Envelope público de `snapshot.enc`. */
export interface EnvelopeSnapshot {
  v: number;
  kdf: { alg: string; iter: number; salt: string };
  cifra?: string;
  iv: string;
  ct: string;
  gerado_em?: string;
}

export type RotasSnapshot = Record<string, unknown>;

export interface SnapshotDecifrado {
  gerado_em: string | null;
  rotas: RotasSnapshot;
}

/** Senha errada ou arquivo adulterado (falha da tag GCM). */
export class SenhaSnapshotInvalida extends Error {
  constructor() {
    super("Senha incorreta ou arquivo de leitura corrompido.");
    this.name = "SenhaSnapshotInvalida";
  }
}

/** Envelope com versão/algoritmo que este front não sabe abrir. */
export class FormatoSnapshotInvalido extends Error {
  constructor(motivo: string) {
    super(`Formato de snapshot não suportado: ${motivo}`);
    this.name = "FormatoSnapshotInvalido";
  }
}

function b64(s: string): Uint8Array<ArrayBuffer> {
  const bin = atob(s);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

function validarEnvelope(env: EnvelopeSnapshot): void {
  if (!env || typeof env !== "object") throw new FormatoSnapshotInvalido("envelope ausente");
  if (env.v !== 1) throw new FormatoSnapshotInvalido(`versão ${String(env.v)}`);
  if (env.kdf?.alg !== "PBKDF2-SHA256") throw new FormatoSnapshotInvalido(`kdf ${String(env.kdf?.alg)}`);
  if (env.cifra !== undefined && env.cifra !== "AES-256-GCM") throw new FormatoSnapshotInvalido(`cifra ${env.cifra}`);
  if (!Number.isInteger(env.kdf.iter) || env.kdf.iter < 1) throw new FormatoSnapshotInvalido("iterações");
}

/** Decifra e descomprime o snapshot. Senha errada ⇒ `SenhaSnapshotInvalida`. */
export async function decifrarSnapshot(env: EnvelopeSnapshot, senha: string): Promise<SnapshotDecifrado> {
  validarEnvelope(env);
  const subtle = globalThis.crypto.subtle;
  const base = await subtle.importKey("raw", new TextEncoder().encode(senha), "PBKDF2", false, ["deriveKey"]);
  const chave = await subtle.deriveKey(
    { name: "PBKDF2", hash: "SHA-256", salt: b64(env.kdf.salt), iterations: env.kdf.iter },
    base,
    { name: "AES-GCM", length: 256 },
    false,
    ["decrypt"],
  );
  let gz: ArrayBuffer;
  try {
    gz = await subtle.decrypt({ name: "AES-GCM", iv: b64(env.iv) }, chave, b64(env.ct));
  } catch {
    throw new SenhaSnapshotInvalida();
  }
  const fluxo = new Blob([gz]).stream().pipeThrough(new DecompressionStream("gzip"));
  const texto = await new Response(fluxo).text();
  const dados = JSON.parse(texto) as { gerado_em?: string; rotas?: RotasSnapshot };
  return { gerado_em: dados.gerado_em ?? env.gerado_em ?? null, rotas: dados.rotas ?? {} };
}

// ---------------------------------------------------------------------------
// Resolução de rotas
// ---------------------------------------------------------------------------

/** Chave da rota no snapshot: `"/api/v1" + path` (T81 §4). */
export function chaveRota(path: string): string {
  return `/api/v1${path.startsWith("/") ? path : `/${path}`}`;
}

const PARAMS_PAGINACAO = new Set(["page", "page_size"]);
/** Filtros de texto livre: casam por "contém", e entre si com OU (a tela manda nome e endereco iguais). */
const PARAMS_TEXTO = new Set(["nome", "endereco", "q", "busca"]);

type Registro = Record<string, unknown>;

function ehPagina(v: unknown): v is { items: Registro[]; page_size?: number } {
  return !!v && typeof v === "object" && Array.isArray((v as { items?: unknown }).items);
}

function normalizar(s: string): string {
  return s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
}

function separar(chave: string): [string, URLSearchParams] {
  const i = chave.indexOf("?");
  return i < 0 ? [chave, new URLSearchParams()] : [chave.slice(0, i), new URLSearchParams(chave.slice(i + 1))];
}

/**
 * Corpo da resposta para a chave, ou `undefined` se o snapshot não tem como responder.
 *
 * 1. Chave exata.
 * 2. Senão (filtros imprevisíveis, P-T81-2): junta a lista sem filtro do mesmo caminho
 *    (array direto ou todas as páginas `?page&page_size`), filtra localmente e pagina.
 */
export function resolverRota(rotas: RotasSnapshot, chave: string): unknown {
  if (Object.prototype.hasOwnProperty.call(rotas, chave)) return rotas[chave];

  const [caminho, params] = separar(chave);
  let itens: Registro[] | null = null;
  let paginado = false;
  let pageSizePadrao: number | null = null;

  const direto = rotas[caminho];
  if (Array.isArray(direto)) {
    itens = direto as Registro[];
  } else {
    const vistos = new Map<string, Registro>();
    const semId: Registro[] = [];
    for (const [k, v] of Object.entries(rotas)) {
      const [c, p] = separar(k);
      if (c !== caminho || !ehPagina(v)) continue;
      if (Array.from(p.keys()).some((nome) => !PARAMS_PAGINACAO.has(nome))) continue;
      paginado = true;
      if (pageSizePadrao === null && typeof v.page_size === "number") pageSizePadrao = v.page_size;
      for (const item of v.items) {
        const id = item && typeof item === "object" ? item.id : undefined;
        if (id === undefined || id === null) semId.push(item);
        else if (!vistos.has(String(id))) vistos.set(String(id), item);
      }
    }
    if (paginado) itens = Array.from(vistos.values()).concat(semId);
  }
  if (!itens) return undefined;

  const filtrosTexto: [string, string][] = [];
  const filtrosExatos: [string, string][] = [];
  params.forEach((v, k) => {
    if (PARAMS_PAGINACAO.has(k)) return;
    (PARAMS_TEXTO.has(k) ? filtrosTexto : filtrosExatos).push([k, v]);
  });
  const filtrados = itens.filter((item) => {
    // Filtro que o item nem tem como campo é ignorado (não zera a lista).
    const exatos = filtrosExatos.every(([k, v]) => !(k in item) || String(item[k]) === v);
    if (!exatos) return false;
    const textos = filtrosTexto.filter(([k]) => k in item);
    if (textos.length === 0) return true;
    return textos.some(([k, v]) => normalizar(String(item[k] ?? "")).includes(normalizar(v)));
  });

  if (!paginado && !params.has("page")) return filtrados;
  const page = Math.max(1, Number(params.get("page") ?? 1) || 1);
  const pageSize = Math.max(1, Number(params.get("page_size") ?? pageSizePadrao ?? filtrados.length) || 1);
  return {
    items: filtrados.slice((page - 1) * pageSize, page * pageSize),
    total: filtrados.length,
    page,
    page_size: pageSize,
  };
}

// ---------------------------------------------------------------------------
// Erro tipado
// ---------------------------------------------------------------------------

export const MENSAGEM_MODO_LEITURA = "Servidor desligado — modo leitura";

/** Motivo pelo qual o modo leitura não pôde atender a requisição. */
export type MotivoErroModoLeitura = "escrita" | "bloqueado" | "sem-dados" | "indisponivel";

/** Erro do modo leitura (convertido em `ModoLeituraError`/`ApiError` em `api-client`). */
export class ModoLeituraErro extends Error {
  readonly motivo: MotivoErroModoLeitura;
  constructor(motivo: MotivoErroModoLeitura, detalhe: string) {
    super(detalhe);
    this.name = "ModoLeituraErro";
    this.motivo = motivo;
  }
}

// ---------------------------------------------------------------------------
// Estado global (store simples + evento)
// ---------------------------------------------------------------------------

export interface EstadoModoLeitura {
  /** Servidor indisponível: o site responde pelo snapshot e bloqueia gravações. */
  ativo: boolean;
  motivo: string | null;
  /** Data de geração do snapshot (vem em claro no envelope). */
  geradoEm: string | null;
  /** Snapshot decifrado e pronto para responder. */
  desbloqueado: boolean;
  /** O diálogo de senha deve ficar aberto. */
  pedindoSenha: boolean;
  carregando: boolean;
  erro: string | null;
}

const ESTADO_INICIAL: EstadoModoLeitura = {
  ativo: false,
  motivo: null,
  geradoEm: null,
  desbloqueado: false,
  pedindoSenha: false,
  carregando: false,
  erro: null,
};

/** Evento `window` disparado a cada mudança (`detail` = estado). */
export const MODO_LEITURA_EVENTO = "garra:modo-leitura";
/** Intervalo entre tentativas de reconectar ao servidor. */
export const RECONEXAO_MS = 60 * 1000;
const SENHA_SESSAO_KEY = "garra:snapshot_senha";

let estado: EstadoModoLeitura = ESTADO_INICIAL;
const ouvintes = new Set<() => void>();
let envelope: EnvelopeSnapshot | null = null;
let rotas: RotasSnapshot | null = null;
let timer: ReturnType<typeof setInterval> | null = null;
let espera: { resolve: (r: RotasSnapshot) => void; reject: (e: Error) => void }[] = [];

export interface DependenciasModoLeitura {
  /** Baixa e faz o parse de `snapshot.enc`. */
  baixarEnvelope: () => Promise<EnvelopeSnapshot>;
  /** `true` quando o servidor voltou (api.json online + /health ok). */
  servidorVoltou: () => Promise<boolean>;
}
let deps: DependenciasModoLeitura | null = null;

export function configurarModoLeitura(d: DependenciasModoLeitura): void {
  deps = d;
}

function definir(parcial: Partial<EstadoModoLeitura>): void {
  estado = { ...estado, ...parcial };
  ouvintes.forEach((f) => f());
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent(MODO_LEITURA_EVENTO, { detail: estado }));
  }
}

export function obterEstadoModoLeitura(): EstadoModoLeitura {
  return estado;
}

export function assinarModoLeitura(fn: () => void): () => void {
  ouvintes.add(fn);
  return () => {
    ouvintes.delete(fn);
  };
}

function sessao(): Storage | null {
  try {
    return typeof window !== "undefined" ? window.sessionStorage : null;
  } catch {
    return null;
  }
}

function rejeitarEspera(erro: Error): void {
  const pendentes = espera;
  espera = [];
  pendentes.forEach((p) => p.reject(erro));
}

function iniciarReconexao(): void {
  if (timer !== null || typeof setInterval === "undefined") return;
  timer = setInterval(() => {
    void tentarReconectar();
  }, RECONEXAO_MS);
}

/** Uma tentativa de voltar ao servidor; sai do modo leitura se ele respondeu. */
export async function tentarReconectar(): Promise<boolean> {
  if (!estado.ativo || !deps) return false;
  try {
    if (await deps.servidorVoltou()) {
      sairModoLeitura();
      return true;
    }
  } catch {
    // segue em modo leitura
  }
  return false;
}

async function baixar(): Promise<boolean> {
  if (envelope) return true;
  if (!deps) {
    definir({ carregando: false, erro: "Modo leitura não configurado." });
    return false;
  }
  definir({ carregando: true, erro: null });
  try {
    envelope = await deps.baixarEnvelope();
    definir({ geradoEm: envelope.gerado_em ?? null });
    return true;
  } catch {
    definir({ carregando: false, erro: "Não foi possível baixar os dados de leitura. Verifique a internet." });
    rejeitarEspera(new ModoLeituraErro("indisponivel", "Os dados de leitura não puderam ser baixados."));
    return false;
  }
}

/** Liga o modo leitura (idempotente): baixa o envelope e usa a senha da sessão, se houver. */
export async function entrarModoLeitura(motivo: string): Promise<void> {
  if (estado.ativo) return;
  definir({ ...ESTADO_INICIAL, ativo: true, motivo, carregando: true });
  iniciarReconexao();
  if (!(await baixar())) return;
  const salva = sessao()?.getItem(SENHA_SESSAO_KEY);
  if (salva && (await informarSenha(salva))) return;
  if (estado.ativo) definir({ carregando: false, pedindoSenha: true, erro: salva ? null : estado.erro });
}

/** Tenta abrir o snapshot com a senha da equipe. Guarda a senha só em `sessionStorage`. */
export async function informarSenha(senha: string): Promise<boolean> {
  if (!estado.ativo) return false;
  if (!(await baixar()) || !envelope) return false;
  definir({ carregando: true, erro: null });
  try {
    const snap = await decifrarSnapshot(envelope, senha);
    if (!estado.ativo) return false;
    rotas = snap.rotas;
    sessao()?.setItem(SENHA_SESSAO_KEY, senha);
    definir({ desbloqueado: true, pedindoSenha: false, carregando: false, geradoEm: snap.gerado_em });
    const pendentes = espera;
    espera = [];
    pendentes.forEach((p) => p.resolve(snap.rotas));
    return true;
  } catch (e) {
    if (e instanceof SenhaSnapshotInvalida) sessao()?.removeItem(SENHA_SESSAO_KEY);
    definir({
      carregando: false,
      erro: e instanceof SenhaSnapshotInvalida ? "Senha incorreta." : "Não foi possível abrir os dados de leitura.",
    });
    return false;
  }
}

/** Reabre o diálogo de senha (botão da faixa). */
export function pedirSenha(): void {
  if (!estado.ativo || estado.desbloqueado) return;
  definir({ pedindoSenha: true });
  if (!envelope) void baixar().then((ok) => ok && definir({ carregando: false }));
}

/** Fecha o diálogo sem senha: as leituras pendentes falham com erro claro. */
export function cancelarSenha(): void {
  definir({ pedindoSenha: false, erro: null });
  rejeitarEspera(new ModoLeituraErro("bloqueado", "Informe a senha da equipe para ver os dados em modo leitura."));
}

/** Desliga o modo leitura (servidor de volta). Descarta o snapshot da memória. */
export function sairModoLeitura(): void {
  if (timer !== null) clearInterval(timer);
  timer = null;
  envelope = null;
  rotas = null;
  rejeitarEspera(new ModoLeituraErro("indisponivel", "O servidor voltou; recarregue a tela."));
  definir(ESTADO_INICIAL);
}

/** Rotas decifradas; espera a senha se o diálogo estiver aberto ou o download em curso. */
export function aguardarRotas(): Promise<RotasSnapshot> {
  if (rotas && estado.desbloqueado) return Promise.resolve(rotas);
  if (!estado.ativo) return Promise.reject(new ModoLeituraErro("indisponivel", "Modo leitura inativo."));
  if (!estado.pedindoSenha && !estado.carregando) {
    return Promise.reject(
      new ModoLeituraErro("bloqueado", estado.erro ?? "Informe a senha da equipe para ver os dados em modo leitura."),
    );
  }
  return new Promise((resolve, reject) => espera.push({ resolve, reject }));
}

/**
 * Resposta do modo leitura para `apiFetch`: GET pelo mapa de rotas; qualquer outro
 * método lança `ModoLeituraErro("escrita")`.
 */
export async function responderModoLeitura(path: string, metodo: string): Promise<unknown> {
  if (metodo.toUpperCase() !== "GET") {
    throw new ModoLeituraErro(
      "escrita",
      `${MENSAGEM_MODO_LEITURA}: gravações voltam quando o servidor estiver ligado.`,
    );
  }
  const mapa = await aguardarRotas();
  const corpo = resolverRota(mapa, chaveRota(path));
  if (corpo === undefined) {
    throw new ModoLeituraErro("sem-dados", "Este dado não está disponível no modo leitura (servidor desligado).");
  }
  return corpo;
}

const ESTADO_SERVIDOR: EstadoModoLeitura = ESTADO_INICIAL;

/**
 * Estado do modo leitura para componentes. `bloquearEscrita` serve para
 * desabilitar botões de criar/editar/excluir/upload/emitir.
 */
export function useModoLeitura(): EstadoModoLeitura & { bloquearEscrita: boolean } {
  const atual = useSyncExternalStore(assinarModoLeitura, obterEstadoModoLeitura, () => ESTADO_SERVIDOR);
  return { ...atual, bloquearEscrita: atual.ativo };
}

/** Texto do placeholder de imagens e downloads em modo leitura. */
export const TEXTO_INDISPONIVEL = "Disponível com o servidor ligado";
