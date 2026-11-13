"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useIdParam } from "@/lib/use-id-param";
import { ArrowLeft } from "lucide-react";

import { ApiErrorAlert } from "@/components/api-error-alert";
import { PageHeader } from "@/components/page-header";
import { ConteudoForm } from "@/components/relatorio/conteudo-form";
import { EmissaoVersoes } from "@/components/relatorio/emissao-versoes";
import { TIPOS_RELATORIO } from "@/components/relatorio/rotulos";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { api, ApiError, conteudo as conteudoApi } from "@/lib/api-client";
import type { Inspecao, RelatorioConteudo } from "@/lib/types";
import { useUsuarioAtual } from "@/lib/use-usuario-atual";

/**
 * Relatório da inspeção (RF-06, V1-06): textos do laudo, emissão de nova versão
 * (só auditor) e download das versões em PDF/DOCX.
 *
 * O tipo do relatório é o da inspeção (`GET /inspecoes/{id}`): a API só emite o
 * tipo igual ao da inspeção (409 `inspecao-nao-{tipo}` caso contrário).
 */
export default function RelatorioPage() {
  const params = { id: useIdParam() };
  const inspecaoId = params.id;
  const { isAuditor } = useUsuarioAtual();

  const [inspecao, setInspecao] = useState<Inspecao | null>(null);
  const [conteudo, setConteudo] = useState<RelatorioConteudo | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<ApiError | Error | null>(null);
  const [textosNaoSalvos, setTextosNaoSalvos] = useState(false);

  const carregar = useCallback(async () => {
    setCarregando(true);
    setErro(null);
    try {
      const dados = await api.get<Inspecao>(`/inspecoes/${inspecaoId}`);
      setInspecao(dados);
      setConteudo(await conteudoApi.obter(inspecaoId, dados.tipo.trim().toUpperCase()));
    } catch (err) {
      setErro(err instanceof Error ? err : new Error("Falha ao carregar o relatório."));
    } finally {
      setCarregando(false);
    }
  }, [inspecaoId]);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  const tipo = inspecao?.tipo.trim().toUpperCase() ?? "";
  const voltarHref = inspecao ? `/contratos/detalhe?id=${inspecao.contrato_id}` : "/contratos";

  return (
    <div className="min-w-0 space-y-6">
      <div>
        <Button variant="ghost" size="sm" className="mb-2 gap-1.5" asChild>
          <Link href={voltarHref}>
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            Voltar ao contrato
          </Link>
        </Button>
        <PageHeader
          title="Relatório da inspeção"
          description={
            tipo
              ? `${TIPOS_RELATORIO[tipo] ?? tipo}. Revise os textos, emita uma nova versão e baixe o PDF ou o DOCX.`
              : "Textos do laudo, emissão de versões e download em PDF e DOCX."
          }
        />
      </div>

      {carregando ? (
        <div className="space-y-4">
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-64 w-full" />
        </div>
      ) : (
        <>
          <ApiErrorAlert error={erro} />
          {inspecao ? (
            <EmissaoVersoes
              inspecaoId={inspecaoId}
              tipo={tipo}
              podeEmitir={isAuditor}
              textosNaoSalvos={textosNaoSalvos}
            />
          ) : null}
          {inspecao && conteudo ? (
            <ConteudoForm
              inspecaoId={inspecaoId}
              tipo={tipo}
              inicial={conteudo}
              podeEditar={isAuditor}
              onDirtyChange={setTextosNaoSalvos}
            />
          ) : null}
        </>
      )}
    </div>
  );
}
