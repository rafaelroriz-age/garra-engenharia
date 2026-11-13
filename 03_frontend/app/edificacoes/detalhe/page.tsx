"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useIdParam } from "@/lib/use-id-param";
import Link from "next/link";
import { ArrowLeft, FileUp, Paperclip, Pencil } from "lucide-react";

import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ApiErrorAlert } from "@/components/api-error-alert";
import { api, ApiError } from "@/lib/api-client";
import { humanizeStatus } from "@/lib/utils";
import type { Contrato, EdificacaoDetail, EdificacaoInput } from "@/lib/types";
import { useUsuarioAtual } from "@/lib/use-usuario-atual";
import { EdificacaoForm } from "../edificacao-form";

interface DocumentoTecnico {
  nome: string;
  tipo: string;
  storage_key: string;
}

/** Detalhe de Edificação com histórico de contratos (RF-01, BL-08) — `GET /edificacoes/{id}`. */
export default function EdificacaoDetailPage() {
  const params = { id: useIdParam() };
  const router = useRouter();
  const [edificacao, setEdificacao] = useState<EdificacaoDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<ApiError | Error | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [tipoDocumento, setTipoDocumento] = useState("");
  const [isUploadingDocumento, setIsUploadingDocumento] = useState(false);
  const [documentoError, setDocumentoError] = useState<ApiError | Error | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { isAuditor } = useUsuarioAtual();

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.get<EdificacaoDetail>(`/edificacoes/${params.id}`);
      setEdificacao(data);
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Falha ao carregar edificação."));
    } finally {
      setIsLoading(false);
    }
  }, [params.id]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleUpdate(input: EdificacaoInput) {
    await api.put<EdificacaoDetail>(`/edificacoes/${params.id}`, input);
    setIsEditing(false);
    await load();
  }

  async function handleUploadDocumento(file: File) {
    setDocumentoError(null);
    if (!tipoDocumento.trim()) {
      setDocumentoError(new Error("Informe o tipo do documento (ex.: Projeto, ART) antes de enviar."));
      return;
    }
    setIsUploadingDocumento(true);
    try {
      const formData = new FormData();
      formData.append("arquivo", file);
      formData.append("tipo", tipoDocumento.trim());
      await api.post<EdificacaoDetail>(`/edificacoes/${params.id}/documentos`, formData, { raw: true });
      setTipoDocumento("");
      await load();
    } catch (err) {
      setDocumentoError(err instanceof Error ? err : new Error("Falha ao enviar documento técnico."));
    } finally {
      setIsUploadingDocumento(false);
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  if (error && !edificacao) {
    return (
      <div>
        <Button variant="ghost" size="sm" className="mb-4 gap-1.5" onClick={() => router.push("/edificacoes")}>
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          Voltar
        </Button>
        <ApiErrorAlert error={error} />
      </div>
    );
  }

  if (!edificacao) return null;

  const contratos: Contrato[] = edificacao.contratos ?? [];
  const documentos = ((edificacao.documentos_tecnicos?.itens as DocumentoTecnico[] | undefined) ?? []) as DocumentoTecnico[];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <Button variant="ghost" size="sm" className="mb-2 gap-1.5" asChild>
            <Link href="/edificacoes">
              <ArrowLeft className="h-4 w-4" aria-hidden="true" />
              Voltar
            </Link>
          </Button>
          <PageHeader title={edificacao.nome} description={edificacao.endereco} />
        </div>
        {!isEditing && isAuditor ? (
          <Button variant="outline" className="gap-1.5" onClick={() => setIsEditing(true)}>
            <Pencil className="h-4 w-4" aria-hidden="true" />
            Editar
          </Button>
        ) : null}
      </div>

      {isEditing ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Editar edificação</CardTitle>
          </CardHeader>
          <CardContent>
            <EdificacaoForm
              initialValue={edificacao}
              submitLabel="Salvar alterações"
              onSubmit={handleUpdate}
              onCancel={() => setIsEditing(false)}
            />
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Dados da edificação</CardTitle>
          </CardHeader>
          <CardContent>
            <dl className="grid grid-cols-1 gap-x-6 gap-y-3 text-sm sm:grid-cols-2">
              <div>
                <dt className="text-muted-foreground">Tipologia</dt>
                <dd className="font-medium">{edificacao.tipologia ?? "—"}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">CEP</dt>
                <dd className="font-medium">{edificacao.cep ?? "—"}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Sistema construtivo</dt>
                <dd className="font-medium">{edificacao.sistema_construtivo ?? "—"}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Área total</dt>
                <dd className="font-medium">
                  {edificacao.area_total_m2 ? `${edificacao.area_total_m2} m²` : "—"}
                </dd>
              </div>
              <div className="sm:col-span-2">
                <dt className="text-muted-foreground">Descrição de pavimentos</dt>
                <dd className="font-medium">{edificacao.descricao_pavimentos ?? "—"}</dd>
              </div>
            </dl>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Documentos técnicos</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {documentos.length > 0 ? (
            <ul className="space-y-1.5 text-sm">
              {documentos.map((documento, index) => (
                <li key={`${documento.storage_key}-${index}`} className="flex items-center gap-2">
                  <Paperclip className="h-4 w-4 shrink-0 text-muted-foreground" aria-hidden="true" />
                  <span className="font-medium">{documento.nome}</span>
                  <Badge variant="outline">{documento.tipo}</Badge>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">Nenhum documento técnico anexado ainda.</p>
          )}

          <ApiErrorAlert error={documentoError} />

          {/* Anexar documento técnico é ato administrativo: só auditor (RN-18). */}
          {isAuditor && (
            <div className="flex flex-wrap items-end gap-2">
              <div className="min-w-[10rem] flex-1 space-y-1.5">
                <Label htmlFor="tipo-documento">Tipo do documento</Label>
                <Input
                  id="tipo-documento"
                  placeholder="Ex.: Projeto arquitetônico, ART"
                  value={tipoDocumento}
                  onChange={(event) => setTipoDocumento(event.target.value)}
                />
              </div>
              <Button
                type="button"
                variant="outline"
                className="gap-1.5"
                disabled={isUploadingDocumento}
                onClick={() => fileInputRef.current?.click()}
              >
                <FileUp className="h-4 w-4" aria-hidden="true" />
                Enviar documento
              </Button>
              <Input
                ref={fileInputRef}
                type="file"
                className="hidden"
                aria-label="Selecionar arquivo do documento técnico"
                onChange={(event) => {
                  const file = event.target.files?.[0];
                  if (file) void handleUploadDocumento(file);
                  event.target.value = "";
                }}
              />
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Histórico de contratos</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {contratos.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Número</TableHead>
                  <TableHead>Tipo de serviço</TableHead>
                  <TableHead>Início</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="sr-only">Ações</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {contratos.map((contrato) => (
                  <TableRow key={contrato.id}>
                    <TableCell className="font-medium">{contrato.numero}</TableCell>
                    <TableCell>{contrato.tipo_servico}</TableCell>
                    <TableCell>{contrato.data_inicio ?? "—"}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{humanizeStatus(contrato.status)}</Badge>
                    </TableCell>
                    <TableCell>
                      <Link
                        href={`/contratos/${contrato.id}`}
                        className="text-sm font-medium text-primary underline-offset-4 hover:underline"
                      >
                        Ver contrato
                      </Link>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <p className="p-6 text-sm text-muted-foreground">
              Nenhum contrato vinculado a esta edificação ainda.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
