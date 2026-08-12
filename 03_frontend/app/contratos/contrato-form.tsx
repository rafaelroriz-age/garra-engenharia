"use client";

import { useEffect, useState } from "react";
import { Plus, Trash2 } from "lucide-react";

import type { ContratoDetail, ContratoExecutor, ContratoInput, ContratoNbr, Edificacao } from "@/lib/types";
import { normalizePaginated, type Paginated } from "@/lib/types";
import { api, ApiError } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { ApiErrorAlert } from "@/components/api-error-alert";

const TIPOS_SERVICO = [
  { value: "RFO", label: "Relatório de Fiscalização de Obra (RFO)" },
  { value: "LTIP", label: "Laudo Técnico de Inspeção Predial (LTIP)" },
  { value: "VISTORIA_CAUTELAR", label: "Vistoria Cautelar de Recebimento" },
  { value: "VISTORIA_RESIDENCIAL", label: "Vistoria de Imóvel Residencial" },
  { value: "RFIP", label: "Relatório Fotográfico de Inspeção Predial" },
];

const STATUS_OPTIONS = [
  { value: "em_andamento", label: "Em andamento" },
  { value: "concluido", label: "Concluído" },
  { value: "cancelado", label: "Cancelado" },
];

function emptyExecutor(): ContratoExecutor {
  return { responsavel_legal_id: "", rte_id: "", razao_social: "", cnpj: "", endereco: "", art_execucao: "" };
}

function emptyNbr(): ContratoNbr {
  return { codigo_nbr: "", descricao: "" };
}

function onlyDigits(value: string): string {
  return value.replace(/\D/g, "");
}

interface ContratoFormProps {
  initialValue?: ContratoDetail;
  submitLabel: string;
  onSubmit: (input: ContratoInput) => Promise<void>;
  onCancel?: () => void;
}

/**
 * Formulário de criação/edição de Contrato (RF-02, RF-12, RN-06, RN-09, BL-09),
 * com arrays dinâmicos de empresas executoras e NBRs aplicáveis.
 *
 * Nota: `fiscal_id`, `responsavel_legal_id` e `rte_id` referenciam a entidade
 * `Responsavel`, para a qual `00_docs/arquitetura.md` Seção 4 ainda não define
 * um endpoint de listagem — por isso são preenchidos como UUID em texto.
 * Recomenda-se registrar `GET /responsaveis` como pendência de backend para
 * substituir esses campos por um seletor de busca.
 */
