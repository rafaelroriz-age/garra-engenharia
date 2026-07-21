"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { AlertTriangle, Building2, CheckCircle2, ClipboardList, XCircle } from "lucide-react";

import { api, ApiError } from "@/lib/api-client";
import { normalizePaginated } from "@/lib/types";
import type { DashboardEdificacao, Edificacao, Paginated } from "@/lib/types";
import { PageHeader } from "@/components/page-header";
import { ApiErrorAlert } from "@/components/api-error-alert";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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

function DashboardSkeleton() {
  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="Indicadores de saúde por edificação e sistema predial (RF-07)."
      />
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i} aria-hidden="true">
            <CardHeader className="space-y-2 pb-2">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-7 w-16" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-3 w-32" />
            </CardContent>
          </Card>
        ))}
      </div>
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

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <PageHeader
          title="Dashboard"
          description="Indicadores de saúde por edificação e sistema predial (RF-07): proporção Conforme/Não Conforme, distribuição por Grau de Risco e gravidade GUT média por subsistema."
        />
        <div className="min-w-56 space-y-1.5">
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
        <Card>
          <CardContent className="flex items-center gap-2 p-6 text-sm text-muted-foreground">
            <Building2 className="h-4 w-4" aria-hidden="true" />
            Nenhuma edificação cadastrada ainda. Cadastre em{" "}
            <a href="/edificacoes" className="font-medium text-primary underline-offset-4 hover:underline">
              Edificações
            </a>
            .
          </CardContent>
        </Card>
      ) : (
        <>
          <ApiErrorAlert error={error} />

          {loadingDashboard ? (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <Card key={i} aria-hidden="true">
                  <CardHeader className="space-y-2 pb-2">
                    <Skeleton className="h-4 w-24" />
                    <Skeleton className="h-7 w-16" />
                  </CardHeader>
                  <CardContent>
                    <Skeleton className="h-3 w-32" />
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : dashboard ? (
            <>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium text-muted-foreground">
                      Total de ocorrências
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="text-2xl font-bold">{totalOcorrencias}</CardContent>
                </Card>
                <Card>
                  <CardHeader className="flex-row items-center gap-1.5 space-y-0 pb-2">
                    <CheckCircle2 className="h-4 w-4 text-emerald-600" aria-hidden="true" />
                    <CardTitle className="text-sm font-medium text-muted-foreground">Conforme</CardTitle>
                  </CardHeader>
                  <CardContent className="text-2xl font-bold">
                    {totalConforme}
                    <span className="ml-1.5 text-sm font-normal text-muted-foreground">
                      ({totalOcorrencias > 0 ? Math.round((totalConforme / totalOcorrencias) * 100) : 0}%)
                    </span>
                  </CardContent>
                </Card>
                <Card>
                  <CardHeader className="flex-row items-center gap-1.5 space-y-0 pb-2">
                    <XCircle className="h-4 w-4 text-destructive" aria-hidden="true" />
                    <CardTitle className="text-sm font-medium text-muted-foreground">Não Conforme</CardTitle>
                  </CardHeader>
                  <CardContent className="text-2xl font-bold">
                    {totalNaoConforme}
                    <span className="ml-1.5 text-sm font-normal text-muted-foreground">
                      ({totalOcorrencias > 0 ? Math.round((totalNaoConforme / totalOcorrencias) * 100) : 0}%)
                    </span>
                  </CardContent>
                </Card>
                <Card className={totalCritico > 0 ? "border-destructive" : undefined}>
                  <CardHeader className="flex-row items-center gap-1.5 space-y-0 pb-2">
                    <AlertTriangle className="h-4 w-4 text-destructive" aria-hidden="true" />
                    <CardTitle className="text-sm font-medium text-muted-foreground">
                      Ocorrências em Grau Crítico
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="text-2xl font-bold">{totalCritico}</CardContent>
                </Card>
              </div>

              <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Conformidade e Grau de Risco por sistema</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {dashboard.conformidade_por_sistema.length === 0 ? (
                      <p className="text-sm text-muted-foreground">Nenhuma ocorrência registrada ainda.</p>
                    ) : (
                      dashboard.conformidade_por_sistema.map((item) => {
                        const risco = dashboard.grau_risco_por_sistema.find(
                          (r) => r.sistema_id === item.sistema_id
                        );
                        const proporcaoConforme = item.total > 0 ? (item.conforme / item.total) * 100 : 0;
                        const critico = risco?.critico ?? 0;
                        return (
                          <div
                            key={item.sistema_id}
                            className={`space-y-1.5 rounded-md border p-3 ${critico > 0 ? "border-destructive" : ""}`}
                          >
                            <div className="flex items-center justify-between gap-2">
                              <span className="text-sm font-medium">{item.sistema_nome}</span>
                              {critico > 0 ? (
                                <Badge variant="destructive">{critico} crítico(s)</Badge>
                              ) : null}
                            </div>
                            <div
                              className="h-2 w-full overflow-hidden rounded-full bg-muted"
                              role="progressbar"
                              aria-valuenow={Math.round(proporcaoConforme)}
                              aria-valuemin={0}
                              aria-valuemax={100}
                              aria-label={`${item.sistema_nome}: ${Math.round(proporcaoConforme)}% conforme`}
                            >
                              <div
                                className="h-full bg-emerald-600"
                                style={{ width: `${proporcaoConforme}%` }}
                              />
                            </div>
                            <p className="text-xs text-muted-foreground">
                              {item.conforme} conforme · {item.nao_conforme} não conforme
                              {risco ? (
                                <>
                                  {" · "}
                                  {risco.minimo} mínimo, {risco.medio} médio, {risco.critico} crítico
                                </>
                              ) : null}
                            </p>
                          </div>
                        );
                      })
                    )}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Gravidade GUT média por subsistema</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {dashboard.gravidade_por_subsistema.length === 0 ? (
                      <p className="text-sm text-muted-foreground">Nenhum dado de gravidade disponível ainda.</p>
                    ) : (
                      <ul className="space-y-2">
                        {dashboard.gravidade_por_subsistema
                          .slice()
                          .sort((a, b) => b.media_gravidade - a.media_gravidade)
                          .map((item) => (
                            <li key={item.subsistema_id} className="flex items-center justify-between gap-2 text-sm">
                              <span>
                                {item.subsistema_nome}
                                {item.sistema_nome ? (
                                  <span className="text-muted-foreground"> · {item.sistema_nome}</span>
                                ) : null}
                              </span>
                              <Badge variant={item.media_gravidade >= 4 ? "destructive" : "outline"}>
                                {item.media_gravidade.toFixed(1)}
                              </Badge>
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

      <p className="mt-6 flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-muted-foreground">
        <span className="inline-flex items-center gap-1.5">
          <Building2 className="h-4 w-4" aria-hidden="true" /> Ver{" "}
          <a href="/edificacoes" className="font-medium text-primary underline-offset-4 hover:underline">
            edificações
          </a>
        </span>
        <span className="inline-flex items-center gap-1.5">
          <ClipboardList className="h-4 w-4" aria-hidden="true" /> Ver exemplo de{" "}
          <a href="/inspecoes/1/ocorrencias" className="font-medium text-primary underline-offset-4 hover:underline">
            ocorrências de inspeção
          </a>
        </span>
      </p>
    </div>
  );
}

