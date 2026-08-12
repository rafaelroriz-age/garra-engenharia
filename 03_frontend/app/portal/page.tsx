"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { AlertTriangle, Building2, CalendarDays, ClipboardList } from "lucide-react";

import { api, ApiError } from "@/lib/api-client";
import type { DashboardEdificacao, Edificacao, PortalAcompanhamento } from "@/lib/types";
import { PageHeader } from "@/components/page-header";
import { ApiErrorAlert } from "@/components/api-error-alert";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

/**
 * Portal do Cliente — acompanhamento da auditoria (RF-13, RN-14, BL-32).
 *
 * Consome apenas os endpoints `/portal/*`, que já resolvem o escopo do
 * contratante a partir do token (nenhum id de outro cliente é aceito pela API).
 */
export default function PortalPage() {
  return (
    <Suspense fallback={<PortalSkeleton />}>
      <PortalContent />
    </Suspense>
  );
}

function PortalSkeleton() {
  return (
    <div>
      <PageHeader title="Acompanhamento" description="Situação atual da auditoria da sua edificação." />
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <Card key={i} aria-hidden="true">
            <CardHeader className="space-y-2 pb-2">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-7 w-16" />
            </CardHeader>
          </Card>
        ))}
      </div>
    </div>
  );
}

function formatarData(valor?: string | null): string {
  if (!valor) return "—";
  const data = new Date(valor);
  return Number.isNaN(data.getTime()) ? "—" : data.toLocaleDateString("pt-BR");
}

function grauRiscoVariant(grau?: string | null) {
  if (grau === "CRITICO") return "destructive" as const;
  if (grau === "MEDIO") return "secondary" as const;
  return "outline" as const;
}

function PortalContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const edificacaoId = searchParams.get("edificacaoId") ?? "";

  const [edificacoes, setEdificacoes] = useState<Edificacao[]>([]);
  const [loadingEdificacoes, setLoadingEdificacoes] = useState(true);
  const [acompanhamento, setAcompanhamento] = useState<PortalAcompanhamento | null>(null);
  const [dashboard, setDashboard] = useState<DashboardEdificacao | null>(null);
  const [loadingDados, setLoadingDados] = useState(false);
  const [error, setError] = useState<ApiError | Error | null>(null);

  useEffect(() => {
    let cancelado = false;
    async function carregarEdificacoes() {
      setLoadingEdificacoes(true);
      try {
        const lista = await api.get<Edificacao[]>("/portal/edificacoes");
        if (cancelado) return;
        setEdificacoes(lista);
        if (!edificacaoId && lista.length > 0) {
          router.replace(`/portal?edificacaoId=${lista[0].id}`);
        }
      } catch (err) {
        if (!cancelado) {
          setError(err instanceof Error ? err : new Error("Falha ao carregar suas edificações."));
        }
      } finally {
        if (!cancelado) setLoadingEdificacoes(false);
      }
    }
    void carregarEdificacoes();
    return () => {
      cancelado = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const carregarDados = useCallback(async () => {
    if (!edificacaoId) {
      setAcompanhamento(null);
      setDashboard(null);
      return;
    }
    setLoadingDados(true);
    setError(null);
    try {
      const [dadosAcompanhamento, dadosDashboard] = await Promise.all([
        api.get<PortalAcompanhamento>(`/portal/edificacoes/${edificacaoId}/acompanhamento`),
        api.get<DashboardEdificacao>(`/portal/edificacoes/${edificacaoId}/dashboard`),
      ]);
      setAcompanhamento(dadosAcompanhamento);
      setDashboard(dadosDashboard);
    } catch (err) {
      setAcompanhamento(null);
      setDashboard(null);
      setError(err instanceof Error ? err : new Error("Falha ao carregar o acompanhamento."));
    } finally {
      setLoadingDados(false);
    }
  }, [edificacaoId]);

  useEffect(() => {
    void carregarDados();
  }, [carregarDados]);

  const totalCritico =
    dashboard?.grau_risco_por_sistema.reduce((soma, item) => soma + item.critico, 0) ?? 0;
  const totalVisitas =
    acompanhamento?.contratos.reduce((soma, contrato) => soma + contrato.total_visitas, 0) ?? 0;
  const totalOcorrencias =
    acompanhamento?.contratos.reduce((soma, contrato) => soma + contrato.total_ocorrencias, 0) ?? 0;

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <PageHeader
          title="Acompanhamento"
          description="Situação atual da auditoria contratada: visitas realizadas, ocorrências registradas e distribuição por grau de risco (RF-13)."
        />
        <div className="min-w-56 space-y-1.5">
          <Label htmlFor="portal-edificacao">Edificação</Label>
          <Select
            id="portal-edificacao"
            value={edificacaoId}
            disabled={loadingEdificacoes || edificacoes.length === 0}
            onChange={(event) => router.replace(`/portal?edificacaoId=${event.target.value}`)}
          >
            {edificacoes.length === 0 ? <option value="">Nenhuma edificação vinculada</option> : null}
            {edificacoes.map((edificacao) => (
              <option key={edificacao.id} value={edificacao.id}>
                {edificacao.nome}
              </option>
            ))}
          </Select>
        </div>
      </div>

      <ApiErrorAlert error={error} />

      {!loadingEdificacoes && edificacoes.length === 0 ? (
        <Card>
          <CardContent className="flex items-center gap-2 p-6 text-sm text-muted-foreground">
            <Building2 className="h-4 w-4" aria-hidden="true" />
            Nenhuma edificação vinculada ao seu acesso. Fale com o engenheiro responsável.
          </CardContent>
        </Card>
      ) : loadingDados ? (
        <PortalSkeleton />
      ) : acompanhamento ? (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <Card>
              <CardHeader className="flex-row items-center gap-1.5 space-y-0 pb-2">
                <CalendarDays className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
                <CardTitle className="text-sm font-medium text-muted-foreground">Visitas realizadas</CardTitle>
              </CardHeader>
              <CardContent className="text-2xl font-bold">{totalVisitas}</CardContent>
            </Card>
            <Card>
              <CardHeader className="flex-row items-center gap-1.5 space-y-0 pb-2">
                <ClipboardList className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
                <CardTitle className="text-sm font-medium text-muted-foreground">Ocorrências</CardTitle>
              </CardHeader>
              <CardContent className="text-2xl font-bold">{totalOcorrencias}</CardContent>
            </Card>
            <Card>
              <CardHeader className="flex-row items-center gap-1.5 space-y-0 pb-2">
                <AlertTriangle className="h-4 w-4 text-destructive" aria-hidden="true" />
                <CardTitle className="text-sm font-medium text-muted-foreground">Grau de risco crítico</CardTitle>
              </CardHeader>
              <CardContent className="text-2xl font-bold">{totalCritico}</CardContent>
            </Card>
          </div>

          {acompanhamento.contratos.length === 0 ? (
            <Card className="mt-6">
              <CardContent className="p-6 text-sm text-muted-foreground">
                Nenhum contrato em andamento para esta edificação.
              </CardContent>
            </Card>
          ) : (
            acompanhamento.contratos.map((contrato) => (
              <Card key={contrato.contrato_id} className="mt-6">
                <CardHeader>
                  <CardTitle className="flex flex-wrap items-center gap-2 text-base">
                    Contrato {contrato.numero}
                    <Badge variant="outline">{contrato.tipo_servico}</Badge>
                    <Badge variant="secondary">{contrato.inspecao_status ?? contrato.status}</Badge>
                    <span className="text-sm font-normal text-muted-foreground">
                      Início em {formatarData(contrato.data_inicio)}
                    </span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  <section>
                    <h3 className="mb-2 text-sm font-semibold">Visitas ({contrato.total_visitas})</h3>
                    {contrato.visitas.length === 0 ? (
                      <p className="text-sm text-muted-foreground">Nenhuma visita registrada até o momento.</p>
                    ) : (
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>#</TableHead>
                            <TableHead>Data</TableHead>
                            <TableHead>Serviços executados</TableHead>
                            <TableHead>Fotos</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {contrato.visitas.map((visita) => (
                            <TableRow key={visita.id}>
                              <TableCell>{visita.seq_numero}</TableCell>
                              <TableCell>{formatarData(visita.data)}</TableCell>
                              <TableCell>{visita.servicos_executados ?? "—"}</TableCell>
                              <TableCell>{visita.total_fotos}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    )}
                  </section>

                  <section>
                    <h3 className="mb-2 text-sm font-semibold">
                      Ocorrências ({contrato.total_ocorrencias}) — crítico:{" "}
                      {contrato.ocorrencias_por_grau_risco.critico}, médio:{" "}
                      {contrato.ocorrencias_por_grau_risco.medio}, mínimo:{" "}
                      {contrato.ocorrencias_por_grau_risco.minimo}
                    </h3>
                    {contrato.ocorrencias.length === 0 ? (
                      <p className="text-sm text-muted-foreground">Nenhuma ocorrência registrada até o momento.</p>
                    ) : (
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead>#</TableHead>
                            <TableHead>Sistema</TableHead>
                            <TableHead>Localização</TableHead>
                            <TableHead>Situação</TableHead>
                            <TableHead>Grau de risco</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {contrato.ocorrencias.map((ocorrencia) => (
                            <TableRow key={ocorrencia.id}>
                              <TableCell>{ocorrencia.seq_numero}</TableCell>
                              <TableCell>
                                {ocorrencia.sistema_nome ?? "—"}
                                {ocorrencia.subsistema_nome ? ` / ${ocorrencia.subsistema_nome}` : ""}
                              </TableCell>
                              <TableCell>{ocorrencia.localizacao ?? "—"}</TableCell>
                              <TableCell>{ocorrencia.situacao}</TableCell>
                              <TableCell>
                                <Badge variant={grauRiscoVariant(ocorrencia.grau_risco)}>
                                  {ocorrencia.grau_risco ?? "—"}
                                </Badge>
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    )}
                  </section>
                </CardContent>
              </Card>
            ))
          )}
        </>
      ) : null}
    </div>
  );
}
