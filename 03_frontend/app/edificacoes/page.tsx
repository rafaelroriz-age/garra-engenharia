"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Plus, Search } from "lucide-react";

import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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
import { normalizePaginated, type Edificacao, type EdificacaoInput, type Paginated } from "@/lib/types";
import { useUsuarioAtual } from "@/lib/use-usuario-atual";
import { EdificacaoForm } from "./edificacao-form";

const PAGE_SIZE = 10;

/** Listagem de Edificações (RF-01, BL-08) — `GET /edificacoes`, paginado e com busca. */
export default function EdificacoesPage() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [data, setData] = useState<Paginated<Edificacao> | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<ApiError | Error | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const { isAuditor } = useUsuarioAtual();

  const loadEdificacoes = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({ page: String(page), page_size: String(PAGE_SIZE) });
      if (search.trim()) {
        // A API filtra `nome` OU `endereco` (busca parcial) — reaproveitamos o mesmo
        // termo digitado em ambos os parâmetros para simular uma busca única.
        params.set("nome", search.trim());
        params.set("endereco", search.trim());
      }
      const response = await api.get<Paginated<Edificacao> | Edificacao[]>(`/edificacoes?${params}`);
      setData(normalizePaginated(response));
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Falha ao carregar edificações."));
    } finally {
      setIsLoading(false);
    }
  }, [page, search]);

  useEffect(() => {
    void loadEdificacoes();
  }, [loadEdificacoes]);

  async function handleCreate(input: EdificacaoInput) {
    await api.post<Edificacao>("/edificacoes", input);
    setIsCreateOpen(false);
    setPage(1);
    await loadEdificacoes();
  }

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <PageHeader
          title="Edificações"
          description="Cadastro das edificações inspecionadas, com histórico de contratos."
        />
        {/* Cadastro é ato administrativo: só auditor (RN-18). O backend rejeita de qualquer forma. */}
        {isAuditor && (
          <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
            <Button className="gap-1.5" onClick={() => setIsCreateOpen(true)}>
              <Plus className="h-4 w-4" aria-hidden="true" />
              Nova edificação
            </Button>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Nova edificação</DialogTitle>
                <DialogDescription>Preencha os dados da edificação.</DialogDescription>
              </DialogHeader>
              <EdificacaoForm
                submitLabel="Criar edificação"
                onSubmit={handleCreate}
                onCancel={() => setIsCreateOpen(false)}
              />
            </DialogContent>
          </Dialog>
        )}
      </div>

      <div className="mb-4 max-w-sm">
        <Label htmlFor="busca-edificacao" className="sr-only">
          Buscar por nome ou endereço
        </Label>
        <div className="relative">
          <Search
            className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
            aria-hidden="true"
          />
          <Input
            id="busca-edificacao"
            placeholder="Buscar por nome ou endereço..."
            className="pl-8"
            value={search}
            onChange={(event) => {
              setSearch(event.target.value);
              setPage(1);
            }}
          />
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
                    <TableHead>Nome</TableHead>
                    <TableHead>Endereço</TableHead>
                    <TableHead>Tipologia</TableHead>
                    <TableHead>Área (m²)</TableHead>
                    <TableHead className="sr-only">Ações</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.items.map((edificacao) => (
                    <TableRow key={edificacao.id}>
                      <TableCell className="font-medium">
                        <Link
                          href={`/edificacoes/detalhe?id=${edificacao.id}`}
                          className="text-primary underline-offset-4 hover:underline"
                        >
                          {edificacao.nome}
                        </Link>
                      </TableCell>
                      <TableCell>{edificacao.endereco}</TableCell>
                      <TableCell>{edificacao.tipologia ?? "—"}</TableCell>
                      <TableCell>{edificacao.area_total_m2 ?? "—"}</TableCell>
                      <TableCell>
                        <Link
                          href={`/edificacoes/detalhe?id=${edificacao.id}`}
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
              Nenhuma edificação cadastrada ainda. Clique em &quot;Nova edificação&quot; para começar.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
