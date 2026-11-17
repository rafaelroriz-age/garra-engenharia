"use client";

import { useCallback, useEffect, useState } from "react";
import { ClipboardList, Plus } from "lucide-react";

import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { ApiErrorAlert } from "@/components/api-error-alert";
import { api, ApiError } from "@/lib/api-client";
import { useIdParam } from "@/lib/use-id-param";
import { useModoLeitura } from "@/lib/modo-leitura";
import type { Inspecao, Visita, VisitaInput } from "@/lib/types";
import { VisitaForm } from "./visita-form";
import { VisitaCard } from "./visita-card";

/** Registro de Visitas do RFO (RF-03, RN-01, RN-02, BL-10) — `GET /inspecoes/{id}`. */
export default function VisitasPage() {
  const params = { id: useIdParam() };
  const { bloquearEscrita } = useModoLeitura();
  const [visitas, setVisitas] = useState<Visita[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<ApiError | Error | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const inspecao = await api.get<Inspecao>(`/inspecoes/${params.id}`);
      const ordenadas = [...(inspecao.visitas ?? [])].sort((a, b) => a.seq_numero - b.seq_numero);
      setVisitas(ordenadas);
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Falha ao carregar visitas."));
    } finally {
      setIsLoading(false);
    }
  }, [params.id]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleCreate(input: VisitaInput) {
    await api.post<Visita>(`/inspecoes/${params.id}/visitas`, input);
    setIsCreateOpen(false);
    await load();
  }

  function handleUpdateVisita(updated: Visita) {
    setVisitas((prev) => prev.map((visita) => (visita.id === updated.id ? updated : visita)));
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <PageHeader
          title={`Visitas · Inspeção #${params.id}`}
          description="Registro de visitas do RFO: equipe, serviços executados e medições."
        />
        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <Button className="gap-1.5" onClick={() => setIsCreateOpen(true)} disabled={bloquearEscrita}>
            <Plus className="h-4 w-4" aria-hidden="true" />
            Nova visita
          </Button>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Nova visita</DialogTitle>
              <DialogDescription>
                O número sequencial da visita é atribuído automaticamente.
              </DialogDescription>
            </DialogHeader>
            <VisitaForm
              submitLabel="Registrar visita"
              onSubmit={handleCreate}
              onCancel={() => setIsCreateOpen(false)}
            />
          </DialogContent>
        </Dialog>
      </div>

      <ApiErrorAlert error={error} />

      {isLoading ? (
        <div className="space-y-3">
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-32 w-full" />
        </div>
      ) : visitas.length > 0 ? (
        <div className="space-y-4">
          {visitas.map((visita) => (
            <VisitaCard key={visita.id} visita={visita} onUpdate={handleUpdateVisita} />
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="flex flex-col items-center gap-2 py-10 text-center text-sm text-muted-foreground">
            <ClipboardList className="h-8 w-8 text-muted-foreground" aria-hidden="true" />
            <p>Nenhuma visita registrada ainda. Clique em &quot;Nova visita&quot; para começar.</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
