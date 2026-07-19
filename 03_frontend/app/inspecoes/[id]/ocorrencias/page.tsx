import { AlertTriangle } from "lucide-react";

import { PageHeader } from "@/components/page-header";
import { UnderConstruction } from "@/components/under-construction";

/** Placeholder das Ocorrências do LTIP (RF-04, BL-14). */
export default function OcorrenciasPage({ params }: { params: { id: string } }) {
  return (
    <div>
      <PageHeader
        title={`Ocorrências · Inspeção #${params.id}`}
        description="Ocorrências por sistema/subsistema, localização e classificação CMM (RF-04)."
      />
      <UnderConstruction requirement="RF-04 · BL-14" icon={AlertTriangle}>
        O cadastro de ocorrências (sistema predial, subsistema, localização, matriz
        GUT) será implementado na tarefa BL-14.
      </UnderConstruction>
    </div>
  );
}
