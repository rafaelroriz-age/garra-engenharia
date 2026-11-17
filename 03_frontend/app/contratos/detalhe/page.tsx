"use client";

import { useCallback, useEffect, useState } from "react";
import { useIdParam } from "@/lib/use-id-param";
import Link from "next/link";
import { ArrowLeft, Pencil } from "lucide-react";

import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ApiErrorAlert } from "@/components/api-error-alert";
import { api, ApiError } from "@/lib/api-client";
import { humanizeStatus } from "@/lib/utils";
import type { ContratoDetail, ContratoInput } from "@/lib/types";
import { useUsuarioAtual } from "@/lib/use-usuario-atual";
import { ContratoForm } from "../contrato-form";

/** Detalhe de Contrato com executoras e NBRs (RF-02, RF-12, BL-09) — `GET /contratos/{id}`. */
export default function ContratoDetailPage() {
  const params = { id: useIdParam() };
  const [contrato, setContrato] = useState<ContratoDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<ApiError | Error | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const { isAuditor } = useUsuarioAtual();

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.get<ContratoDetail>(`/contratos/${params.id}`);
      setContrato(data);
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Falha ao carregar contrato."));
    } finally {
      setIsLoading(false);
    }
  }, [params.id]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleUpdate(input: ContratoInput) {
    await api.put<ContratoDetail>(`/contratos/${params.id}`, input);
    setIsEditing(false);
    await load();
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  if (error && !contrato) {
    return (
      <div>
        <Button variant="ghost" size="sm" className="mb-4 gap-1.5" asChild>
          <Link href="/contratos">
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            Voltar
          </Link>
        </Button>
        <ApiErrorAlert error={error} />
      </div>
    );
  }

  if (!contrato) return null;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <Button variant="ghost" size="sm" className="mb-2 gap-1.5" asChild>
            <Link href="/contratos">
              <ArrowLeft className="h-4 w-4" aria-hidden="true" />
              Voltar
            </Link>
          </Button>
          <PageHeader
            title={`Contrato ${contrato.numero}`}
            description={`${contrato.tipo_servico} · Status: ${humanizeStatus(contrato.status)}`}
          />
        </div>
        {!isEditing && isAuditor ? (
          <Button variant="outline" className="gap-1.5" onClick={() => setIsEditing(true)}>
            <Pencil className="h-4 w-4" aria-hidden="true" />
            Editar
          </Button>
        ) : null}
      </div>

      {isEditing ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Editar contrato</CardTitle>
          </CardHeader>
          <CardContent>
            <ContratoForm
              initialValue={contrato}
              submitLabel="Salvar alterações"
              onSubmit={handleUpdate}
              onCancel={() => setIsEditing(false)}
            />
          </CardContent>
        </Card>
      ) : (
        <>
          {contrato.inspecao ? (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Inspeção</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-wrap gap-4 text-sm">
                <Link
                  href={`/inspecoes/visitas?id=${contrato.inspecao.id}`}
                  className="font-medium text-primary underline-offset-4 hover:underline"
                >
                  Visitas
                </Link>
                <Link
                  href={`/inspecoes/ocorrencias?id=${contrato.inspecao.id}`}
                  className="font-medium text-primary underline-offset-4 hover:underline"
                >
                  Ocorrências
                </Link>
                <Link
                  href={`/inspecoes/relatorio?id=${contrato.inspecao.id}`}
                  className="font-medium text-primary underline-offset-4 hover:underline"
                >
                  Relatório
                </Link>
              </CardContent>
            </Card>
          ) : null}

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Dados do contrato</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="grid grid-cols-1 gap-x-6 gap-y-3 text-sm sm:grid-cols-2">
                <div>
                  <dt className="text-muted-foreground">Objeto</dt>
                  <dd className="font-medium">{contrato.objeto ?? "—"}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Data de início</dt>
                  <dd className="font-medium">{contrato.data_inicio ?? "—"}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">Prazo</dt>
                  <dd className="font-medium">{contrato.prazo_dias ? `${contrato.prazo_dias} dias` : "—"}</dd>
                </div>
                <div>
                  <dt className="text-muted-foreground">ART de Fiscalização</dt>
                  <dd className="font-medium">{contrato.art_fiscalizacao ?? "—"}</dd>
                </div>
                <div className="sm:col-span-2">
                  <dt className="text-muted-foreground">Observações gerais</dt>
                  <dd className="font-medium">{contrato.observacoes_gerais ?? "—"}</dd>
                </div>
              </dl>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">
                Empresas executoras
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              {contrato.executores.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Razão social</TableHead>
                      <TableHead>CNPJ</TableHead>
                      <TableHead>ART de Execução</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {contrato.executores.map((executor) => (
                      <TableRow key={executor.id ?? executor.cnpj}>
                        <TableCell className="font-medium">{executor.razao_social}</TableCell>
                        <TableCell>{executor.cnpj}</TableCell>
                        <TableCell>{executor.art_execucao ?? "—"}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <p className="p-6 text-sm text-muted-foreground">Nenhuma empresa executora cadastrada.</p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">NBRs aplicáveis</CardTitle>
            </CardHeader>
            <CardContent>
              {contrato.nbrs.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {contrato.nbrs.map((nbr) => (
                    <Badge key={nbr.id ?? nbr.codigo_nbr} variant="secondary">
                      {nbr.codigo_nbr}
                    </Badge>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">Nenhuma NBR vinculada.</p>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
