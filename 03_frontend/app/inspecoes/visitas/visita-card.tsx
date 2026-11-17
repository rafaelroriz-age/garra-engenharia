"use client";

import { useState } from "react";
import { Pencil, Plus, Users2, Ruler, Camera } from "lucide-react";

import type { Visita, VisitaMaoObra, VisitaMedicao } from "@/lib/types";
import { api } from "@/lib/api-client";
import { useModoLeitura } from "@/lib/modo-leitura";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ApiErrorAlert } from "@/components/api-error-alert";
import { FotoUpload } from "@/components/foto-upload";
import { VisitaForm } from "./visita-form";

interface VisitaCardProps {
  visita: Visita;
  onUpdate: (visita: Visita) => void;
}

/**
 * Card de uma Visita do RFO com sub-formulários para mão de obra e medições
 * (RF-03, BL-10) e upload de fotos vinculadas (RF-05, BL-11).
 */
export function VisitaCard({ visita, onUpdate }: VisitaCardProps) {
  const { bloquearEscrita } = useModoLeitura();
  const [funcao, setFuncao] = useState("");
  const [quantidade, setQuantidade] = useState("");
  const [maoObraError, setMaoObraError] = useState<Error | null>(null);
  const [isAddingMaoObra, setIsAddingMaoObra] = useState(false);

  const [descricaoMedicao, setDescricaoMedicao] = useState("");
  const [quantidadeMedicao, setQuantidadeMedicao] = useState("");
  const [unidadeMedicao, setUnidadeMedicao] = useState("");
  const [medicaoError, setMedicaoError] = useState<Error | null>(null);
  const [isAddingMedicao, setIsAddingMedicao] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [isUpdatingVisit, setIsUpdatingVisit] = useState(false);
  const [editError, setEditError] = useState<Error | null>(null);

  const maoObra = visita.mao_obra ?? [];
  const medicoes = visita.medicoes ?? [];
  const fotos = visita.fotos ?? [];

  async function handleAddMaoObra(event: React.FormEvent) {
    event.preventDefault();
    setMaoObraError(null);
    if (!funcao.trim() || !quantidade || Number(quantidade) <= 0) {
      setMaoObraError(new Error("Informe a função e uma quantidade válida."));
      return;
    }
    setIsAddingMaoObra(true);
    try {
      const novo = await api.post<VisitaMaoObra>(`/visitas/${visita.id}/mao-obra`, {
        funcao: funcao.trim(),
        quantidade: Number(quantidade),
      });
      onUpdate({ ...visita, mao_obra: [...maoObra, novo] });
      setFuncao("");
      setQuantidade("");
    } catch (err) {
      setMaoObraError(err instanceof Error ? err : new Error("Falha ao adicionar mão de obra."));
    } finally {
      setIsAddingMaoObra(false);
    }
  }

  async function handleAddMedicao(event: React.FormEvent) {
    event.preventDefault();
    setMedicaoError(null);
    if (!descricaoMedicao.trim() || !quantidadeMedicao || !unidadeMedicao.trim()) {
      setMedicaoError(new Error("Preencha descrição, quantidade e unidade."));
      return;
    }
    setIsAddingMedicao(true);
    try {
      const nova = await api.post<VisitaMedicao>(`/visitas/${visita.id}/medicoes`, {
        descricao: descricaoMedicao.trim(),
        quantidade: Number(quantidadeMedicao),
        unidade: unidadeMedicao.trim(),
      });
      onUpdate({ ...visita, medicoes: [...medicoes, nova] });
      setDescricaoMedicao("");
      setQuantidadeMedicao("");
      setUnidadeMedicao("");
    } catch (err) {
      setMedicaoError(err instanceof Error ? err : new Error("Falha ao adicionar medição."));
    } finally {
      setIsAddingMedicao(false);
    }
  }

  async function handleUpdateVisit(input: { data: string; servicos_executados: string; observacoes?: string | null }) {
    setEditError(null);
    setIsUpdatingVisit(true);
    try {
      const updated = await api.put<Visita>(`/visitas/${visita.id}`, input);
      onUpdate(updated);
      setIsEditing(false);
    } catch (err) {
      setEditError(err instanceof Error ? err : new Error("Falha ao atualizar visita."));
    } finally {
      setIsUpdatingVisit(false);
    }
  }

  return (
    <Card>
      <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <CardTitle className="text-base">
            Visita #{visita.seq_numero} · {new Date(`${visita.data}T00:00:00`).toLocaleDateString("pt-BR")}
          </CardTitle>
          {visita.servicos_executados ? (
            <p className="mt-1 text-sm text-muted-foreground">{visita.servicos_executados}</p>
          ) : null}
          {visita.observacoes ? (
            <p className="mt-1 text-xs text-muted-foreground">Obs.: {visita.observacoes}</p>
          ) : null}
        </div>
        <Button type="button" variant="outline" size="sm" className="gap-1.5 self-start" onClick={() => setIsEditing(true)} disabled={bloquearEscrita}>
          <Pencil className="h-3.5 w-3.5" aria-hidden="true" />
          Editar visita
        </Button>
      </CardHeader>
      <CardContent className="space-y-6">
        <Dialog open={isEditing} onOpenChange={setIsEditing}>
          <DialogContent className="sm:max-w-xl">
            <DialogHeader>
              <DialogTitle>Editar visita</DialogTitle>
              <DialogDescription>Atualize os dados da visita sem alterar o sequenciamento automático.</DialogDescription>
            </DialogHeader>
            <VisitaForm
              key={visita.id}
              initialValue={{
                data: visita.data,
                servicos_executados: visita.servicos_executados ?? "",
                observacoes: visita.observacoes ?? "",
              }}
              submitLabel={isUpdatingVisit ? "Salvando..." : "Salvar alterações"}
              onSubmit={handleUpdateVisit}
              onCancel={() => setIsEditing(false)}
            />
            <ApiErrorAlert error={editError} />
          </DialogContent>
        </Dialog>
        {/* Equipe (mão de obra) */}
        <section aria-labelledby={`equipe-heading-${visita.id}`}>
          <h3 id={`equipe-heading-${visita.id}`} className="mb-2 flex items-center gap-1.5 text-sm font-semibold">
            <Users2 className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
            Equipe presente
          </h3>
          {maoObra.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Função</TableHead>
                  <TableHead>Quantidade</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {maoObra.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell>{item.funcao}</TableCell>
                    <TableCell>{item.quantidade}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <p className="text-xs text-muted-foreground">Nenhum registro de equipe ainda.</p>
          )}
          <form onSubmit={handleAddMaoObra} className="mt-2 flex flex-wrap items-end gap-2">
            <div className="min-w-[10rem] flex-1 space-y-1">
              <Label htmlFor={`funcao-${visita.id}`} className="text-xs">
                Função
              </Label>
              <Input
                id={`funcao-${visita.id}`}
                value={funcao}
                onChange={(event) => setFuncao(event.target.value)}
                placeholder="Ex.: Pedreiro"
                className="h-8 text-sm"
              />
            </div>
            <div className="w-24 space-y-1">
              <Label htmlFor={`quantidade-mo-${visita.id}`} className="text-xs">
                Qtd.
              </Label>
              <Input
                id={`quantidade-mo-${visita.id}`}
                type="number"
                min="1"
                value={quantidade}
                onChange={(event) => setQuantidade(event.target.value)}
                className="h-8 text-sm"
              />
            </div>
            <Button type="submit" size="sm" variant="outline" className="gap-1.5" disabled={isAddingMaoObra || bloquearEscrita}>
              <Plus className="h-3.5 w-3.5" aria-hidden="true" />
              Adicionar
            </Button>
          </form>
          <ApiErrorAlert error={maoObraError} />
        </section>

        {/* Medições */}
        <section aria-labelledby={`medicoes-heading-${visita.id}`}>
          <h3 id={`medicoes-heading-${visita.id}`} className="mb-2 flex items-center gap-1.5 text-sm font-semibold">
            <Ruler className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
            Medições parciais
          </h3>
          {medicoes.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Descrição</TableHead>
                  <TableHead>Quantidade</TableHead>
                  <TableHead>Unidade</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {medicoes.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell>{item.descricao}</TableCell>
                    <TableCell>{item.quantidade}</TableCell>
                    <TableCell>{item.unidade}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <p className="text-xs text-muted-foreground">Nenhuma medição registrada ainda.</p>
          )}
          <form onSubmit={handleAddMedicao} className="mt-2 flex flex-wrap items-end gap-2">
            <div className="min-w-[10rem] flex-1 space-y-1">
              <Label htmlFor={`descricao-med-${visita.id}`} className="text-xs">
                Descrição
              </Label>
              <Input
                id={`descricao-med-${visita.id}`}
                value={descricaoMedicao}
                onChange={(event) => setDescricaoMedicao(event.target.value)}
                placeholder="Ex.: Reboco externo"
                className="h-8 text-sm"
              />
            </div>
            <div className="w-20 space-y-1">
              <Label htmlFor={`quantidade-med-${visita.id}`} className="text-xs">
                Qtd.
              </Label>
              <Input
                id={`quantidade-med-${visita.id}`}
                type="number"
                step="0.01"
                min="0"
                value={quantidadeMedicao}
                onChange={(event) => setQuantidadeMedicao(event.target.value)}
                className="h-8 text-sm"
              />
            </div>
            <div className="w-20 space-y-1">
              <Label htmlFor={`unidade-med-${visita.id}`} className="text-xs">
                Unidade
              </Label>
              <Input
                id={`unidade-med-${visita.id}`}
                value={unidadeMedicao}
                onChange={(event) => setUnidadeMedicao(event.target.value)}
                placeholder="m²"
                className="h-8 text-sm"
              />
            </div>
            <Button type="submit" size="sm" variant="outline" className="gap-1.5" disabled={isAddingMedicao || bloquearEscrita}>
              <Plus className="h-3.5 w-3.5" aria-hidden="true" />
              Adicionar
            </Button>
          </form>
          <ApiErrorAlert error={medicaoError} />
        </section>

        {/* Fotos (BL-11) */}
        <section aria-labelledby={`fotos-heading-${visita.id}`}>
          <h3 id={`fotos-heading-${visita.id}`} className="mb-2 flex items-center gap-1.5 text-sm font-semibold">
            <Camera className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
            Fotos da visita
            {fotos.length > 0 ? (
              <Badge variant="secondary" className="ml-1">
                {fotos.length}
              </Badge>
            ) : null}
          </h3>
          <FotoUpload visitaId={visita.id} fotos={fotos} onChange={(novasFotos) => onUpdate({ ...visita, fotos: novasFotos })} />
        </section>
      </CardContent>
    </Card>
  );
}
