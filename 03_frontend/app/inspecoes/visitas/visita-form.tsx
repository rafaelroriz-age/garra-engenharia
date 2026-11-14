"use client";

import { useEffect, useState } from "react";

import type { VisitaInput } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ApiError } from "@/lib/api-client";
import { ApiErrorAlert } from "@/components/api-error-alert";

interface VisitaFormProps {
  initialValue?: Partial<VisitaInput>;
  submitLabel: string;
  onSubmit: (input: VisitaInput) => Promise<void>;
  onCancel?: () => void;
}

/**
 * Formulário de criação/edição de Visita do RFO (RF-03, RN-02, BL-10).
 * O sequenciamento (`seq_numero`) é atribuído automaticamente pelo backend.
 */
export function VisitaForm({ initialValue, submitLabel, onSubmit, onCancel }: VisitaFormProps) {
  const [data, setData] = useState(initialValue?.data ?? "");
  const [servicosExecutados, setServicosExecutados] = useState(initialValue?.servicos_executados ?? "");
  const [observacoes, setObservacoes] = useState(initialValue?.observacoes ?? "");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<ApiError | Error | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    setData(initialValue?.data ?? "");
    setServicosExecutados(initialValue?.servicos_executados ?? "");
    setObservacoes(initialValue?.observacoes ?? "");
    setFieldErrors({});
    setError(null);
  }, [initialValue?.data, initialValue?.servicos_executados, initialValue?.observacoes]);

  function validate(): boolean {
    const errors: Record<string, string> = {};
    if (!data) errors.data = "Informe a data da visita (RN-02).";
    if (!servicosExecutados?.trim()) errors.servicos_executados = "Descreva os serviços executados (RN-02).";
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
        data,
        servicos_executados: servicosExecutados.trim(),
        observacoes: observacoes.trim() || null,
      });
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Falha ao salvar visita."));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4" noValidate>
      <ApiErrorAlert error={error} />

      <div className="space-y-1.5">
        <Label htmlFor="data-visita" required>
          Data da visita
        </Label>
        <Input
          id="data-visita"
          type="date"
          value={data}
          onChange={(event) => setData(event.target.value)}
          aria-invalid={Boolean(fieldErrors.data)}
          required
        />
        {fieldErrors.data ? <p className="text-xs text-destructive">{fieldErrors.data}</p> : null}
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="servicos-executados" required>
          Serviços executados
        </Label>
        <Textarea
          id="servicos-executados"
          value={servicosExecutados ?? ""}
          onChange={(event) => setServicosExecutados(event.target.value)}
          rows={3}
          aria-invalid={Boolean(fieldErrors.servicos_executados)}
          required
        />
        {fieldErrors.servicos_executados ? (
          <p className="text-xs text-destructive">{fieldErrors.servicos_executados}</p>
        ) : null}
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="observacoes-visita">Observações</Label>
        <Textarea
          id="observacoes-visita"
          value={observacoes ?? ""}
          onChange={(event) => setObservacoes(event.target.value)}
          rows={3}
        />
      </div>

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
