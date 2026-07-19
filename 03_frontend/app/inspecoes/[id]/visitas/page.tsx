import { ClipboardList } from "lucide-react";

import { PageHeader } from "@/components/page-header";
import { UnderConstruction } from "@/components/under-construction";

/** Placeholder do registro de Visitas do RFO (RF-03, BL-10). */
export default function VisitasPage({ params }: { params: { id: string } }) {
  return (
    <div>
      <PageHeader
        title={`Visitas · Inspeção #${params.id}`}
        description="Registro de visitas do RFO: equipe, serviços executados e medições (RF-03)."
      />
      <UnderConstruction requirement="RF-03 · BL-10" icon={ClipboardList}>
        A listagem e o formulário de visitas serão implementados na tarefa BL-10,
        após o CRUD de contratos (BL-09).
      </UnderConstruction>
    </div>
  );
}
