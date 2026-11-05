"use client";

import { useEffect, useId, useState } from "react";
import { CheckCircle2, Info, Loader2, Sparkles, TriangleAlert } from "lucide-react";

import { ApiError, legendaIA } from "@/lib/api-client";
import {
  LEGENDA_BRUTA_MAX_LENGTH,
  LEGENDA_MAX_LENGTH,
  type Foto,
  type NivelCertezaIA,
} from "@/lib/types";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ApiErrorAlert } from "@/components/api-error-alert";

const NIVEL_CERTEZA_LABEL: Record<NivelCertezaIA, string> = {
  constatacao_direta: "Constatação direta",
  indicio_tecnico: "Indício técnico",
  hipotese_tecnica: "Hipótese técnica",
  causa_comprovada: "Causa comprovada",
};

interface LegendaIAPainelProps {
  foto: Foto;
  /** Recebe a foto devolvida pela API (`FotoRead`) após gerar ou aprovar. */
  onFotoAtualizada: (foto: Foto) => void;
}

/** Texto inicial do campo editável: a legenda aprovada, se houver; senão, a sugestão da IA. */
function textoInicial(foto: Foto): string {
  if (foto.status_validacao_ia === "aprovada") {
    return foto.legenda ?? foto.legenda_ia_sugerida ?? "";
  }
  return foto.legenda_ia_sugerida ?? "";
}

/**
 * 503 = nenhum provedor de LLM configurado no servidor (`legenda-ia-indisponivel`, B-04).
 * Troca a mensagem técnica por uma orientação clara, ainda exibida via `ApiErrorAlert`.
 */
function normalizarErroGeracao(err: unknown): ApiError | Error {
  if (err instanceof ApiError && err.status === 503) {
    return new ApiError({
      status: 503,
      title: "Geração de legenda por IA indisponível",
      detail:
        "O servidor ainda não tem um provedor de IA configurado. Escreva a legenda manualmente no campo da foto; a geração automática ficará disponível quando o provedor for habilitado.",
    });
  }
  return err instanceof Error ? err : new Error("Falha ao gerar a legenda com IA.");
}

function formatarDataHora(iso: string | null | undefined): string | null {
  if (!iso) return null;
  const data = new Date(iso);
  if (Number.isNaN(data.getTime())) return null;
  return data.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
}

/**
 * Painel de legenda de foto assistida por IA (BL-35; RF-15, RN-16, RN-17, DEC-21).
 *
 * A IA só produz um **rascunho** (`POST /fotos/{id}/legenda-ia/gerar`): a `legenda` final da
 * foto, que é a única que entra no relatório, só é gravada quando um humano revisa o texto e
 * confirma a aprovação (`PUT /fotos/{id}` com `aprovar_legenda_ia: true`). Aprovador e data
 * vêm do token no backend; nada de aprovação é enviado pelo cliente.
 *
 * Exibido apenas para a equipe (auditor/auxiliar) — o controle de acesso real é do backend.
 */
