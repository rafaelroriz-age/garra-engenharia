"use client";

import { useCallback, useEffect, useState } from "react";
import { AlertTriangle, CheckCircle2, Download, FileText, Loader2, Send } from "lucide-react";

import { ApiErrorAlert } from "@/components/api-error-alert";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ApiError, relatorios as relatoriosApi } from "@/lib/api-client";
import type { FormatoRelatorio, RelatorioVersao } from "@/lib/types";
import { humanizeStatus } from "@/lib/utils";
import { TEXTO_INDISPONIVEL, useModoLeitura } from "@/lib/modo-leitura";

const emitidaEm = (versao: RelatorioVersao) =>
  versao.emitido_em ? new Date(versao.emitido_em).toLocaleDateString("pt-BR") : "—";

interface EmissaoVersoesProps {
  inspecaoId: string;
  tipo: string;
  /** Só o auditor emite (`require_auditor`); a listagem e o download valem para a equipe. */
  podeEmitir: boolean;
  /** Há alterações de texto não salvas: a emissão usa só o conteúdo salvo. */
  textosNaoSalvos?: boolean;
}

/**
 * Emissão de nova versão e tabela de versões com download PDF/DOCX (V1-06), sobre
 * `POST /inspecoes/{id}/relatorios/{tipo}`, `GET /inspecoes/{id}/relatorios` e
 * `GET .../relatorios/{relatorio_id}/download/{formato}` (V1-02).
 *
 * O download segue o padrão do portal: a API devolve uma URL pré-assinada de curta
 * duração, aberta em nova aba (o objeto do storage nunca é exposto).
 */
