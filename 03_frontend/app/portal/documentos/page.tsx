"use client";

import { useCallback, useEffect, useState } from "react";
import { Download, FileText } from "lucide-react";

import { api, ApiError } from "@/lib/api-client";
import type { PortalDownload, PortalRelatorio } from "@/lib/types";
import { PageHeader } from "@/components/page-header";
import { ApiErrorAlert } from "@/components/api-error-alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

/**
 * Portal do Cliente — documentos emitidos (RF-11/RF-13, RN-14, BL-33).
 *
 * O download não expõe o objeto do storage: a API devolve uma URL pré-assinada
 * de curta duração (arquitetura.md Seção 10.1, A02), aberta em nova aba.
 */
export default function PortalDocumentosPage() {
  const [relatorios, setRelatorios] = useState<PortalRelatorio[]>([]);
  const [loading, setLoading] = useState(true);
  const [baixando, setBaixando] = useState<string | null>(null);
  const [error, setError] = useState<ApiError | Error | null>(null);

  useEffect(() => {
    let cancelado = false;
    async function carregar() {
      setLoading(true);
      try {
        const lista = await api.get<PortalRelatorio[]>("/portal/relatorios");
        if (!cancelado) setRelatorios(lista);
      } catch (err) {
        if (!cancelado) {
          setError(err instanceof Error ? err : new Error("Falha ao carregar seus documentos."));
        }
      } finally {
        if (!cancelado) setLoading(false);
      }
    }
    void carregar();
    return () => {
      cancelado = true;
    };
  }, []);

  const baixar = useCallback(async (relatorioId: string, formato: "pdf" | "docx") => {
    setBaixando(`${relatorioId}:${formato}`);
    setError(null);
    try {
      const { url } = await api.get<PortalDownload>(
        `/portal/relatorios/${relatorioId}/download/${formato}`
      );
      window.open(url, "_blank", "noopener,noreferrer");
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Falha ao gerar o link de download."));
    } finally {
      setBaixando(null);
    }
  }, []);

  return (
    <div>
      <PageHeader
        title="Meus documentos"
        description="Relatórios e laudos já emitidos para as suas edificações. Os links de download expiram em poucos minutos por segurança."
      />

      <ApiErrorAlert error={error} />

      {loading ? (
        <div className="space-y-2">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-12 w-full" />
          ))}
        </div>
      ) : relatorios.length === 0 ? (
        <Card>
          <CardContent className="flex items-center gap-2 p-6 text-sm text-muted-foreground">
            <FileText className="h-4 w-4" aria-hidden="true" />
            Nenhum documento emitido até o momento.
          </CardContent>
        </Card>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Edificação</TableHead>
              <TableHead>Contrato</TableHead>
              <TableHead>Tipo</TableHead>
              <TableHead>Versão</TableHead>
              <TableHead>Emitido em</TableHead>
              <TableHead>Download</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {relatorios.map((relatorio) => (
              <TableRow key={relatorio.id}>
                <TableCell>{relatorio.edificacao_nome ?? "—"}</TableCell>
                <TableCell>{relatorio.contrato_numero}</TableCell>
                <TableCell>
                  <Badge variant="outline">{relatorio.tipo}</Badge>
                </TableCell>
                <TableCell className="space-x-2">
                  <span>{relatorio.versao}</span>
                  {relatorio.vigente && <Badge variant="default">Vigente</Badge>}
                </TableCell>
                <TableCell>
                  {relatorio.emitido_em
                    ? new Date(relatorio.emitido_em).toLocaleDateString("pt-BR")
                    : "—"}
                </TableCell>
                <TableCell className="space-x-2">
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={!relatorio.tem_pdf || baixando === `${relatorio.id}:pdf`}
                    onClick={() => void baixar(relatorio.id, "pdf")}
                  >
                    <Download className="mr-1.5 h-3.5 w-3.5" aria-hidden="true" />
                    PDF
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={!relatorio.tem_docx || baixando === `${relatorio.id}:docx`}
                    onClick={() => void baixar(relatorio.id, "docx")}
                  >
                    <Download className="mr-1.5 h-3.5 w-3.5" aria-hidden="true" />
                    DOCX
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  );
}
