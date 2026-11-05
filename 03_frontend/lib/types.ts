/**
 * Tipos TypeScript espelhando os schemas Pydantic do backend
 * (`04_backend/app/schemas/*.py`) e os contratos de API em
 * `00_docs/arquitetura.md` Seção 4. Somente DTOs — nenhuma regra de negócio.
 */

export type UUID = string;

/** Envelope de paginação genérico usado pelas listagens (`GET /edificacoes`, `/contratos`). */
export interface Paginated<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

/** Normaliza uma resposta de listagem que pode vir paginada ou como array simples. */
export function normalizePaginated<T>(data: Paginated<T> | T[]): Paginated<T> {
  if (Array.isArray(data)) {
    return { items: data, total: data.length, page: 1, page_size: data.length || 1 };
  }
  return data;
}

// ---------------------------------------------------------------------------
// Edificação (RF-01, BL-08)
// ---------------------------------------------------------------------------

export interface Edificacao {
  id: UUID;
  nome: string;
  endereco: string;
  cep?: string | null;
  tipologia?: string | null;
  sistema_construtivo?: string | null;
  descricao_pavimentos?: string | null;
  area_total_m2?: number | null;
  documentos_tecnicos?: Record<string, unknown> | null;
  created_at: string;
}

export type EdificacaoInput = Omit<Edificacao, "id" | "created_at">;

export interface EdificacaoDetail extends Edificacao {
  contratos?: Contrato[];
}

// ---------------------------------------------------------------------------
// Responsável (fiscal, RTE, responsável legal)
// ---------------------------------------------------------------------------

export interface Responsavel {
  id: UUID;
  nome: string;
  tipo: string;
  cpf_cnpj?: string | null;
  crea?: string | null;
  email?: string | null;
  telefone?: string | null;
}

// ---------------------------------------------------------------------------
// Contrato (RF-02, RF-12, RN-06, RN-09, BL-09)
// ---------------------------------------------------------------------------

export type TipoServico =
  | "RFO"
  | "LTIP"
  | "VISTORIA_CAUTELAR"
  | "VISTORIA_RESIDENCIAL"
  | "RFIP";

export type StatusContrato = "EM_ANDAMENTO" | "CONCLUIDO" | "CANCELADO";

export interface ContratoExecutor {
  id?: UUID;
  contrato_id?: UUID;
  responsavel_legal_id: UUID;
  rte_id?: UUID | null;
  razao_social: string;
  cnpj: string;
  endereco?: string | null;
  /** Obrigatória para toda executora do payload (RN-09, `ContratoExecutorNested`). */
  art_execucao: string;
}

export interface ContratoNbr {
  id?: UUID;
  contrato_id?: UUID;
  codigo_nbr: string;
  descricao?: string | null;
}

export interface Contrato {
  id: UUID;
  edificacao_id: UUID;
  fiscal_id: UUID;
  numero: string;
  tipo_servico: string;
  objeto?: string | null;
  data_inicio?: string | null;
  prazo_dias?: number | null;
  art_fiscalizacao?: string | null;
  observacoes_gerais?: string | null;
  status: string;
  created_at: string;
  /** Não retornado pela API — preenchido no cliente a partir da lista de edificações carregada. */
  edificacao_nome?: string;
}

export interface ContratoDetail extends Contrato {
  executores: ContratoExecutor[];
  nbrs: ContratoNbr[];
  inspecao?: Inspecao | null;
}

/** Payload de `POST /contratos` e `PUT /contratos/{id}` (`ContratoCreatePayload`/`ContratoUpdatePayload`). */
export interface ContratoInput {
  edificacao_id: UUID;
  fiscal_id: UUID;
  numero: string;
  tipo_servico: string;
  objeto?: string | null;
  data_inicio?: string | null;
  prazo_dias?: number | null;
  art_fiscalizacao: string;
  observacoes_gerais?: string | null;
  status: string;
  executores: ContratoExecutor[];
  nbrs: ContratoNbr[];
}

// ---------------------------------------------------------------------------
// Inspeção / Visita (RF-03, RN-01, RN-02, BL-10)
// ---------------------------------------------------------------------------

export interface Inspecao {
  id: UUID;
  contrato_id: UUID;
  tipo: string;
  status: string;
  created_at: string;
  visitas?: Visita[];
  contrato?: Contrato;
}

export interface VisitaMaoObra {
  id: UUID;
  visita_id: UUID;
  funcao: string;
  quantidade: number;
}

export interface VisitaMedicao {
  id: UUID;
  visita_id: UUID;
  descricao: string;
  quantidade: number;
  unidade: string;
}

export interface Visita {
  id: UUID;
  inspecao_id: UUID;
  data: string;
  servicos_executados?: string | null;
  observacoes?: string | null;
  seq_numero: number;
  mao_obra?: VisitaMaoObra[];
  medicoes?: VisitaMedicao[];
  fotos?: Foto[];
}

/** Payload de `POST /inspecoes/{id}/visitas` e `PUT /visitas/{id}` — `inspecao_id`/`seq_numero` não entram no corpo. */
export interface VisitaInput {
  data: string;
  servicos_executados: string;
  observacoes?: string | null;
}

// ---------------------------------------------------------------------------
// Foto (RF-05, RNF-02 parcial, BL-11)
// ---------------------------------------------------------------------------

/**
 * Valores aceitos em `origem` ao vincular foto (`POST /visitas/{id}/fotos`, `POST /ocorrencias/{id}/fotos`).
 * Único tipo de origem do frontend — o editor usa rótulos internos e os converte só na chamada ao backend.
 */
export type OrigemFoto = "upload_manual" | "lightshot" | "clipboard";

