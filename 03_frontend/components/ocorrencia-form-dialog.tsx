"use client";

import { useEffect, useState } from "react";

import { api, ApiError } from "@/lib/api-client";
import type {
  Localizacao,
  Ocorrencia,
  OcorrenciaInput,
  SistemaPredialComSubsistemas,
  TipoAnomalia,
  TipoFalha,
} from "@/lib/types";
import {
  CLASSIFICACAO_OPTIONS,
  GRAU_RISCO_OPTIONS,
  SITUACAO_OPTIONS,
  exigeTipoAnomalia,
  exigeTipoFalha,
} from "@/lib/ocorrencia-enums";
import { ApiErrorAlert } from "@/components/api-error-alert";
import { FotoUpload } from "@/components/foto-upload";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";

interface OcorrenciaFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  inspecaoId: string;
  /** Presente em modo de edição; `null` para criação de uma nova ocorrência. */
  ocorrencia: Ocorrencia | null;
  sistemas: SistemaPredialComSubsistemas[];
  tiposAnomalia: TipoAnomalia[];
  tiposFalha: TipoFalha[];
  localizacoes: Localizacao[];
  onSaved: (ocorrencia: Ocorrencia) => void;
}

const FORM_VAZIO: OcorrenciaInput = {
  inspecao_id: "",
  sistema_id: "",
  subsistema_id: null,
  localizacao: "",
  situacao: "",
  classificacao: "",
  tipo_anomalia: null,
  tipo_falha: null,
  grau_risco: "",
  prioridade: null,
  descricao: "",
  gut_gravidade: null,
  gut_urgencia: null,
  gut_tendencia: null,
};

/**
 * Formulário de criação/edição de Ocorrência (RF-04, RN-05, BL-14).
 *
 * A classificação completa (Situação, Classificação, Tipo de Anomalia/Falha
 * quando aplicável, Grau de Risco e Prioridade) é exigida no cliente para dar
 * feedback imediato, mas a validação definitiva é sempre feita pelo backend.
 * A `Prioridade` é informada manualmente (0-5) até a automação por Grau de
 * Risco (RN-04) ser destravada na BL-15 — ver observação no rodapé do formulário.
 */
