import { Plus } from "lucide-react";

import { PageHeader } from "@/components/page-header";
import { UnderConstruction } from "@/components/under-construction";
import { Button } from "@/components/ui/button";

/** Placeholder do CRUD de Contratos (RF-02, RF-12, BL-09). */
export default function ContratosPage() {
  return (
    <div>
      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <PageHeader
          title="Contratos"
          description="Contratos com múltiplas empresas executoras e NBRs aplicáveis (RF-02, RF-12)."
        />
        <Button disabled className="gap-1.5">
          <Plus className="h-4 w-4" aria-hidden="true" />
          Novo contrato
        </Button>
      </div>

      <UnderConstruction requirement="RF-02 · BL-09">
        O cadastro de contratos (empresas executoras, NBRs, vínculo com edificação)
        será implementado na tarefa BL-09, após a modelagem de dados (BL-04).
      </UnderConstruction>
    </div>
  );
}
