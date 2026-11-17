"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Plus } from "lucide-react";

import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { PaginationBar } from "@/components/pagination-bar";
import { ApiErrorAlert } from "@/components/api-error-alert";
import { api, ApiError } from "@/lib/api-client";
import { humanizeStatus } from "@/lib/utils";
import {
  normalizePaginated,
  type Contrato,
  type ContratoDetail,
  type ContratoInput,
  type Edificacao,
  type Paginated,
} from "@/lib/types";
import { useUsuarioAtual } from "@/lib/use-usuario-atual";
import { useModoLeitura } from "@/lib/modo-leitura";
import { ContratoForm } from "./contrato-form";

const PAGE_SIZE = 10;

const TIPOS_SERVICO = [
  { value: "RFO", label: "RFO" },
  { value: "LTIP", label: "LTIP" },
  { value: "VISTORIA_CAUTELAR", label: "Vistoria Cautelar" },
  { value: "VISTORIA_RESIDENCIAL", label: "Vistoria Residencial" },
  { value: "RFIP", label: "RFIP" },
];

const STATUS_OPTIONS = [
  { value: "em_andamento", label: "Em andamento" },
  { value: "concluido", label: "Concluído" },
  { value: "cancelado", label: "Cancelado" },
];

/** Listagem de Contratos (RF-02, RF-12, BL-09) — `GET /contratos`, com filtros. */
export default function ContratosPage() {
  const [tipoServico, setTipoServico] = useState("");
  const [status, setStatus] = useState("");
  const [edificacaoId, setEdificacaoId] = useState("");
  const [edificacoes, setEdificacoes] = useState<Edificacao[]>([]);
  const [page, setPage] = useState(1);
  const [data, setData] = useState<Paginated<Contrato> | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<ApiError | Error | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const { isAuditor } = useUsuarioAtual();
  const { bloquearEscrita } = useModoLeitura();

  useEffect(() => {
    api
      .get<Paginated<Edificacao> | Edificacao[]>("/edificacoes?page=1&page_size=100")
      .then((response) => setEdificacoes(normalizePaginated(response).items))
      .catch(() => setEdificacoes([]));
  }, []);

  const loadContratos = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({ page: String(page), page_size: String(PAGE_SIZE) });
      if (tipoServico) params.set("tipo_servico", tipoServico);
      if (status) params.set("status", status);
      if (edificacaoId) params.set("edificacao_id", edificacaoId);
      const response = await api.get<Paginated<Contrato> | Contrato[]>(`/contratos?${params}`);
      setData(normalizePaginated(response));
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Falha ao carregar contratos."));
    } finally {
      setIsLoading(false);
    }
  }, [edificacaoId, page, status, tipoServico]);

  useEffect(() => {
    void loadContratos();
  }, [loadContratos]);

  async function handleCreate(input: ContratoInput) {
    await api.post<ContratoDetail>("/contratos", input);
    setIsCreateOpen(false);
    setPage(1);
    await loadContratos();
  }

  function edificacaoNome(id: string): string {
    return edificacoes.find((edificacao) => edificacao.id === id)?.nome ?? "—";
  }

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <PageHeader
          title="Contratos"
          description="Contratos com múltiplas empresas executoras e NBRs aplicáveis (RF-02, RF-12)."
        />
        {/* Contrato é ato administrativo: só auditor (RN-18). O backend rejeita de qualquer forma. */}
        {isAuditor && (
          <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
            <Button className="gap-1.5" onClick={() => setIsCreateOpen(true)} disabled={bloquearEscrita}>
              <Plus className="h-4 w-4" aria-hidden="true" />
              Novo contrato
            </Button>
            <DialogContent className="max-w-3xl">
              <DialogHeader>
                <DialogTitle>Novo contrato</DialogTitle>
                <DialogDescription>
                  Empresas executoras (RN-06) e ART de Fiscalização (RN-09) obrigatória.
                </DialogDescription>
              </DialogHeader>
              <ContratoForm
                submitLabel="Criar contrato"
                onSubmit={handleCreate}
                onCancel={() => setIsCreateOpen(false)}
              />
            </DialogContent>
          </Dialog>
        )}
      </div>

      <div className="mb-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
        <div className="space-y-1.5">
          <Label htmlFor="filtro-tipo-servico">Tipo de serviço</Label>
          <Select
            id="filtro-tipo-servico"
            value={tipoServico}
            onChange={(event) => {
              setTipoServico(event.target.value);
              setPage(1);
            }}
          >
            <option value="">Todos</option>
            {TIPOS_SERVICO.map((tipo) => (
              <option key={tipo.value} value={tipo.value}>
                {tipo.label}
              </option>
            ))}
          </Select>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="filtro-status">Status</Label>
          <Select
            id="filtro-status"
            value={status}
            onChange={(event) => {
              setStatus(event.target.value);
              setPage(1);
            }}
          >
            <option value="">Todos</option>
            {STATUS_OPTIONS.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </Select>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="filtro-edificacao">Edificação</Label>
          <Select
            id="filtro-edificacao"
            value={edificacaoId}
            onChange={(event) => {
              setEdificacaoId(event.target.value);
              setPage(1);
            }}
          >
            <option value="">Todas</option>
            {edificacoes.map((edificacao) => (
              <option key={edificacao.id} value={edificacao.id}>
                {edificacao.nome}
              </option>
            ))}
          </Select>
        </div>
      </div>

      <ApiErrorAlert error={error} />

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="space-y-2 p-6">
              <Skeleton className="h-8 w-full" />
              <Skeleton className="h-8 w-full" />
              <Skeleton className="h-8 w-full" />
            </div>
          ) : data && data.items.length > 0 ? (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Número</TableHead>
                    <TableHead>Edificação</TableHead>
                    <TableHead>Tipo de serviço</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="sr-only">Ações</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.items.map((contrato) => (
                    <TableRow key={contrato.id}>
                      <TableCell className="font-medium">
                        <Link
                          href={`/contratos/detalhe?id=${contrato.id}`}
                          className="text-primary underline-offset-4 hover:underline"
                        >
                          {contrato.numero}
                        </Link>
                      </TableCell>
                      <TableCell>{contrato.edificacao_nome ?? edificacaoNome(contrato.edificacao_id)}</TableCell>
                      <TableCell>{contrato.tipo_servico}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{humanizeStatus(contrato.status)}</Badge>
                      </TableCell>
                      <TableCell>
                        <Link
                          href={`/contratos/detalhe?id=${contrato.id}`}
                          className="text-sm font-medium text-primary underline-offset-4 hover:underline"
                        >
                          Ver detalhes
                        </Link>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              <PaginationBar page={data.page} pageSize={data.page_size} total={data.total} onPageChange={setPage} />
            </>
          ) : (
            <p className="p-6 text-sm text-muted-foreground">
              Nenhum contrato cadastrado ainda. Clique em &quot;Novo contrato&quot; para começar.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