export function OcorrenciaFormDialog({
  open,
  onOpenChange,
  inspecaoId,
  ocorrencia,
  sistemas,
  tiposAnomalia,
  tiposFalha,
  localizacoes,
  onSaved,
}: OcorrenciaFormDialogProps) {
  const [form, setForm] = useState<OcorrenciaInput>({ ...FORM_VAZIO, inspecao_id: inspecaoId });
  const [savedOcorrencia, setSavedOcorrencia] = useState<Ocorrencia | null>(ocorrencia);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<ApiError | Error | null>(null);

  useEffect(() => {
    if (open) {
      setSavedOcorrencia(ocorrencia);
      setError(null);
      setForm(
        ocorrencia
          ? {
              inspecao_id: ocorrencia.inspecao_id,
              sistema_id: ocorrencia.sistema_id,
              subsistema_id: ocorrencia.subsistema_id ?? null,
              localizacao: ocorrencia.localizacao ?? "",
              situacao: ocorrencia.situacao,
              classificacao: ocorrencia.classificacao,
              tipo_anomalia: ocorrencia.tipo_anomalia ?? null,
              tipo_falha: ocorrencia.tipo_falha ?? null,
              grau_risco: ocorrencia.grau_risco ?? "",
              prioridade: ocorrencia.prioridade ?? null,
              descricao: ocorrencia.descricao ?? "",
              gut_gravidade: ocorrencia.gut_gravidade ?? null,
              gut_urgencia: ocorrencia.gut_urgencia ?? null,
              gut_tendencia: ocorrencia.gut_tendencia ?? null,
            }
          : { ...FORM_VAZIO, inspecao_id: inspecaoId }
      );
    }
  }, [open, ocorrencia, inspecaoId]);

  const subsistemasDoSistema = sistemas.find((sistema) => sistema.id === form.sistema_id)?.subsistemas ?? [];
  const precisaTipoAnomalia = exigeTipoAnomalia(form.classificacao);
  const precisaTipoFalha = exigeTipoFalha(form.classificacao);

  const camposObrigatoriosPreenchidos =
    Boolean(form.sistema_id) &&
    Boolean(form.situacao) &&
    Boolean(form.classificacao) &&
    Boolean(form.grau_risco) &&
    (!precisaTipoAnomalia || Boolean(form.tipo_anomalia)) &&
    (!precisaTipoFalha || Boolean(form.tipo_falha));

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!camposObrigatoriosPreenchidos) return;
    setSaving(true);
    setError(null);
    try {
      const payload: OcorrenciaInput = {
        ...form,
        subsistema_id: form.subsistema_id || null,
        tipo_anomalia: precisaTipoAnomalia ? form.tipo_anomalia : null,
        tipo_falha: precisaTipoFalha ? form.tipo_falha : null,
      };
      const result = savedOcorrencia
        ? await api.put<Ocorrencia>(`/ocorrencias/${savedOcorrencia.id}`, payload)
        : await api.post<Ocorrencia>(`/inspecoes/${inspecaoId}/ocorrencias`, payload);
      setSavedOcorrencia(result);
      onSaved(result);
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Falha ao salvar a ocorrência."));
    } finally {
      setSaving(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>{savedOcorrencia ? "Editar ocorrência" : "Nova ocorrência"}</DialogTitle>
          <DialogDescription>
            Classificação completa: Situação, Classificação, Tipo de
            Anomalia/Falha (quando aplicável), Grau de Risco e Prioridade.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="sistema" required>
                Sistema predial
              </Label>
              <Select
                id="sistema"
                required
                value={form.sistema_id}
                onChange={(event) =>
                  setForm((prev) => ({ ...prev, sistema_id: event.target.value, subsistema_id: null }))
                }
              >
                <option value="">Selecione…</option>
                {sistemas.map((sistema) => (
                  <option key={sistema.id} value={sistema.id}>
                    {sistema.nome}
                  </option>
                ))}
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="subsistema">Subsistema</Label>
              <Select
                id="subsistema"
                value={form.subsistema_id ?? ""}
                disabled={!form.sistema_id}
                onChange={(event) => setForm((prev) => ({ ...prev, subsistema_id: event.target.value || null }))}
              >
                <option value="">
                  {form.sistema_id ? "Selecione…" : "Selecione o sistema primeiro"}
                </option>
                {subsistemasDoSistema.map((subsistema) => (
                  <option key={subsistema.id} value={subsistema.id}>
                    {subsistema.nome}
                  </option>
                ))}
              </Select>
            </div>

            <div className="space-y-1.5 sm:col-span-2">
              <Label htmlFor="localizacao">Localização</Label>
              <Input
                id="localizacao"
                list="localizacoes-gabarito"
                value={form.localizacao ?? ""}
                placeholder="Selecione do gabarito ou digite uma localização"
                onChange={(event) => setForm((prev) => ({ ...prev, localizacao: event.target.value }))}
              />
              <datalist id="localizacoes-gabarito">
                {localizacoes.map((localizacao) => (
                  <option key={localizacao.id} value={localizacao.nome} />
                ))}
              </datalist>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="situacao" required>
                Situação
              </Label>
              <Select
                id="situacao"
                required
                value={form.situacao}
                onChange={(event) => setForm((prev) => ({ ...prev, situacao: event.target.value }))}
              >
                <option value="">Selecione…</option>
                {SITUACAO_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Select>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="grau_risco" required>
                Grau de Risco (CMM)
              </Label>
              <Select
                id="grau_risco"
                required
                value={form.grau_risco ?? ""}
                onChange={(event) => setForm((prev) => ({ ...prev, grau_risco: event.target.value }))}
              >
                <option value="">Selecione…</option>
                {GRAU_RISCO_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Select>
            </div>

            <div className="space-y-1.5 sm:col-span-2">
              <Label htmlFor="classificacao" required>
                Classificação
              </Label>
              <Select
                id="classificacao"
                required
                value={form.classificacao}
                onChange={(event) => setForm((prev) => ({ ...prev, classificacao: event.target.value }))}
              >
                <option value="">Selecione…</option>
                {CLASSIFICACAO_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Select>
            </div>

            {precisaTipoAnomalia ? (
              <div className="space-y-1.5">
                <Label htmlFor="tipo_anomalia" required>
                  Tipo de Anomalia
                </Label>
                <Select
                  id="tipo_anomalia"
                  required
                  value={form.tipo_anomalia ?? ""}
                  onChange={(event) => setForm((prev) => ({ ...prev, tipo_anomalia: event.target.value }))}
                >
                  <option value="">Selecione…</option>
                  {tiposAnomalia.map((tipo) => (
                    <option key={tipo.id} value={tipo.nome}>
                      {tipo.nome}
                    </option>
                  ))}
                </Select>
              </div>
            ) : null}

            {precisaTipoFalha ? (
              <div className="space-y-1.5">
                <Label htmlFor="tipo_falha" required>
                  Tipo de Falha
                </Label>
                <Select
                  id="tipo_falha"
                  required
                  value={form.tipo_falha ?? ""}
                  onChange={(event) => setForm((prev) => ({ ...prev, tipo_falha: event.target.value }))}
                >
                  <option value="">Selecione…</option>
                  {tiposFalha.map((tipo) => (
                    <option key={tipo.id} value={tipo.nome}>
                      {tipo.nome}
                    </option>
                  ))}
                </Select>
              </div>
            ) : null}

            <div className="space-y-1.5">
              <Label htmlFor="prioridade">Prioridade (0-5)</Label>
              <Input
                id="prioridade"
                type="number"
                min={0}
                max={5}
                value={form.prioridade ?? ""}
                onChange={(event) =>
                  setForm((prev) => ({
                    ...prev,
                    prioridade: event.target.value === "" ? null : Number(event.target.value),
                  }))
                }
                aria-describedby="prioridade-hint"
              />
              <p id="prioridade-hint" className="text-xs text-muted-foreground">
                Informada manualmente.
              </p>
            </div>

            <div className="space-y-1.5 sm:col-span-2">
              <Label htmlFor="descricao">Descrição</Label>
              <Textarea
                id="descricao"
                value={form.descricao ?? ""}
                onChange={(event) => setForm((prev) => ({ ...prev, descricao: event.target.value }))}
                rows={3}
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <Label>Fotos</Label>
            <FotoUpload
              ocorrenciaId={savedOcorrencia?.id}
              fotos={savedOcorrencia?.fotos ?? []}
              onChange={(fotos) => setSavedOcorrencia((prev) => (prev ? { ...prev, fotos } : prev))}
            />
          </div>

          <ApiErrorAlert error={error} />

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              {savedOcorrencia ? "Concluir" : "Cancelar"}
            </Button>
            <Button type="submit" disabled={saving || !camposObrigatoriosPreenchidos}>
              {saving ? "Salvando…" : savedOcorrencia ? "Salvar alterações" : "Criar ocorrência"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
