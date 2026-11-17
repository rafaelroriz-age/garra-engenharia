"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { AlertTriangle, Building2, CheckCircle2, ClipboardList, XCircle } from "lucide-react";

import { api, ApiError } from "@/lib/api-client";
import { normalizePaginated } from "@/lib/types";
import type { DashboardEdificacao, Edificacao, Paginated } from "@/lib/types";
import { PageHeader } from "@/components/page-header";
import { ApiErrorAlert } from "@/components/api-error-alert";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/prancha/empty-state";
import { KpiTile } from "@/components/prancha/kpi-tile";
import { cn } from "@/lib/utils";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";

/**
 * Dashboard de saúde por edificação/sistema predial (RF-07, BL-16).
 * Consome `GET /edificacoes/{id}/dashboard` (agregados cacheados ~60s no
 * backend, arquitetura.md Seção 10.4) — nenhuma agregação é feita aqui.
 *
 * `useSearchParams()` exige um limite de Suspense (Next.js App Router) para
 * não forçar toda a rota a renderização client-only durante o build estático.
 */
export default function DashboardPage() {
  return (
    <Suspense fallback={<DashboardSkeleton />}>
      <DashboardContent />
    </Suspense>
  );
}

function KpiSkeletonGrid() {
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4" aria-hidden="true">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="rounded-lg border bg-card px-4 pb-3 pt-3.5">
          <Skeleton className="h-3 w-24" />
          <Skeleton className="mt-3 h-8 w-16" />
          <Skeleton className="mt-3 h-1.5 w-full" />
        </div>
      ))}
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div>
      <PageHeader
        eyebrow="Visão geral"
        title="Dashboard"
        description="Indicadores de saúde por edificação e sistema predial."
      />
      <KpiSkeletonGrid />
    </div>
  );
}

function DashboardContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const edificacaoId = searchParams.get("edificacaoId") ?? "";

  const [edificacoes, setEdificacoes] = useState<Edificacao[]>([]);
  const [loadingEdificacoes, setLoadingEdificacoes] = useState(true);
  const [dashboard, setDashboard] = useState<DashboardEdificacao | null>(null);
  const [loadingDashboard, setLoadingDashboard] = useState(false);
  const [error, setError] = useState<ApiError | Error | null>(null);

  useEffect(() => {
    let cancelado = false;
    async function carregarEdificacoes() {
      setLoadingEdificacoes(true);
      try {
        const data = await api.get<Paginated<Edificacao> | Edificacao[]>("/edificacoes");
        if (cancelado) return;
        const lista = normalizePaginated<Edificacao>(data).items;
        setEdificacoes(lista);
        if (!edificacaoId && lista.length > 0) {
          router.replace(`/dashboard?edificacaoId=${lista[0].id}`);
        }
      } catch (err) {
        if (!cancelado) setError(err instanceof Error ? err : new Error("Falha ao carregar edificações."));
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

  const carregarDashboard = useCallback(async () => {
    if (!edificacaoId) {
      setDashboard(null);
      return;
    }
    setLoadingDashboard(true);
    setError(null);
    try {
      const data = await api.get<DashboardEdificacao>(`/edificacoes/${edificacaoId}/dashboard`);
      setDashboard(data);
    } catch (err) {
      setDashboard(null);
      setError(err instanceof Error ? err : new Error("Falha ao carregar o dashboard."));
    } finally {
      setLoadingDashboard(false);
    }
  }, [edificacaoId]);

  useEffect(() => {
    void carregarDashboard();
  }, [carregarDashboard]);

  const totalConforme = dashboard?.conformidade_por_sistema.reduce((soma, item) => soma + item.conforme, 0) ?? 0;
  const totalNaoConforme =
    dashboard?.conformidade_por_sistema.reduce((soma, item) => soma + item.nao_conforme, 0) ?? 0;
  const totalCritico = dashboard?.grau_risco_por_sistema.reduce((soma, item) => soma + item.critico, 0) ?? 0;
  const totalOcorrencias = totalConforme + totalNaoConforme;

  const pct = (parte: number) => (totalOcorrencias > 0 ? Math.round((parte / totalOcorrencias) * 100) : 0);

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <PageHeader
          eyebrow="Visão geral"
          className="mb-0"
          title="Dashboard"
          description="Indicadores de saúde por edificação e sistema predial: proporção Conforme/Não Conforme, distribuição por Grau de Risco e gravidade GUT média por subsistema."
        />
        <div className="w-full space-y-2 sm:w-auto sm:min-w-64">
          <Label htmlFor="dashboard-edificacao">Edificação</Label>
          <Select
            id="dashboard-edificacao"
            value={edificacaoId}
            disabled={loadingEdificacoes || edificacoes.length === 0}
            onChange={(event) => router.replace(`/dashboard?edificacaoId=${event.target.value}`)}
          >
            {edificacoes.length === 0 ? <option value="">Nenhuma edificação cadastrada</option> : null}
            {edificacoes.map((edificacao) => (
              <option key={edificacao.id} value={edificacao.id}>
                {edificacao.nome}
              </option>
            ))}
          </Select>
        </div>
      </div>

      {!loadingEdificacoes && edificacoes.length === 0 ? (
        <EmptyState icon={Building2}>
          Nenhuma edificação cadastrada ainda. Cadastre em{" "}
          <Link href="/edificacoes" className="font-medium text-primary underline underline-offset-4">
            Edificações
          </Link>
          .
        </EmptyState>
      ) : (
        <>
          <ApiErrorAlert error={error} />

          {loadingDashboard ? (
            <KpiSkeletonGrid />
          ) : dashboard ? (
            <>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <KpiTile index={0} label="Total de ocorrências" value={totalOcorrencias} tone="primary" />
                <KpiTile
                  index={1}
                  label="Conforme"
                  icon={CheckCircle2}
                  tone="ok"
                  value={totalConforme}
                  suffix={`(${pct(totalConforme)}%)`}
                  ratio={totalOcorrencias > 0 ? totalConforme / totalOcorrencias : 0}
                />
                <KpiTile
                  index={2}
                  label="Não Conforme"
                  icon={XCircle}
                  tone="atencao"
                  value={totalNaoConforme}
                  suffix={`(${pct(totalNaoConforme)}%)`}
                  ratio={totalOcorrencias > 0 ? totalNaoConforme / totalOcorrencias : 0}
                />
                <KpiTile
                  index={3}
                  label="Ocorrências em Grau Crítico"
                  icon={AlertTriangle}
                  tone="critico"
                  value={totalCritico}
                  emphasis={totalCritico > 0}
                  ratio={totalOcorrencias > 0 ? totalCritico / totalOcorrencias : 0}
                />
              </div>

              <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-2">
                <Card className="animate-reveal [animation-delay:200ms]">
                  <CardHeader className="flex-row items-baseline gap-3 space-y-0 border-b border-foreground/15 pb-3 sm:pb-3">
                    <span aria-hidden="true" className="dado text-xs font-medium text-sinal-ink">
                      02 —
                    </span>
                    <CardTitle className="text-base">Conformidade e Grau de Risco por sistema</CardTitle>
                  </CardHeader>
                  <CardContent className="p-0 sm:p-0">
                    {dashboard.conformidade_por_sistema.length === 0 ? (
                      <p className="p-5 text-sm text-muted-foreground sm:p-6">Nenhuma ocorrência registrada ainda.</p>
                    ) : (
                      <ul>
                        {dashboard.conformidade_por_sistema.map((item) => {
                          const risco = dashboard.grau_risco_por_sistema.find(
                            (r) => r.sistema_id === item.sistema_id
                          );
                          const proporcaoConforme = item.total > 0 ? (item.conforme / item.total) * 100 : 0;
                          const critico = risco?.critico ?? 0;
                          return (
                            <li
                              key={item.sistema_id}
                              className={cn(
                                "relative space-y-2 border-b border-border px-5 py-3.5 last:border-b-0 sm:px-6",
                                critico > 0 && "bg-sev-critico/[0.05]"
                              )}
                            >
                              {critico > 0 ? (
                                <span aria-hidden="true" className="absolute inset-y-0 left-0 w-[3px] bg-sev-critico" />
                              ) : null}
                              <div className="flex items-center justify-between gap-2">
                                <span className="text-sm font-semibold">{item.sistema_nome}</span>
                                {critico > 0 ? (
                                  <Badge variant="destructive">{critico} crítico(s)</Badge>
                                ) : null}
                              </div>
                              <div
                                className="relative h-2 w-full overflow-hidden bg-sev-atencao/25"
                                role="progressbar"
                                aria-valuenow={Math.round(proporcaoConforme)}
                                aria-valuemin={0}
                                aria-valuemax={100}
                                aria-label={`${item.sistema_nome}: ${Math.round(proporcaoConforme)}% conforme`}
                              >
                                <div
                                  className="h-full origin-left bg-sev-ok animate-regua-fill"
                                  style={{ width: `${proporcaoConforme}%` }}
                                />
                                <div
                                  aria-hidden="true"
                                  className="pointer-events-none absolute inset-0 bg-[linear-gradient(90deg,hsl(var(--card))_1px,transparent_1px)] bg-[length:10%_100%]"
                                />
                              </div>
                              <p className="dado text-xs text-muted-foreground">
                                {item.conforme} conforme · {item.nao_conforme} não conforme
                                {risco ? (
                                  <>
                                    {" · "}
                                    {risco.minimo} mínimo, {risco.medio} médio, {risco.critico} crítico
                                  </>
                                ) : null}
                              </p>
                            </li>
                          );
                        })}
                      </ul>
                    )}
                  </CardContent>
                </Card>

                <Card className="animate-reveal [animation-delay:260ms]">
                  <CardHeader className="flex-row items-baseline gap-3 space-y-0 border-b border-foreground/15 pb-3 sm:pb-3">
                    <span aria-hidden="true" className="dado text-xs font-medium text-sinal-ink">
                      03 —
                    </span>
                    <CardTitle className="text-base">Gravidade GUT média por subsistema</CardTitle>
                  </CardHeader>
                  <CardContent className="p-0 sm:p-0">
                    {dashboard.gravidade_por_subsistema.length === 0 ? (
                      <p className="p-5 text-sm text-muted-foreground sm:p-6">Nenhum dado de gravidade disponível ainda.</p>
                    ) : (
                      <ul>
                        {dashboard.gravidade_por_subsistema
                          .slice()
                          .sort((a, b) => b.media_gravidade - a.media_gravidade)
                          .map((item) => (
                            <li
                              key={item.subsistema_id}
                              className="grid grid-cols-[minmax(0,1fr)_auto] items-center gap-x-3 gap-y-1.5 border-b border-border px-5 py-2.5 text-sm last:border-b-0 sm:px-6"
                            >
                              <span className="min-w-0">
                                {item.subsistema_nome}
                                {item.sistema_nome ? (
                                  <span className="text-muted-foreground"> · {item.sistema_nome}</span>
                                ) : null}
                              </span>
                              <Badge variant={item.media_gravidade >= 4 ? "destructive" : "outline"}>
                                {item.media_gravidade.toFixed(1)}
                              </Badge>
                              {/* Escala GUT 1–5 (decorativa; o valor está no badge) */}
                              <span aria-hidden="true" className="col-span-2 flex h-1 gap-px">
                                {Array.from({ length: 5 }).map((_, i) => (
                                  <span
                                    key={i}
                                    className={cn(
                                      "flex-1",
                                      i < Math.round(item.media_gravidade)
                                        ? item.media_gravidade >= 4
                                          ? "bg-sev-critico"
                                          : item.media_gravidade >= 3
                                            ? "bg-sev-atencao"
                                            : "bg-primary"
                                        : "bg-foreground/10"
                                    )}
                                  />
                                ))}
                              </span>
                            </li>
                          ))}
                      </ul>
                    )}
                  </CardContent>
                </Card>
              </div>
            </>
          ) : null}
        </>
      )}

      <p className="mt-8 flex flex-wrap items-center gap-x-6 gap-y-2 border-t border-foreground/15 pt-4 text-sm text-muted-foreground">
        <span className="inline-flex items-center gap-1.5">
          <Building2 className="h-4 w-4" aria-hidden="true" /> Ver{" "}
          <Link href="/edificacoes" className="font-medium text-primary underline-offset-4 hover:underline">
            edificações
          </Link>
        </span>
        <span className="inline-flex items-center gap-1.5">
          <ClipboardList className="h-4 w-4" aria-hidden="true" /> Ver exemplo de{" "}
          <Link href="/inspecoes/ocorrencias?id=1" className="font-medium text-primary underline-offset-4 hover:underline">
            ocorrências de inspeção
          </Link>
        </span>
      </p>
    </div>
  );
}
