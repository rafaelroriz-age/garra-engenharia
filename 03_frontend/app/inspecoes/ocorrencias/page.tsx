"use client";

import { useCallback, useEffect, useState } from "react";
import { AlertTriangle, Pencil, Plus, Trash2 } from "lucide-react";

import { api, ApiError } from "@/lib/api-client";
import { useIdParam } from "@/lib/use-id-param";
import { useModoLeitura } from "@/lib/modo-leitura";
import { normalizePaginated } from "@/lib/types";
import type {
  Localizacao,
  Ocorrencia,
  Paginated,
  SistemaPredialComSubsistemas,
  TipoAnomalia,
  TipoFalha,
} from "@/lib/types";
import {
  classificacaoLabel,
  grauRiscoBadgeVariant,
  grauRiscoLabel,
  GRAU_RISCO_OPTIONS,
  situacaoLabel,
} from "@/lib/ocorrencia-enums";
import { PageHeader } from "@/components/page-header";
import { ApiErrorAlert } from "@/components/api-error-alert";
import { OcorrenciaFormDialog } from "@/components/ocorrencia-form-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

/** Ocorrências por sistema/subsistema, localização e classificação CMM (RF-04, RN-03, RN-05, RN-10, BL-14). */
export default function OcorrenciasPage() {
  const inspecaoId = useIdParam();
  const { bloquearEscrita } = useModoLeitura();

  const [sistemas, setSistemas] = useState<SistemaPredialComSubsistemas[]>([]);
  const [tiposAnomalia, setTiposAnomalia] = useState<TipoAnomalia[]>([]);
  const [tiposFalha, setTiposFalha] = useState<TipoFalha[]>([]);
  const [localizacoes, setLocalizacoes] = useState<Localizacao[]>([]);

  const [ocorrencias, setOcorrencias] = useState<Ocorrencia[]>([]);
  const [todasOcorrencias, setTodasOcorrencias] = useState<Ocorrencia[]>([]);

  const [filtroSistema, setFiltroSistema] = useState("");
  const [filtroGrauRisco, setFiltroGrauRisco] = useState("");

  const [loadingGabarito, setLoadingGabarito] = useState(true);
  const [loadingLista, setLoadingLista] = useState(true);
  const [error, setError] = useState<ApiError | Error | null>(null);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [ocorrenciaEmEdicao, setOcorrenciaEmEdicao] = useState<Ocorrencia | null>(null);

  // Gabarito (sistemas prediais, tipos de anomalia/falha, localizações) — carregado uma vez.
  useEffect(() => {
    let cancelado = false;
    async function carregarGabarito() {
      setLoadingGabarito(true);
      try {
        const [sistemasData, anomaliaData, falhaData, localizacaoData] = await Promise.all([
          api.get<SistemaPredialComSubsistemas[]>("/sistemas-prediais"),
          api.get<TipoAnomalia[]>("/gabarito/tipos-anomalia"),
          api.get<TipoFalha[]>("/gabarito/tipos-falha"),
          api.get<Localizacao[]>("/gabarito/localizacoes"),
        ]);
        if (cancelado) return;
        setSistemas(sistemasData);
        setTiposAnomalia(anomaliaData);
        setTiposFalha(falhaData);
        setLocalizacoes(localizacaoData);
      } catch (err) {
        if (!cancelado) setError(err instanceof Error ? err : new Error("Falha ao carregar o gabarito."));
      } finally {
        if (!cancelado) setLoadingGabarito(false);
      }
    }
    void carregarGabarito();
    return () => {
      cancelado = true;
    };
  }, []);

  // Lista completa (sem filtro) para o painel de cobertura por sistema (RN-10).
  const carregarTodasOcorrencias = useCallback(async () => {
    try {
      const data = await api.get<Paginated<Ocorrencia> | Ocorrencia[]>(
        `/inspecoes/${inspecaoId}/ocorrencias`
      );
      setTodasOcorrencias(normalizePaginated<Ocorrencia>(data).items);
    } catch {
      // painel de cobertura é informativo; falha aqui não deve bloquear a listagem principal
    }
  }, [inspecaoId]);

  // Lista filtrada (sistema/grau de risco) exibida na tabela — filtro aplicado no backend.
  const carregarOcorrencias = useCallback(async () => {
    setLoadingLista(true);
    setError(null);
    try {
      const query = new URLSearchParams();
      if (filtroSistema) query.set("sistema_id", filtroSistema);
      if (filtroGrauRisco) query.set("grau_risco", filtroGrauRisco);
      const queryString = query.toString();
      const data = await api.get<Paginated<Ocorrencia> | Ocorrencia[]>(
        `/inspecoes/${inspecaoId}/ocorrencias${queryString ? `?${queryString}` : ""}`
      );
      setOcorrencias(normalizePaginated<Ocorrencia>(data).items);
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Falha ao carregar as ocorrências."));
    } finally {
      setLoadingLista(false);
    }
  }, [inspecaoId, filtroSistema, filtroGrauRisco]);

  useEffect(() => {
    void carregarOcorrencias();
  }, [carregarOcorrencias]);

  useEffect(() => {
    void carregarTodasOcorrencias();
  }, [carregarTodasOcorrencias]);

  function abrirCriacao() {
    setOcorrenciaEmEdicao(null);
    setDialogOpen(true);
  }

  function abrirEdicao(ocorrencia: Ocorrencia) {
    setOcorrenciaEmEdicao(ocorrencia);
    setDialogOpen(true);
  }

  function handleSaved() {
    void carregarOcorrencias();
    void carregarTodasOcorrencias();
  }

  async function handleExcluir(ocorrencia: Ocorrencia) {
    const sistemaNome = sistemas.find((sistema) => sistema.id === ocorrencia.sistema_id)?.nome ?? "esta ocorrência";
    const confirmado = window.confirm(`Remover a ocorrência de "${sistemaNome}"? Esta ação não pode ser desfeita.`);
    if (!confirmado) return;
    try {
      await api.delete(`/ocorrencias/${ocorrencia.id}`);
      void carregarOcorrencias();
      void carregarTodasOcorrencias();
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Falha ao remover a ocorrência."));
    }
  }

  const sistemasNaoAvaliados = sistemas.filter(
    (sistema) => !todasOcorrencias.some((ocorrencia) => ocorrencia.sistema_id === sistema.id)
  );

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <PageHeader
          title={`Ocorrências · Inspeção #${inspecaoId}`}
          description="Ocorrências por sistema/subsistema, localização e classificação CMM (RF-04)."
        />
        <Button className="gap-1.5" onClick={abrirCriacao} disabled={loadingGabarito || bloquearEscrita}>
          <Plus className="h-4 w-4" aria-hidden="true" />
          Nova ocorrência
        </Button>
      </div>

      {sistemasNaoAvaliados.length > 0 ? (
        <Card className="mb-4 border-amber-300 bg-amber-50 dark:border-amber-900 dark:bg-amber-950">
          <CardHeader className="flex-row items-center gap-2 space-y-0 pb-2">
            <AlertTriangle className="h-4 w-4 text-amber-600 dark:text-amber-500" aria-hidden="true" />
            <CardTitle className="text-sm font-semibold">
              {sistemasNaoAvaliados.length} sistema(s) predial(is) ainda não avaliado(s) (RN-10)
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-1.5 pt-0">
            {sistemasNaoAvaliados.map((sistema) => (
              <Badge key={sistema.id} variant="outline">
                {sistema.nome}
              </Badge>
            ))}
          </CardContent>
        </Card>
      ) : null}

      <div className="mb-4 flex flex-wrap items-end gap-4">
        <div className="min-w-48 space-y-1.5">
          <Label htmlFor="filtro-sistema">Filtrar por sistema</Label>
          <Select
            id="filtro-sistema"
            value={filtroSistema}
            onChange={(event) => setFiltroSistema(event.target.value)}
          >
            <option value="">Todos os sistemas</option>
            {sistemas.map((sistema) => (
              <option key={sistema.id} value={sistema.id}>
                {sistema.nome}
              </option>
            ))}
          </Select>
        </div>
        <div className="min-w-48 space-y-1.5">
          <Label htmlFor="filtro-grau-risco">Filtrar por grau de risco</Label>
          <Select
            id="filtro-grau-risco"
            value={filtroGrauRisco}
            onChange={(event) => setFiltroGrauRisco(event.target.value)}
          >
            <option value="">Todos os graus</option>
            {GRAU_RISCO_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </Select>
        </div>
      </div>

      <ApiErrorAlert error={error} />

      <Card>
        <CardContent className="p-0">
          {loadingLista ? (
            <div className="space-y-2 p-4">
              <Skeleton className="h-9 w-full" />
              <Skeleton className="h-9 w-full" />
              <Skeleton className="h-9 w-full" />
            </div>
          ) : ocorrencias.length === 0 ? (
            <p className="p-6 text-center text-sm text-muted-foreground">
              Nenhuma ocorrência encontrada{filtroSistema || filtroGrauRisco ? " para os filtros aplicados" : ""}.
            </p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Sistema</TableHead>
                  <TableHead>Subsistema</TableHead>
                  <TableHead>Localização</TableHead>
                  <TableHead>Situação</TableHead>
                  <TableHead>Classificação</TableHead>
                  <TableHead>Grau de Risco</TableHead>
                  <TableHead>Prioridade</TableHead>
                  <TableHead>Fotos</TableHead>
                  <TableHead className="text-right">Ações</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {ocorrencias.map((ocorrencia) => {
                  const sistema = sistemas.find((item) => item.id === ocorrencia.sistema_id);
                  const subsistema = sistema?.subsistemas.find((item) => item.id === ocorrencia.subsistema_id);
                  const semFoto = ocorrencia.situacao === "NAO_CONFORME" && (ocorrencia.fotos?.length ?? 0) === 0;
                  return (
                    <TableRow key={ocorrencia.id}>
                      <TableCell>{sistema?.nome ?? "—"}</TableCell>
                      <TableCell>{subsistema?.nome ?? "—"}</TableCell>
                      <TableCell>{ocorrencia.localizacao || "—"}</TableCell>
                      <TableCell>{situacaoLabel(ocorrencia.situacao)}</TableCell>
                      <TableCell>{classificacaoLabel(ocorrencia.classificacao)}</TableCell>
                      <TableCell>
                        <Badge variant={grauRiscoBadgeVariant(ocorrencia.grau_risco)}>
                          {grauRiscoLabel(ocorrencia.grau_risco)}
                        </Badge>
                      </TableCell>
                      <TableCell>{ocorrencia.prioridade ?? "—"}</TableCell>
                      <TableCell>
                        {ocorrencia.fotos?.length ?? 0}
                        {semFoto ? (
                          <span className="ml-1.5 text-xs text-destructive" title="Exigida ao menos 1 foto antes da emissão (RN-03)">
                            sem foto
                          </span>
                        ) : null}
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => abrirEdicao(ocorrencia)}
                          disabled={bloquearEscrita}
                          aria-label={`Editar ocorrência de ${sistema?.nome ?? "sistema"}`}
                        >
                          <Pencil className="h-4 w-4" aria-hidden="true" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="text-destructive hover:text-destructive"
                          onClick={() => void handleExcluir(ocorrencia)}
                          disabled={bloquearEscrita}
                          aria-label={`Excluir ocorrência de ${sistema?.nome ?? "sistema"}`}
                        >
                          <Trash2 className="h-4 w-4" aria-hidden="true" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <OcorrenciaFormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        inspecaoId={inspecaoId}
        ocorrencia={ocorrenciaEmEdicao}
        sistemas={sistemas}
        tiposAnomalia={tiposAnomalia}
        tiposFalha={tiposFalha}
        localizacoes={localizacoes}
        onSaved={handleSaved}
      />
    </div>
  );
}