export function ContratoForm({ initialValue, submitLabel, onSubmit, onCancel }: ContratoFormProps) {
  const [edificacoes, setEdificacoes] = useState<Edificacao[]>([]);
  const [edificacaoId, setEdificacaoId] = useState(initialValue?.edificacao_id ?? "");
  const [fiscalId, setFiscalId] = useState(initialValue?.fiscal_id ?? "");
  const [numero, setNumero] = useState(initialValue?.numero ?? "");
  const [tipoServico, setTipoServico] = useState(initialValue?.tipo_servico ?? "RFO");
  const [objeto, setObjeto] = useState(initialValue?.objeto ?? "");
  const [dataInicio, setDataInicio] = useState(initialValue?.data_inicio ?? "");
  const [prazoDias, setPrazoDias] = useState(initialValue?.prazo_dias?.toString() ?? "");
  const [artFiscalizacao, setArtFiscalizacao] = useState(initialValue?.art_fiscalizacao ?? "");
  const [observacoes, setObservacoes] = useState(initialValue?.observacoes_gerais ?? "");
  const [status, setStatus] = useState(initialValue?.status ?? "em_andamento");
  const [executores, setExecutores] = useState<ContratoExecutor[]>(
    initialValue?.executores?.length ? initialValue.executores : [emptyExecutor()]
  );
  const [nbrs, setNbrs] = useState<ContratoNbr[]>(initialValue?.nbrs?.length ? initialValue.nbrs : [emptyNbr()]);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<ApiError | Error | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    api
      .get<Paginated<Edificacao> | Edificacao[]>("/edificacoes?page=1&page_size=100")
      .then((response) => setEdificacoes(normalizePaginated(response).items))
      .catch(() => setEdificacoes([]));
  }, []);

  function updateExecutor(index: number, patch: Partial<ContratoExecutor>) {
    setExecutores((prev) => prev.map((item, i) => (i === index ? { ...item, ...patch } : item)));
  }

  function updateNbr(index: number, patch: Partial<ContratoNbr>) {
    setNbrs((prev) => prev.map((item, i) => (i === index ? { ...item, ...patch } : item)));
  }

  function validate(): boolean {
    const errors: Record<string, string> = {};
    if (!edificacaoId) errors.edificacao_id = "Selecione a edificação.";
    if (!fiscalId.trim()) errors.fiscal_id = "Informe o identificador do engenheiro fiscal.";
    if (!numero.trim()) errors.numero = "Informe o número do contrato.";
    if (!artFiscalizacao.trim()) errors.art_fiscalizacao = "ART de Fiscalização é obrigatória (RN-09).";

    executores.forEach((executor, index) => {
      if (!executor.razao_social.trim()) errors[`executor.${index}.razao_social`] = "Informe a razão social.";
      if (onlyDigits(executor.cnpj).length !== 14) errors[`executor.${index}.cnpj`] = "CNPJ deve ter 14 dígitos.";
      if (!executor.responsavel_legal_id.trim())
        errors[`executor.${index}.responsavel_legal_id`] = "Informe o responsável legal.";
      if (!executor.art_execucao.trim())
        errors[`executor.${index}.art_execucao`] = "ART de Execução é obrigatória para cada executora.";
    });

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    if (!validate()) return;

    setIsSubmitting(true);
    try {
      await onSubmit({
        edificacao_id: edificacaoId,
        fiscal_id: fiscalId.trim(),
        numero: numero.trim(),
        tipo_servico: tipoServico,
        objeto: objeto.trim() || null,
        data_inicio: dataInicio || null,
        prazo_dias: prazoDias ? Number(prazoDias) : null,
        art_fiscalizacao: artFiscalizacao.trim(),
        observacoes_gerais: observacoes.trim() || null,
        status,
        executores: executores
          .filter((executor) => executor.razao_social.trim() || executor.cnpj.trim())
          .map((executor) => ({
            ...executor,
            // `rte_id` é opcional (RN-06) — o backend valida como UUID-ou-null e
            // rejeita string vazia (`""`), que é o valor default do formulário
            // quando o campo não é preenchido.
            rte_id: executor.rte_id?.trim() ? executor.rte_id.trim() : null,
            endereco: executor.endereco?.trim() || null,
          })),
        nbrs: nbrs.filter((nbr) => nbr.codigo_nbr.trim()),
      });
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err);
        const apiFieldErrors: Record<string, string> = {};
        err.errors.forEach((fieldError) => {
          apiFieldErrors[fieldError.field] = fieldError.message;
        });
        setFieldErrors((prev) => ({ ...prev, ...apiFieldErrors }));
      } else {
        setError(err instanceof Error ? err : new Error("Falha ao salvar contrato."));
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6" noValidate>
      <ApiErrorAlert error={error} />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="space-y-1.5">
          <Label htmlFor="edificacao_id" required>
            Edificação
          </Label>
          <Select
            id="edificacao_id"
            value={edificacaoId}
            onChange={(event) => setEdificacaoId(event.target.value)}
            aria-invalid={Boolean(fieldErrors.edificacao_id)}
            required
          >
            <option value="">Selecione...</option>
            {edificacoes.map((edificacao) => (
              <option key={edificacao.id} value={edificacao.id}>
                {edificacao.nome}
              </option>
            ))}
          </Select>
          {fieldErrors.edificacao_id ? <p className="text-xs text-destructive">{fieldErrors.edificacao_id}</p> : null}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="numero" required>
            Número do contrato
          </Label>
          <Input
            id="numero"
            value={numero}
            onChange={(event) => setNumero(event.target.value)}
            aria-invalid={Boolean(fieldErrors.numero)}
            required
          />
          {fieldErrors.numero ? <p className="text-xs text-destructive">{fieldErrors.numero}</p> : null}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="tipo_servico" required>
            Tipo de serviço
          </Label>
          <Select id="tipo_servico" value={tipoServico} onChange={(event) => setTipoServico(event.target.value)}>
            {TIPOS_SERVICO.map((tipo) => (
              <option key={tipo.value} value={tipo.value}>
                {tipo.label}
              </option>
            ))}
          </Select>
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="status">Status</Label>
          <Select id="status" value={status} onChange={(event) => setStatus(event.target.value)}>
            {STATUS_OPTIONS.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </Select>
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="fiscal_id" required>
            Engenheiro fiscal (ID)
          </Label>
          <Input
            id="fiscal_id"
            value={fiscalId}
            onChange={(event) => setFiscalId(event.target.value)}
            placeholder="UUID do responsável"
            aria-invalid={Boolean(fieldErrors.fiscal_id)}
            required
          />
          {fieldErrors.fiscal_id ? <p className="text-xs text-destructive">{fieldErrors.fiscal_id}</p> : null}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="art_fiscalizacao" required>
            ART de Fiscalização
          </Label>
          <Input
            id="art_fiscalizacao"
            value={artFiscalizacao}
            onChange={(event) => setArtFiscalizacao(event.target.value)}
            aria-invalid={Boolean(fieldErrors.art_fiscalizacao)}
            required
          />
          {fieldErrors.art_fiscalizacao ? (
            <p className="text-xs text-destructive">{fieldErrors.art_fiscalizacao}</p>
          ) : null}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="data_inicio">Data de início</Label>
          <Input
            id="data_inicio"
            type="date"
            value={dataInicio ?? ""}
            onChange={(event) => setDataInicio(event.target.value)}
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="prazo_dias">Prazo (dias)</Label>
          <Input
            id="prazo_dias"
            type="number"
            min="0"
            value={prazoDias}
            onChange={(event) => setPrazoDias(event.target.value)}
          />
        </div>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="objeto">Objeto do contrato</Label>
        <Textarea id="objeto" value={objeto ?? ""} onChange={(event) => setObjeto(event.target.value)} rows={2} />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="observacoes_gerais">Observações gerais</Label>
        <Textarea
          id="observacoes_gerais"
          value={observacoes ?? ""}
          onChange={(event) => setObservacoes(event.target.value)}
          rows={2}
        />
      </div>

      <Separator />

      <fieldset className="space-y-3">
        <legend className="text-sm font-semibold text-foreground">
          Empresas executoras <span className="font-normal text-muted-foreground">(RN-06)</span>
        </legend>
        {executores.map((executor, index) => (
          <div key={index} className="space-y-3 rounded-md border p-3">
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor={`executor-razao-${index}`} required>
                  Razão social
                </Label>
                <Input
                  id={`executor-razao-${index}`}
                  value={executor.razao_social}
                  onChange={(event) => updateExecutor(index, { razao_social: event.target.value })}
                  aria-invalid={Boolean(fieldErrors[`executor.${index}.razao_social`])}
                />
                {fieldErrors[`executor.${index}.razao_social`] ? (
                  <p className="text-xs text-destructive">{fieldErrors[`executor.${index}.razao_social`]}</p>
                ) : null}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor={`executor-cnpj-${index}`} required>
                  CNPJ
                </Label>
                <Input
                  id={`executor-cnpj-${index}`}
                  value={executor.cnpj}
                  onChange={(event) => updateExecutor(index, { cnpj: event.target.value })}
                  placeholder="00.000.000/0000-00"
                  aria-invalid={Boolean(fieldErrors[`executor.${index}.cnpj`])}
                />
                {fieldErrors[`executor.${index}.cnpj`] ? (
                  <p className="text-xs text-destructive">{fieldErrors[`executor.${index}.cnpj`]}</p>
                ) : null}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor={`executor-legal-${index}`} required>
                  Responsável legal (ID)
                </Label>
                <Input
                  id={`executor-legal-${index}`}
                  value={executor.responsavel_legal_id}
                  onChange={(event) => updateExecutor(index, { responsavel_legal_id: event.target.value })}
                  placeholder="UUID do responsável"
                  aria-invalid={Boolean(fieldErrors[`executor.${index}.responsavel_legal_id`])}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor={`executor-rte-${index}`}>RTE (ID)</Label>
                <Input
                  id={`executor-rte-${index}`}
                  value={executor.rte_id ?? ""}
                  onChange={(event) => updateExecutor(index, { rte_id: event.target.value })}
                  placeholder="UUID do RTE (opcional)"
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor={`executor-art-${index}`} required>
                  ART de Execução
                </Label>
                <Input
                  id={`executor-art-${index}`}
                  value={executor.art_execucao ?? ""}
                  onChange={(event) => updateExecutor(index, { art_execucao: event.target.value })}
                  aria-invalid={Boolean(fieldErrors[`executor.${index}.art_execucao`])}
                />
                {fieldErrors[`executor.${index}.art_execucao`] ? (
                  <p className="text-xs text-destructive">{fieldErrors[`executor.${index}.art_execucao`]}</p>
                ) : null}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor={`executor-endereco-${index}`}>Endereço</Label>
                <Input
                  id={`executor-endereco-${index}`}
                  value={executor.endereco ?? ""}
                  onChange={(event) => updateExecutor(index, { endereco: event.target.value })}
                />
              </div>
            </div>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="gap-1.5 text-destructive hover:text-destructive"
              onClick={() => setExecutores((prev) => prev.filter((_, i) => i !== index))}
              disabled={executores.length === 1}
            >
              <Trash2 className="h-3.5 w-3.5" aria-hidden="true" />
              Remover executora
            </Button>
          </div>
        ))}
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="gap-1.5"
          onClick={() => setExecutores((prev) => [...prev, emptyExecutor()])}
        >
          <Plus className="h-3.5 w-3.5" aria-hidden="true" />
          Adicionar empresa executora
        </Button>
      </fieldset>

      <Separator />

      <fieldset className="space-y-3">
        <legend className="text-sm font-semibold text-foreground">NBRs aplicáveis</legend>
        {nbrs.map((nbr, index) => (
          <div key={index} className="flex flex-wrap items-start gap-2">
            <div className="w-32 space-y-1.5">
              <Label htmlFor={`nbr-codigo-${index}`} className="sr-only">
                Código da NBR
              </Label>
              <Input
                id={`nbr-codigo-${index}`}
                value={nbr.codigo_nbr}
                onChange={(event) => updateNbr(index, { codigo_nbr: event.target.value })}
                placeholder="NBR 16747"
              />
            </div>
            <div className="flex-1 space-y-1.5">
              <Label htmlFor={`nbr-descricao-${index}`} className="sr-only">
                Descrição da NBR
              </Label>
              <Input
                id={`nbr-descricao-${index}`}
                value={nbr.descricao ?? ""}
                onChange={(event) => updateNbr(index, { descricao: event.target.value })}
                placeholder="Descrição (opcional)"
              />
            </div>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="text-destructive hover:text-destructive"
              onClick={() => setNbrs((prev) => prev.filter((_, i) => i !== index))}
              disabled={nbrs.length === 1}
              aria-label="Remover NBR"
            >
              <Trash2 className="h-4 w-4" aria-hidden="true" />
            </Button>
          </div>
        ))}
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="gap-1.5"
          onClick={() => setNbrs((prev) => [...prev, emptyNbr()])}
        >
          <Plus className="h-3.5 w-3.5" aria-hidden="true" />
          Adicionar NBR
        </Button>
      </fieldset>

      <div className="flex justify-end gap-2 pt-2">
        {onCancel ? (
          <Button type="button" variant="outline" onClick={onCancel} disabled={isSubmitting}>
            Cancelar
          </Button>
        ) : null}
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Salvando..." : submitLabel}
        </Button>
      </div>
    </form>
  );
}