export interface Foto {
  id: UUID;
  ocorrencia_id?: UUID | null;
  visita_id?: UUID | null;
  storage_key: string;
  url_publica?: string | null;
  legenda?: string | null;
  origem: string;
  ordem?: number | null;
  created_at: string;
}

/** Resposta do upload bruto (`/fotos/upload` e `/fotos/upload-clipboard`), antes da vinculação. */
export interface FotoUploadResult {
  storage_key: string;
  url: string;
}

/** Payload de `POST /ocorrencias/{id}/fotos` e `POST /visitas/{id}/fotos` — vincula um upload já feito. */
export interface FotoLinkInput {
  storage_key: string;
  url_publica?: string | null;
  legenda?: string | null;
  origem: OrigemFoto;
  ordem?: number | null;
}

// ---------------------------------------------------------------------------
// Gabarito de Sistemas Prediais (RF-10, BL-05) — consumido pelo formulário de Ocorrência
// ---------------------------------------------------------------------------

export interface Subsistema {
  id: UUID;
  sistema_id: UUID;
  nome: string;
  ordem: number;
}

export interface SistemaPredial {
  id: UUID;
  nome: string;
  ordem: number;
}

export interface SistemaPredialComSubsistemas extends SistemaPredial {
  subsistemas: Subsistema[];
}

export interface TipoAnomalia {
  id: UUID;
  nome: string;
  ordem: number;
}

export interface TipoFalha {
  id: UUID;
  nome: string;
  ordem: number;
}

export interface Localizacao {
  id: UUID;
  nome: string;
  ordem: number;
}

// ---------------------------------------------------------------------------
// Ocorrência (RF-04, RN-03, RN-05, RN-10, BL-14)
// ---------------------------------------------------------------------------

export interface Ocorrencia {
  id: UUID;
  inspecao_id: UUID;
  sistema_id: UUID;
  subsistema_id?: UUID | null;
  localizacao?: string | null;
  situacao: string;
  classificacao: string;
  tipo_anomalia?: string | null;
  tipo_falha?: string | null;
  grau_risco?: string | null;
  /** Informada manualmente (0-5) até a automação por Grau de Risco (RN-04) ser destravada na BL-15. */
  prioridade?: number | null;
  descricao?: string | null;
  gut_gravidade?: number | null;
  gut_urgencia?: number | null;
  gut_tendencia?: number | null;
  seq_numero: number;
  fotos?: Foto[];
}

export type OcorrenciaInput = Omit<Ocorrencia, "id" | "seq_numero" | "fotos">;

// ---------------------------------------------------------------------------
// Dashboard de saúde por Edificação/Sistema Predial (RF-07, BL-16)
// ---------------------------------------------------------------------------

export interface DashboardConformidadePorSistema {
  sistema_id: UUID;
  sistema_nome: string;
  conforme: number;
  nao_conforme: number;
  total: number;
}

export interface DashboardGrauRiscoPorSistema {
  sistema_id: UUID;
  sistema_nome: string;
  minimo: number;
  medio: number;
  critico: number;
}

export interface DashboardGravidadePorSubsistema {
  subsistema_id: UUID;
  subsistema_nome: string;
  sistema_nome?: string;
  media_gravidade: number;
}

/** Resposta de `GET /edificacoes/{id}/dashboard` (RF-07, cache Redis ~60s, ver arquitetura.md Seção 10.4). */
export interface DashboardEdificacao {
  edificacao_id: UUID;
  edificacao_nome?: string;
  conformidade_por_sistema: DashboardConformidadePorSistema[];
  grau_risco_por_sistema: DashboardGrauRiscoPorSistema[];
  gravidade_por_subsistema: DashboardGravidadePorSubsistema[];
}

// ---------------------------------------------------------------------------
// Portal do Cliente (RF-13, RN-14, BL-32/BL-33) — somente leitura
// ---------------------------------------------------------------------------

export interface PortalVisitaResumo {
  id: UUID;
  seq_numero: number;
  data: string;
  servicos_executados?: string | null;
  total_fotos: number;
}

export interface PortalOcorrenciaResumo {
  id: UUID;
  seq_numero: number;
  sistema_nome?: string | null;
  subsistema_nome?: string | null;
  localizacao?: string | null;
  situacao: string;
  grau_risco?: string | null;
  prioridade?: number | null;
  descricao?: string | null;
}

export interface PortalContratoAcompanhamento {
  contrato_id: UUID;
  numero: string;
  tipo_servico: string;
  status: string;
  data_inicio?: string | null;
  inspecao_id?: UUID | null;
  inspecao_status?: string | null;
  total_visitas: number;
  total_ocorrencias: number;
  ocorrencias_por_grau_risco: { minimo: number; medio: number; critico: number };
  visitas: PortalVisitaResumo[];
  ocorrencias: PortalOcorrenciaResumo[];
}

/** Resposta de `GET /portal/edificacoes/{id}/acompanhamento`. */
export interface PortalAcompanhamento {
  edificacao_id: UUID;
  edificacao_nome?: string | null;
  contratos: PortalContratoAcompanhamento[];
}

/** Item de `GET /portal/relatorios` (RF-11/RF-13). */
export interface PortalRelatorio {
  id: UUID;
  versao: string;
  tipo: string;
  status: string;
  emitido_em?: string | null;
  tem_pdf: boolean;
  tem_docx: boolean;
  inspecao_id: UUID;
  contrato_id: UUID;
  contrato_numero: string;
  edificacao_id: UUID;
  edificacao_nome?: string | null;
}

/** Resposta de `GET /portal/relatorios/{id}/download/{formato}` — URL pré-assinada. */
export interface PortalDownload {
  relatorio_id: UUID;
  formato: string;
  url: string;
  expira_em_segundos: number;
}