export function LegendaIAPainel({ foto, onFotoAtualizada }: LegendaIAPainelProps) {
  const idBase = useId();
  const [legendaBruta, setLegendaBruta] = useState(foto.legenda_bruta ?? "");
  const [texto, setTexto] = useState(() => textoInicial(foto));
  const [isGerando, setIsGerando] = useState(false);
  const [isAprovando, setIsAprovando] = useState(false);
  const [confirmando, setConfirmando] = useState(false);
  const [erro, setErro] = useState<ApiError | Error | null>(null);
  const [mensagemSucesso, setMensagemSucesso] = useState<string | null>(null);

  // Troca de foto selecionada: reinicia o estado local a partir da foto recebida.
  useEffect(() => {
    setLegendaBruta(foto.legenda_bruta ?? "");
    setTexto(textoInicial(foto));
    setConfirmando(false);
    setErro(null);
    setMensagemSucesso(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [foto.id]);

  const temSugestao = foto.status_validacao_ia != null && Boolean(foto.legenda_ia_sugerida);
  const textoLimpo = texto.trim();
  const ocupado = isGerando || isAprovando;
  const podeAprovar = temSugestao && textoLimpo.length > 0 && !ocupado;
  const alertas = foto.alertas_ia ?? [];
  const pendencias = foto.pendencias_ia ?? [];
  const geradaEm = formatarDataHora(foto.legenda_ia_gerada_em);
  const aprovadaEm = formatarDataHora(foto.aprovado_em);

  const gerar = async () => {
    setErro(null);
    setMensagemSucesso(null);
    setConfirmando(false);
    setIsGerando(true);
    try {
      const bruta = legendaBruta.trim();
      const atualizada = await legendaIA.gerar(foto.id, { legenda_bruta: bruta.length > 0 ? bruta : null });
      setTexto(atualizada.legenda_ia_sugerida ?? "");
      onFotoAtualizada(atualizada);
      setMensagemSucesso("Sugestão gerada. Revise o texto antes de aprovar.");
    } catch (err) {
      setErro(normalizarErroGeracao(err));
    } finally {
      setIsGerando(false);
    }
  };

  const aprovar = async () => {
    if (!podeAprovar) return;
    setErro(null);
    setMensagemSucesso(null);
    setIsAprovando(true);
    try {
      const atualizada = await legendaIA.aprovar(foto.id, textoLimpo);
      setTexto(atualizada.legenda ?? textoLimpo);
      onFotoAtualizada(atualizada);
      setConfirmando(false);
      setMensagemSucesso("Legenda aprovada. Ela passa a ser usada no relatório.");
    } catch (err) {
      setErro(err instanceof Error ? err : new Error("Falha ao aprovar a legenda."));
    } finally {
      setIsAprovando(false);
    }
  };

  return (
    <section aria-labelledby={`${idBase}-titulo`} className="space-y-3 rounded-md border bg-muted/30 p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h4 id={`${idBase}-titulo`} className="flex items-center gap-1.5 text-sm font-semibold">
          <Sparkles className="h-4 w-4 text-brand-accent" aria-hidden="true" />
          Legenda com IA
        </h4>
        {foto.status_validacao_ia === "rascunho" ? (
          <Badge variant="secondary">Rascunho — aguardando aprovação</Badge>
        ) : foto.status_validacao_ia === "aprovada" ? (
          <Badge>Aprovada{aprovadaEm ? ` em ${aprovadaEm}` : ""}</Badge>
        ) : null}
      </div>

      <Alert>
        <Info aria-hidden="true" />
        <AlertDescription>
          A legenda gerada pela IA é sempre um rascunho. Ela só entra no relatório depois que você
          revisar o texto e aprovar.
        </AlertDescription>
      </Alert>

      <div className="space-y-1.5">
        <Label htmlFor={`${idBase}-bruta`}>Anotação de campo (opcional)</Label>
        <Textarea
          id={`${idBase}-bruta`}
          value={legendaBruta}
          onChange={(event) => setLegendaBruta(event.target.value)}
          maxLength={LEGENDA_BRUTA_MAX_LENGTH}
          placeholder="Observações do auditor que a IA deve considerar"
          className="min-h-[60px] text-sm"
          disabled={ocupado}
        />
      </div>

      <Button type="button" size="sm" onClick={() => void gerar()} disabled={ocupado} className="gap-1.5">
        {isGerando ? (
          <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
        ) : (
          <Sparkles className="h-4 w-4" aria-hidden="true" />
        )}
        {isGerando ? "Gerando legenda..." : temSugestao ? "Gerar nova sugestão com IA" : "Gerar legenda com IA"}
      </Button>

      <ApiErrorAlert error={erro} />

      {mensagemSucesso ? (
        <p role="status" className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" />
          {mensagemSucesso}
        </p>
      ) : null}

      {temSugestao ? (
        <div className="space-y-3">
          <div className="space-y-1.5">
            <Label htmlFor={`${idBase}-texto`}>Legenda sugerida (editável)</Label>
            <Textarea
              id={`${idBase}-texto`}
              value={texto}
              onChange={(event) => {
                setTexto(event.target.value);
                setConfirmando(false);
              }}
              maxLength={LEGENDA_MAX_LENGTH}
              aria-invalid={textoLimpo.length === 0}
              aria-describedby={`${idBase}-texto-ajuda`}
              className="text-sm"
              disabled={ocupado}
            />
            <p id={`${idBase}-texto-ajuda`} className="text-xs text-muted-foreground">
              {texto.length}/{LEGENDA_MAX_LENGTH} caracteres
              {geradaEm ? ` · sugestão gerada em ${geradaEm}` : ""}
              {foto.nivel_certeza_ia ? ` · nível de certeza: ${NIVEL_CERTEZA_LABEL[foto.nivel_certeza_ia]}` : ""}
            </p>
          </div>

          {alertas.length > 0 ? (
            <div className="space-y-1">
              <p className="flex items-center gap-1.5 text-xs font-semibold">
                <TriangleAlert className="h-3.5 w-3.5 text-brand-accent" aria-hidden="true" />
                Alertas da IA
              </p>
              <ul className="list-inside list-disc text-xs text-muted-foreground">
                {alertas.map((alerta, index) => (
                  <li key={`alerta-${index}`}>{alerta}</li>
                ))}
              </ul>
            </div>
          ) : null}

          {pendencias.length > 0 ? (
            <div className="space-y-1">
              <p className="text-xs font-semibold">Pendências para revisão</p>
              <ul className="list-inside list-disc text-xs text-muted-foreground">
                {pendencias.map((pendencia, index) => (
                  <li key={`pendencia-${index}`}>{pendencia}</li>
                ))}
              </ul>
            </div>
          ) : null}

          {confirmando ? (
            <Alert>
              <CheckCircle2 aria-hidden="true" />
              <AlertTitle>Confirmar aprovação</AlertTitle>
              <AlertDescription className="space-y-2">
                <p>
                  Esta legenda passará a ser usada no relatório, registrada em seu nome:
                </p>
                <blockquote className="border-l-2 pl-2 italic">{textoLimpo}</blockquote>
                <div className="flex flex-wrap gap-2">
                  <Button type="button" size="sm" onClick={() => void aprovar()} disabled={!podeAprovar} className="gap-1.5">
                    {isAprovando ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> : null}
                    {isAprovando ? "Aprovando..." : "Confirmar aprovação"}
                  </Button>
                  <Button type="button" size="sm" variant="outline" onClick={() => setConfirmando(false)} disabled={isAprovando}>
                    Voltar e revisar
                  </Button>
                </div>
              </AlertDescription>
            </Alert>
          ) : (
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={() => setConfirmando(true)}
              disabled={!podeAprovar}
              className="gap-1.5"
            >
              <CheckCircle2 className="h-4 w-4" aria-hidden="true" />
              Aprovar legenda
            </Button>
          )}
          {textoLimpo.length === 0 ? (
            <p className="text-xs text-destructive">Escreva a legenda antes de aprovar.</p>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
