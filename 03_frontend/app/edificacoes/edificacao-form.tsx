"use client";

import { useState } from "react";

import type { Edificacao, EdificacaoInput } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select } from "@/components/ui/select";
import { ApiError } from "@/lib/api-client";
import { ApiErrorAlert } from "@/components/api-error-alert";

const TIPOLOGIAS = ["Residencial", "Comercial", "Misto", "Industrial"];

interface EdificacaoFormProps {
  initialValue?: Edificacao;
  submitLabel: string;
  onSubmit: (input: EdificacaoInput) => Promise<void>;
  onCancel?: () => void;
}

/**
 * Formulário de criação/edição de Edificação (RF-01, BL-08).
 * Validação client-side espelha os campos obrigatórios do backend
 * (`nome`, `endereco`) — regras de negócio permanecem no backend.
 */
export function EdificacaoForm({ initialValue, submitLabel, onSubmit, onCancel }: EdificacaoFormProps) {
  const [nome, setNome] = useState(initialValue?.nome ?? "");
  const [endereco, setEndereco] = useState(initialValue?.endereco ?? "");
  const [cep, setCep] = useState(initialValue?.cep ?? "");
  const [cidade, setCidade] = useState(initialValue?.cidade ?? "");
  const [uf, setUf] = useState(initialValue?.uf ?? "");
  const [tipologia, setTipologia] = useState(initialValue?.tipologia ?? "");
  const [sistemaConstrutivo, setSistemaConstrutivo] = useState(initialValue?.sistema_construtivo ?? "");
  const [descricaoPavimentos, setDescricaoPavimentos] = useState(initialValue?.descricao_pavimentos ?? "");
  const [areaTotal, setAreaTotal] = useState(initialValue?.area_total_m2?.toString() ?? "");

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<ApiError | Error | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  function validate(): boolean {
    const errors: Record<string, string> = {};
    if (!nome.trim()) errors.nome = "Informe o nome da edificação.";
    if (!endereco.trim()) errors.endereco = "Informe o endereço completo.";
    if (areaTotal && Number.isNaN(Number(areaTotal))) errors.area_total_m2 = "Área deve ser numérica.";
    if (uf.trim() && !/^[A-Za-z]{2}$/.test(uf.trim())) errors.uf = "UF deve ter 2 letras (ex.: SP).";
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
        nome: nome.trim(),
        endereco: endereco.trim(),
        cep: cep.trim() || null,
        cidade: cidade.trim() || null,
        uf: uf.trim() ? uf.trim().toUpperCase() : null,
        tipologia: tipologia || null,
        sistema_construtivo: sistemaConstrutivo.trim() || null,
        descricao_pavimentos: descricaoPavimentos.trim() || null,
        area_total_m2: areaTotal ? Number(areaTotal) : null,
        documentos_tecnicos: initialValue?.documentos_tecnicos ?? null,
      });
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err);
        const apiFieldErrors: Record<string, string> = {};
        err.errors.forEach((fieldError) => {
          // 422 de UF (T97): mensagem em português, independente do texto do backend.
          if (fieldError.field === "uf" || fieldError.field.endsWith(".uf")) {
            apiFieldErrors.uf = "UF inválida. Informe a sigla de 2 letras do estado (ex.: SP).";
            return;
          }
          apiFieldErrors[fieldError.field] = fieldError.message;
        });
        setFieldErrors((prev) => ({ ...prev, ...apiFieldErrors }));
      } else {
        setError(err instanceof Error ? err : new Error("Falha ao salvar edificação."));
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4" noValidate>
      <ApiErrorAlert error={error} />

      <div className="space-y-1.5">
        <Label htmlFor="nome" required>
          Nome
        </Label>
        <Input
          id="nome"
          value={nome}
          onChange={(event) => setNome(event.target.value)}
          aria-invalid={Boolean(fieldErrors.nome)}
          aria-describedby={fieldErrors.nome ? "nome-error" : undefined}
          required
        />
        {fieldErrors.nome ? (
          <p id="nome-error" className="text-xs text-destructive">
            {fieldErrors.nome}
          </p>
        ) : null}
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="endereco" required>
          Endereço
        </Label>
        <Input
          id="endereco"
          value={endereco}
          onChange={(event) => setEndereco(event.target.value)}
          aria-invalid={Boolean(fieldErrors.endereco)}
          aria-describedby={fieldErrors.endereco ? "endereco-error" : undefined}
          required
        />
        {fieldErrors.endereco ? (
          <p id="endereco-error" className="text-xs text-destructive">
            {fieldErrors.endereco}
          </p>
        ) : null}
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="space-y-1.5">
          <Label htmlFor="cep">CEP</Label>
          <Input id="cep" value={cep} onChange={(event) => setCep(event.target.value)} />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="cidade">Cidade</Label>
          <Input
            id="cidade"
            maxLength={120}
            value={cidade}
            onChange={(event) => setCidade(event.target.value)}
            aria-invalid={Boolean(fieldErrors.cidade)}
          />
          {fieldErrors.cidade ? <p className="text-xs text-destructive">{fieldErrors.cidade}</p> : null}
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="uf">UF</Label>
          <Input
            id="uf"
            maxLength={2}
            placeholder="Ex.: SP"
            value={uf}
            onChange={(event) => setUf(event.target.value.toUpperCase())}
            aria-invalid={Boolean(fieldErrors.uf)}
            aria-describedby={fieldErrors.uf ? "uf-error" : undefined}
          />
          {fieldErrors.uf ? (
            <p id="uf-error" className="text-xs text-destructive">
              {fieldErrors.uf}
            </p>
          ) : null}
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="tipologia">Tipologia</Label>
          <Select id="tipologia" value={tipologia} onChange={(event) => setTipologia(event.target.value)}>
            <option value="">Selecione...</option>
            {TIPOLOGIAS.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </Select>
        </div>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="sistema_construtivo">Sistema construtivo</Label>
        <Input
          id="sistema_construtivo"
          value={sistemaConstrutivo}
          onChange={(event) => setSistemaConstrutivo(event.target.value)}
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="descricao_pavimentos">Descrição de pavimentos</Label>
        <Textarea
          id="descricao_pavimentos"
          value={descricaoPavimentos}
          onChange={(event) => setDescricaoPavimentos(event.target.value)}
          rows={3}
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="area_total_m2">Área total (m²)</Label>
        <Input
          id="area_total_m2"
          type="number"
          step="0.01"
          min="0"
          value={areaTotal}
          onChange={(event) => setAreaTotal(event.target.value)}
          aria-invalid={Boolean(fieldErrors.area_total_m2)}
        />
        {fieldErrors.area_total_m2 ? (
          <p className="text-xs text-destructive">{fieldErrors.area_total_m2}</p>
        ) : null}
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
