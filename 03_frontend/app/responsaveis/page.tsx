"use client";

import { useCallback, useEffect, useState } from "react";
import { Plus } from "lucide-react";

import { ApiErrorAlert } from "@/components/api-error-alert";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { ApiError, responsaveis as responsaveisApi } from "@/lib/api-client";
import type { Responsavel, ResponsavelInput } from "@/lib/types";
import { useUsuarioAtual } from "@/lib/use-usuario-atual";
import { ResponsavelForm, TIPOS_RESPONSAVEL } from "./responsavel-form";

const rotuloTipo = (tipo: string) => TIPOS_RESPONSAVEL.find((t) => t.value === tipo)?.label ?? tipo;

/**
 * Responsáveis (fiscal, RTE, responsável legal...) com os dados de assinatura dos
 * laudos (V1-06). A API tem `GET /responsaveis` e `POST /responsaveis` (só auditor);
 * não há rota de edição, então aqui só se lista e cadastra.
 */
export default function ResponsaveisPage() {
  const [lista, setLista] = useState<Responsavel[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<ApiError | Error | null>(null);
  const [criando, setCriando] = useState(false);
  const { isAuditor } = useUsuarioAtual();

  const carregar = useCallback(async () => {
    setCarregando(true);
    setErro(null);
    try {
      setLista(await responsaveisApi.listar());
    } catch (err) {
      setErro(err instanceof Error ? err : new Error("Falha ao carregar responsáveis."));
    } finally {
      setCarregando(false);
    }
  }, []);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  async function criar(input: ResponsavelInput) {
    await responsaveisApi.criar(input);
    setCriando(false);
    await carregar();
  }

  return (
    <div className="min-w-0">
      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <PageHeader
          title="Responsáveis"
          description="Fiscais, responsáveis técnicos e legais. O título, as qualificações e a assinatura aparecem no bloco de assinatura dos laudos."
        />
        {isAuditor ? (
          <Dialog open={criando} onOpenChange={setCriando}>
            <Button className="gap-1.5" onClick={() => setCriando(true)}>
              <Plus className="h-4 w-4" aria-hidden="true" />
              Novo responsável
            </Button>
            <DialogContent className="max-h-[90dvh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Novo responsável</DialogTitle>
                <DialogDescription>Dados de identificação e de assinatura nos laudos.</DialogDescription>
              </DialogHeader>
              <ResponsavelForm onSubmit={criar} onCancel={() => setCriando(false)} />
            </DialogContent>
          </Dialog>
        ) : null}
      </div>

      <ApiErrorAlert error={erro} />

      {carregando ? (
        <div className="space-y-2">
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-16 w-full" />
        </div>
      ) : lista.length === 0 ? (
        <Card>
          <CardContent className="p-6 text-sm text-muted-foreground">Nenhum responsável cadastrado.</CardContent>
        </Card>
      ) : (
        <ul className="space-y-2">
          {lista.map((responsavel) => (
            <li key={responsavel.id}>
              <Card>
                <CardContent className="space-y-1 p-4 text-sm">
                  <p className="break-words font-medium">{responsavel.nome}</p>
                  <p className="text-muted-foreground">
                    {rotuloTipo(responsavel.tipo)}
                    {responsavel.crea ? ` · CREA ${responsavel.crea}` : ""}
                  </p>
                  {responsavel.titulo_profissional ? (
                    <p className="break-words">{responsavel.titulo_profissional}</p>
                  ) : null}
                  {responsavel.qualificacoes && responsavel.qualificacoes.length > 0 ? (
                    <ul className="list-inside list-disc break-words text-muted-foreground">
                      {responsavel.qualificacoes.map((q, i) => (
                        <li key={i}>{q}</li>
                      ))}
                    </ul>
                  ) : null}
                  <p className="text-xs text-muted-foreground">
                    {responsavel.assinatura_storage_key ? "Assinatura cadastrada" : "Sem imagem de assinatura"}
                  </p>
                </CardContent>
              </Card>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
