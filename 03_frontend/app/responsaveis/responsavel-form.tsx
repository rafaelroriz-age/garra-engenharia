"use client";

import { useState } from "react";
import { ImageUp, Loader2, Plus, Trash2 } from "lucide-react";

import { ApiErrorAlert } from "@/components/api-error-alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { ApiError, uploadImagem } from "@/lib/api-client";
import type { ResponsavelInput } from "@/lib/types";

export const TIPOS_RESPONSAVEL = [
  { value: "fiscal", label: "Fiscal / responsável técnico" },
  { value: "responsavel_legal", label: "Responsável legal" },
  { value: "rte", label: "RTE (responsável técnico da executora)" },
  { value: "sindico", label: "Síndico" },
  { value: "contratante", label: "Contratante" },
];

// Tetos de `app/schemas/responsavel.py` (V1-01).
const TITULO_MAX = 120;
const QUALIFICACAO_MAX = 300;
const QUALIFICACOES_MAX_ITENS = 20;

const vazioParaNull = (valor: string) => (valor.trim() ? valor.trim() : null);

interface ResponsavelFormProps {
  onSubmit: (input: ResponsavelInput) => Promise<void>;
  onCancel: () => void;
}

/**
 * Cadastro de Responsável com o bloco de assinatura dos laudos (V1-06): título
 * profissional, qualificações e imagem da assinatura.
 *
 * A imagem sobe pelo upload bruto de fotos (`POST /fotos/upload`, revalidado com
 * Pillow no backend) e só a `storage_key` devolvida é gravada no responsável.
 */