export function EmissaoVersoes({ inspecaoId, tipo, podeEmitir, textosNaoSalvos }: EmissaoVersoesProps) {
  const [versoes, setVersoes] = useState<RelatorioVersao[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erroLista, setErroLista] = useState<ApiError | Error | null>(null);
  const [emitindo, setEmitindo] = useState(false);
  const [erroEmissao, setErroEmissao] = useState<ApiError | Error | null>(null);
  const [emitida, setEmitida] = useState<string | null>(null);
  const [fotosRascunho, setFotosRascunho] = useState(0);
  const [baixando, setBaixando] = useState<string | null>(null);
  const [erroDownload, setErroDownload] = useState<ApiError | Error | null>(null);
  const { bloquearEscrita } = useModoLeitura();

  const carregar = useCallback(async () => {
    setCarregando(true);
    setErroLista(null);
    try {
      setVersoes(await relatoriosApi.listar(inspecaoId));
    } catch (err) {
      setErroLista(err instanceof Error ? err : new Error("Falha ao carregar as versões do relatório."));
    } finally {
      setCarregando(false);
    }
  }, [inspecaoId]);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  async function emitir() {
    setEmitindo(true);
    setErroEmissao(null);
    setEmitida(null);
    setFotosRascunho(0);
    try {
      const nova = await relatoriosApi.emitir(inspecaoId, tipo);
      setEmitida(nova.versao);
      setFotosRascunho(nova.fotos_ia_em_rascunho?.length ?? 0);
      await carregar();
    } catch (err) {
      setErroEmissao(err instanceof Error ? err : new Error("Falha ao emitir o relatório."));
    } finally {
      setEmitindo(false);
    }
  }

  async function baixar(relatorioId: string, formato: FormatoRelatorio) {
    setBaixando(`${relatorioId}:${formato}`);
    setErroDownload(null);
    try {
      const { url } = await relatoriosApi.download(inspecaoId, relatorioId, formato);
      window.open(url, "_blank", "noopener,noreferrer");
    } catch (err) {
      setErroDownload(err instanceof Error ? err : new Error("Falha ao gerar o link de download."));
    } finally {
      setBaixando(null);
    }
  }

  // 422 da emissão: campos obrigatórios ausentes (`{tipo}-contexto-incompleto`) ou tipo não emitível.
  const faltantes =
    erroEmissao instanceof ApiError && erroEmissao.status === 422 ? erroEmissao.errors : [];

  return (
    <Card>
      <CardHeader className="px-4 sm:px-6">
        <CardTitle className="text-base">Versões emitidas</CardTitle>
        <CardDescription>
          Cada emissão gera uma nova versão (V01, V02...) em PDF e DOCX. Os links de download expiram em
          poucos minutos.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4 px-4 sm:px-6">
        {podeEmitir ? (
          <div className="space-y-2">
            <Button type="button" onClick={() => void emitir()} disabled={emitindo || bloquearEscrita} aria-busy={emitindo}>
              {emitindo ? <Loader2 className="animate-spin" aria-hidden="true" /> : <Send aria-hidden="true" />}
              {emitindo ? "Emitindo..." : "Emitir nova versão"}
            </Button>
            <div role="status" aria-live="polite" className="text-sm">
              {emitindo ? (
                <p className="text-muted-foreground">
                  Gerando PDF e DOCX. Isso pode levar algumas dezenas de segundos; não feche a página.
                </p>
              ) : emitida ? (
                <p className="inline-flex items-center gap-1">
                  <CheckCircle2 className="h-4 w-4 text-green-600" aria-hidden="true" />
                  Versão {emitida} emitida.
                </p>
              ) : textosNaoSalvos ? (
                <p className="text-muted-foreground">
                  Há textos não salvos: a emissão usa apenas o conteúdo já salvo.
                </p>
              ) : null}
            </div>
          </div>
        ) : null}

        {fotosRascunho > 0 ? (
          <Alert variant="warning">
            <AlertTriangle aria-hidden="true" />
            <AlertTitle>Legendas IA em rascunho</AlertTitle>
            <AlertDescription>
              {fotosRascunho} foto(s) com legenda IA ainda em rascunho; só legendas aprovadas aparecem no
              relatório.
            </AlertDescription>
          </Alert>
        ) : null}

        {faltantes.length > 0 && erroEmissao instanceof ApiError ? (
          <Alert variant="destructive">
            <AlertTriangle aria-hidden="true" />
            <AlertTitle>{erroEmissao.title}</AlertTitle>
            <AlertDescription>
              <p>Não foi possível emitir. Complete os dados abaixo e tente de novo:</p>
              <ul className="mt-1 list-inside list-disc break-words" aria-label="Campos faltantes">
                {faltantes.map((campo) => (
                  <li key={campo.field}>
                    <code className="font-mono text-xs">{campo.field}</code>: {campo.message}
                  </li>
                ))}
              </ul>
            </AlertDescription>
          </Alert>
        ) : (
          <ApiErrorAlert error={erroEmissao} />
        )}

        <ApiErrorAlert error={erroLista ?? erroDownload} />

        {carregando ? (
          <div className="space-y-2">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        ) : versoes.length === 0 ? (
          <p className="flex items-center gap-2 text-sm text-muted-foreground">
            <FileText className="h-4 w-4" aria-hidden="true" />
            Nenhuma versão emitida ainda.
          </p>
        ) : (
          <Table aria-label="Versões do relatório">
            <TableHeader>
              <TableRow>
                <TableHead className="px-2">Versão</TableHead>
                <TableHead className="hidden px-2 sm:table-cell">Emitida em</TableHead>
                <TableHead className="hidden px-2 sm:table-cell">Status</TableHead>
                <TableHead className="px-2">Arquivos</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {versoes.map((versao) => (
                <TableRow key={versao.id}>
                  <TableCell className="px-2 font-medium">
                    {versao.versao}
                    {versao.tipo !== tipo ? (
                      <span className="block text-xs font-normal text-muted-foreground">{versao.tipo}</span>
                    ) : null}
                    {/* Celular: data e status sob a versão, para a tabela caber sem rolagem (5,5"). */}
                    <span className="block text-xs font-normal text-muted-foreground sm:hidden">
                      {emitidaEm(versao)} · {humanizeStatus(versao.status)}
                    </span>
                  </TableCell>
                  <TableCell className="hidden px-2 sm:table-cell">{emitidaEm(versao)}</TableCell>
                  <TableCell className="hidden px-2 sm:table-cell">
                    <Badge variant="outline" className="px-1.5">
                      {humanizeStatus(versao.status)}
                    </Badge>
                  </TableCell>
                  <TableCell className="px-2">
                    <div className="flex flex-wrap gap-1.5">
                      <Button
                        size="sm"
                        variant="outline"
                        className="px-2"
                        aria-label={`Baixar PDF da versão ${versao.versao}`}
                        disabled={!versao.tem_pdf || baixando === `${versao.id}:pdf` || bloquearEscrita}
                        title={bloquearEscrita ? TEXTO_INDISPONIVEL : undefined}
                        onClick={() => void baixar(versao.id, "pdf")}
                      >
                        <Download aria-hidden="true" />
                        PDF
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="px-2"
                        aria-label={`Baixar DOCX da versão ${versao.versao}`}
                        disabled={!versao.tem_docx || baixando === `${versao.id}:docx` || bloquearEscrita}
                        title={bloquearEscrita ? TEXTO_INDISPONIVEL : undefined}
                        onClick={() => void baixar(versao.id, "docx")}
                      >
                        <Download aria-hidden="true" />
                        DOCX
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
