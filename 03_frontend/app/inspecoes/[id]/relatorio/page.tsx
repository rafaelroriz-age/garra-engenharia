import { FileDown } from "lucide-react";

import { PageHeader } from "@/components/page-header";
import { UnderConstruction } from "@/components/under-construction";

/** Placeholder da geração/download do relatório (RF-06, BL-12/BL-13). */
export default function RelatorioPage({ params }: { params: { id: string } }) {
  return (
    <div>
      <PageHeader
        title={`Relatório · Inspeção #${params.id}`}
        description="Geração e download do relatório em PDF (WeasyPrint) e DOCX editável (docxtpl)."
      />
      <UnderConstruction requirement="RF-06 · BL-12/BL-13" icon={FileDown}>
        A geração de relatório depende do recebimento do template `.docx` original do
        cliente (bloqueio B-02) — ver BL-12 e BL-13 no backlog.
      </UnderConstruction>
    </div>
  );
}
