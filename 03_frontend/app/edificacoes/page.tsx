import Link from "next/link";
import { Plus } from "lucide-react";

import { PageHeader } from "@/components/page-header";
import { UnderConstruction } from "@/components/under-construction";
import { Button } from "@/components/ui/button";

/** Placeholder do CRUD de Edificações (RF-01, BL-08). */
export default function EdificacoesPage() {
  return (
    <div>
      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <PageHeader
          title="Edificações"
          description="Cadastro das edificações inspecionadas, com badge de saúde e última inspeção (RF-01)."
        />
        <Button disabled className="gap-1.5">
          <Plus className="h-4 w-4" aria-hidden="true" />
          Nova edificação
        </Button>
      </div>

      <UnderConstruction requirement="RF-01 · BL-08">
        A listagem e o formulário de cadastro de edificações serão implementados na
        tarefa BL-08 do backlog, consumindo o endpoint{" "}
        <code className="rounded bg-muted px-1 py-0.5 text-xs">GET /edificacoes</code>{" "}
        do backend.
      </UnderConstruction>

      <p className="mt-4 text-sm text-muted-foreground">
        Enquanto isso, veja o exemplo de navegação de uma inspeção:{" "}
        <Link href="/inspecoes/1/visitas" className="font-medium text-primary underline-offset-4 hover:underline">
          visitas
        </Link>
        ,{" "}
        <Link href="/inspecoes/1/ocorrencias" className="font-medium text-primary underline-offset-4 hover:underline">
          ocorrências
        </Link>{" "}
        e{" "}
        <Link href="/inspecoes/1/relatorio" className="font-medium text-primary underline-offset-4 hover:underline">
          relatório
        </Link>
        .
      </p>
    </div>
  );
}