export function ResponsavelForm({ onSubmit, onCancel }: ResponsavelFormProps) {
  const [nome, setNome] = useState("");
  const [tipo, setTipo] = useState("fiscal");
  const [crea, setCrea] = useState("");
  const [cpfCnpj, setCpfCnpj] = useState("");
  const [email, setEmail] = useState("");
  const [telefone, setTelefone] = useState("");
  const [titulo, setTitulo] = useState("");
  const [qualificacoes, setQualificacoes] = useState<string[]>([]);
  const [assinatura, setAssinatura] = useState<{ storage_key: string; url: string } | null>(null);
  const [enviandoAssinatura, setEnviandoAssinatura] = useState(false);
  const [salvando, setSalvando] = useState(false);
  const [erroNome, setErroNome] = useState<string | null>(null);
  const [erro, setErro] = useState<ApiError | Error | null>(null);

  async function enviarAssinatura(arquivo: File | undefined) {
    if (!arquivo) return;
    setEnviandoAssinatura(true);
    setErro(null);
    try {
      setAssinatura(await uploadImagem(arquivo));
    } catch (err) {
      setErro(err instanceof Error ? err : new Error("Falha ao enviar a imagem da assinatura."));
    } finally {
      setEnviandoAssinatura(false);
    }
  }

  async function submeter(event: React.FormEvent) {
    event.preventDefault();
    if (!nome.trim()) {
      setErroNome("Informe o nome.");
      return;
    }
    setErroNome(null);
    setSalvando(true);
    setErro(null);
    try {
      const listaQualificacoes = qualificacoes.map((q) => q.trim()).filter(Boolean);
      await onSubmit({
        nome: nome.trim(),
        tipo,
        crea: vazioParaNull(crea),
        cpf_cnpj: vazioParaNull(cpfCnpj),
        email: vazioParaNull(email),
        telefone: vazioParaNull(telefone),
        titulo_profissional: vazioParaNull(titulo),
        qualificacoes: listaQualificacoes.length > 0 ? listaQualificacoes : null,
        assinatura_storage_key: assinatura?.storage_key ?? null,
      });
    } catch (err) {
      setErro(err instanceof Error ? err : new Error("Falha ao cadastrar o responsável."));
    } finally {
      setSalvando(false);
    }
  }

  return (
    <form onSubmit={submeter} className="space-y-4" noValidate>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="space-y-1.5 sm:col-span-2">
          <Label htmlFor="resp-nome">Nome *</Label>
          <Input
            id="resp-nome"
            value={nome}
            onChange={(e) => setNome(e.target.value)}
            aria-invalid={Boolean(erroNome)}
            aria-describedby={erroNome ? "resp-nome-erro" : undefined}
          />
          {erroNome ? (
            <p id="resp-nome-erro" className="text-sm text-destructive">
              {erroNome}
            </p>
          ) : null}
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="resp-tipo">Tipo *</Label>
          <Select id="resp-tipo" value={tipo} onChange={(e) => setTipo(e.target.value)}>
            {TIPOS_RESPONSAVEL.map((opcao) => (
              <option key={opcao.value} value={opcao.value}>
                {opcao.label}
              </option>
            ))}
          </Select>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="resp-crea">CREA</Label>
          <Input id="resp-crea" value={crea} onChange={(e) => setCrea(e.target.value)} />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="resp-cpf">CPF/CNPJ</Label>
          <Input id="resp-cpf" inputMode="numeric" value={cpfCnpj} onChange={(e) => setCpfCnpj(e.target.value)} />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="resp-telefone">Telefone</Label>
          <Input id="resp-telefone" type="tel" value={telefone} onChange={(e) => setTelefone(e.target.value)} />
        </div>
        <div className="space-y-1.5 sm:col-span-2">
          <Label htmlFor="resp-email">E-mail</Label>
          <Input id="resp-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
      </div>

      <fieldset className="space-y-4 rounded-md border p-3">
        <legend className="px-1 text-sm font-medium">Assinatura nos laudos</legend>
        <div className="space-y-1.5">
          <Label htmlFor="resp-titulo">Título profissional</Label>
          <Input
            id="resp-titulo"
            maxLength={TITULO_MAX}
            placeholder="Ex.: Engenheiro Civil"
            value={titulo}
            onChange={(e) => setTitulo(e.target.value)}
          />
        </div>

        <div className="space-y-2">
          <p className="text-sm font-medium" id="resp-qualificacoes">
            Qualificações
          </p>
          {qualificacoes.length === 0 ? (
            <p className="text-sm text-muted-foreground">Nenhuma qualificação informada.</p>
          ) : null}
          <ul className="space-y-2" aria-labelledby="resp-qualificacoes">
            {qualificacoes.map((qualificacao, index) => (
              <li key={index} className="flex items-center gap-2">
                <Input
                  aria-label={`Qualificação ${index + 1}`}
                  className="min-w-0 flex-1"
                  maxLength={QUALIFICACAO_MAX}
                  placeholder="Ex.: Especialista em Patologia das Construções"
                  value={qualificacao}
                  onChange={(e) =>
                    setQualificacoes((atual) => atual.map((q, i) => (i === index ? e.target.value : q)))
                  }
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  aria-label={`Remover qualificação ${index + 1}`}
                  onClick={() => setQualificacoes((atual) => atual.filter((_, i) => i !== index))}
                >
                  <Trash2 aria-hidden="true" />
                </Button>
              </li>
            ))}
          </ul>
          {qualificacoes.length < QUALIFICACOES_MAX_ITENS ? (
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setQualificacoes((atual) => [...atual, ""])}
            >
              <Plus aria-hidden="true" />
              Adicionar qualificação
            </Button>
          ) : null}
        </div>

        <div className="space-y-2">
          <Label htmlFor="resp-assinatura">Imagem da assinatura (PNG ou JPEG)</Label>
          <Input
            id="resp-assinatura"
            type="file"
            accept="image/png,image/jpeg"
            disabled={enviandoAssinatura}
            onChange={(e) => void enviarAssinatura(e.target.files?.[0])}
          />
          <div role="status" aria-live="polite" className="text-sm">
            {enviandoAssinatura ? (
              <span className="inline-flex items-center gap-1 text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                Enviando imagem...
              </span>
            ) : assinatura ? (
              <span className="inline-flex items-center gap-1">
                <ImageUp className="h-4 w-4" aria-hidden="true" />
                Assinatura enviada.
              </span>
            ) : null}
          </div>
          {assinatura ? (
            // URL pré-assinada temporária do storage: <img> simples, sem otimização do Next.
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={assinatura.url}
              alt="Pré-visualização da assinatura"
              className="max-h-24 max-w-full rounded border bg-white object-contain p-1"
            />
          ) : null}
        </div>
      </fieldset>

      <ApiErrorAlert error={erro} />

      <div className="flex flex-wrap justify-end gap-2">
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancelar
        </Button>
        <Button type="submit" disabled={salvando || enviandoAssinatura}>
          {salvando ? <Loader2 className="animate-spin" aria-hidden="true" /> : null}
          Cadastrar responsável
        </Button>
      </div>
    </form>
  );
}
