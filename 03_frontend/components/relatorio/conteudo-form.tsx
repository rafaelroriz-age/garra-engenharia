"use client";

import { useMemo, useState } from "react";
import { CheckCircle2, ChevronDown, Loader2, Plus, Save, Trash2 } from "lucide-react";

import { ApiErrorAlert } from "@/components/api-error-alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ApiError, conteudo as conteudoApi } from "@/lib/api-client";
import type { ConteudoDados, RelatorioConteudo } from "@/lib/types";
import { agruparTextos } from "./rotulos";

/** Parágrafos (API) ↔ texto do textarea: um parágrafo por bloco, separados por linha em branco. */
const paraTexto = (paragrafos: string[] | undefined) => (paragrafos ?? []).join("\n\n");
const paraParagrafos = (texto: string) =>
  texto
    .split(/\r?\n/)
    .map((linha) => linha.trim())
    .filter(Boolean);

interface CamposSimples {
  data_emissao: string;
  local_emissao: string;
  parecer: string;
  unidade: string;
  datas_vistorias: string[];
  incluir_resumo: boolean;
}

function camposIniciais(dados: ConteudoDados): CamposSimples {
  return {
    data_emissao: dados.data_emissao ?? "",
    local_emissao: dados.local_emissao ?? "",
    parecer: dados.parecer ?? "",
    unidade: dados.unidade ?? "",
    datas_vistorias: dados.datas_vistorias ?? [],
    incluir_resumo: Boolean(dados.incluir_resumo),
  };
}

const vazioParaNull = (valor: string) => (valor.trim() ? valor.trim() : null);

interface ConteudoFormProps {
  inspecaoId: string;
  tipo: string;
  inicial: RelatorioConteudo;
  /** Só o auditor grava (`PUT` exige `require_auditor`); os demais veem em modo leitura. */
  podeEditar: boolean;
  /** Avisa a página se há alterações não salvas (a emissão usa o conteúdo salvo). */
  onDirtyChange?: (dirty: boolean) => void;
}

/**
 * Textos do relatório e campos simples (V1-06), sobre `GET/PUT /inspecoes/{id}/conteudo/{tipo}`.
 *
 * O `PUT` SUBSTITUI o conteúdo salvo: por isso o payload parte de tudo o que a API
 * devolveu (inclusive `metodologia_corretiva`/`fundamentacao_tecnica`, que esta tela
 * não edita) e sobrescreve só o que o usuário pode alterar aqui.
 */
export function ConteudoForm({ inspecaoId, tipo, inicial, podeEditar, onDirtyChange }: ConteudoFormProps) {
  const [base, setBase] = useState<RelatorioConteudo>(inicial);
  const [textos, setTextos] = useState<Record<string, string>>(() =>
    Object.fromEntries(Object.entries(inicial.dados.textos ?? {}).map(([k, v]) => [k, paraTexto(v)]))
  );
  const [campos, setCampos] = useState<CamposSimples>(() => camposIniciais(inicial.dados));
  const [dirty, setDirtyState] = useState(false);
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState<ApiError | Error | null>(null);
  const [salvoEm, setSalvoEm] = useState<string | null>(null);

  const chaves = useMemo(() => Object.keys(inicial.dados.textos ?? {}), [inicial]);
  const grupos = useMemo(() => agruparTextos(tipo, chaves), [tipo, chaves]);

  const temParecer = tipo === "VISTORIA_CAUTELAR";
  const temUnidade = tipo === "VISTORIA_RESIDENCIAL";
  const temDatasVistorias = tipo === "VISTORIA_CAUTELAR" || tipo === "VISTORIA_RESIDENCIAL";
  const temResumo = tipo === "RFIP";

  function marcarAlterado() {
    setSalvoEm(null);
    if (!dirty) {
      setDirtyState(true);
      onDirtyChange?.(true);
    }
  }

  function atualizarCampo<K extends keyof CamposSimples>(campo: K, valor: CamposSimples[K]) {
    setCampos((atual) => ({ ...atual, [campo]: valor }));
    marcarAlterado();
  }

  async function salvar(event: React.FormEvent) {
    event.preventDefault();
    setSalvando(true);
    setErro(null);
    try {
      const dados: ConteudoDados = {
        ...base.dados,
        textos: Object.fromEntries(Object.entries(textos).map(([k, v]) => [k, paraParagrafos(v)])),
        data_emissao: campos.data_emissao || null,
        local_emissao: vazioParaNull(campos.local_emissao),
      };
      if (temParecer) dados.parecer = vazioParaNull(campos.parecer);
      if (temUnidade) dados.unidade = vazioParaNull(campos.unidade);
      if (temDatasVistorias) dados.datas_vistorias = campos.datas_vistorias.filter(Boolean);
      if (temResumo) dados.incluir_resumo = campos.incluir_resumo;

      const resposta = await conteudoApi.salvar(inspecaoId, tipo, dados);
      setBase(resposta);
      setDirtyState(false);
      onDirtyChange?.(false);
      setSalvoEm(
        resposta.atualizado_em
          ? new Date(resposta.atualizado_em).toLocaleString("pt-BR")
          : new Date().toLocaleString("pt-BR")
      );
    } catch (err) {
      setErro(err instanceof Error ? err : new Error("Falha ao salvar os textos do relatório."));
    } finally {
      setSalvando(false);
    }
  }

  const somenteLeitura = !podeEditar;

  return (
    <form onSubmit={salvar} className="space-y-6" aria-label="Conteúdo do relatório">
      <Card>
        <CardHeader className="px-4 sm:px-6">
          <CardTitle className="text-base">Dados da emissão</CardTitle>
          <CardDescription>Usados na capa e no bloco de assinatura.</CardDescription>
        </CardHeader>
        <CardContent className="grid grid-cols-1 gap-4 px-4 sm:grid-cols-2 sm:px-6">
          <div className="space-y-1.5">
            <Label htmlFor="data-emissao">Data de emissão</Label>
            <Input
              id="data-emissao"
              type="date"
              value={campos.data_emissao}
              readOnly={somenteLeitura}
              onChange={(e) => atualizarCampo("data_emissao", e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="local-emissao">Local de emissão</Label>
            <Input
              id="local-emissao"
              maxLength={200}
              placeholder="Ex.: Goiânia-GO"
              value={campos.local_emissao}
              readOnly={somenteLeitura}
              onChange={(e) => atualizarCampo("local_emissao", e.target.value)}
            />
          </div>
          {temUnidade ? (
            <div className="space-y-1.5 sm:col-span-2">
              <Label htmlFor="unidade">Unidade vistoriada</Label>
              <Input
                id="unidade"
                maxLength={200}
                placeholder="Ex.: Apartamento 101"
                value={campos.unidade}
                readOnly={somenteLeitura}
                onChange={(e) => atualizarCampo("unidade", e.target.value)}
              />
            </div>
          ) : null}
          {temDatasVistorias ? (
            <fieldset className="space-y-2 sm:col-span-2">
              <legend className="text-sm font-medium">Datas das vistorias</legend>
              {campos.datas_vistorias.length === 0 ? (
                <p className="text-sm text-muted-foreground">Nenhuma data informada.</p>
              ) : null}
              <ul className="space-y-2">
                {campos.datas_vistorias.map((data, index) => (
                  <li key={index} className="flex items-center gap-2">
                    <Input
                      type="date"
                      aria-label={`Data da vistoria ${index + 1}`}
                      className="min-w-0 flex-1"
                      value={data}
                      readOnly={somenteLeitura}
                      onChange={(e) =>
                        atualizarCampo(
                          "datas_vistorias",
                          campos.datas_vistorias.map((d, i) => (i === index ? e.target.value : d))
                        )
                      }
                    />
                    {podeEditar ? (
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        aria-label={`Remover data da vistoria ${index + 1}`}
                        onClick={() =>
                          atualizarCampo(
                            "datas_vistorias",
                            campos.datas_vistorias.filter((_, i) => i !== index)
                          )
                        }
                      >
                        <Trash2 aria-hidden="true" />
                      </Button>
                    ) : null}
                  </li>
                ))}
              </ul>
              {podeEditar && campos.datas_vistorias.length < 60 ? (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => atualizarCampo("datas_vistorias", [...campos.datas_vistorias, ""])}
                >
                  <Plus aria-hidden="true" />
                  Adicionar data
                </Button>
              ) : null}
            </fieldset>
          ) : null}
          {temParecer ? (
            <div className="space-y-1.5 sm:col-span-2">
              <Label htmlFor="parecer">Parecer técnico (complemento do item 10.1)</Label>
              <Textarea
                id="parecer"
                rows={5}
                maxLength={20000}
                value={campos.parecer}
                readOnly={somenteLeitura}
                onChange={(e) => atualizarCampo("parecer", e.target.value)}
              />
            </div>
          ) : null}
          {temResumo ? (
            <div className="flex items-start gap-2 sm:col-span-2">
              <input
                id="incluir-resumo"
                type="checkbox"
                className="mt-0.5 h-4 w-4 accent-primary"
                checked={campos.incluir_resumo}
                disabled={somenteLeitura}
                onChange={(e) => atualizarCampo("incluir_resumo", e.target.checked)}
              />
              <Label htmlFor="incluir-resumo" className="leading-snug">
                Incluir resumo no relatório
              </Label>
            </div>
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="px-4 sm:px-6">
          <CardTitle className="text-base">Textos do relatório</CardTitle>
          <CardDescription>
            {grupos.length > 0
              ? "Já preenchidos com o texto padrão do laudo. Separe parágrafos com uma linha em branco; um texto vazio remove a seção."
              : "Este tipo de relatório não tem textos editáveis."}
          </CardDescription>
        </CardHeader>
        {grupos.length > 0 ? (
          <CardContent className="space-y-2 px-4 sm:px-6">
            {grupos.map((grupo) => (
              <details key={grupo.titulo} className="group rounded-md border">
                <summary className="flex cursor-pointer list-none items-center justify-between gap-2 px-3 py-2 text-sm font-medium [&::-webkit-details-marker]:hidden">
                  <span className="min-w-0 break-words">{grupo.titulo}</span>
                  <ChevronDown
                    className="h-4 w-4 shrink-0 transition-transform group-open:rotate-180"
                    aria-hidden="true"
                  />
                </summary>
                <div className="space-y-4 border-t px-3 py-3">
                  {grupo.chaves.map(({ chave, rotulo }) => (
                    <div key={chave} className="space-y-1.5">
                      <Label htmlFor={`texto-${chave}`} className="break-words">
                        {rotulo}
                      </Label>
                      <Textarea
                        id={`texto-${chave}`}
                        rows={6}
                        value={textos[chave] ?? ""}
                        readOnly={somenteLeitura}
                        onChange={(e) => {
                          const valor = e.target.value;
                          setTextos((atual) => ({ ...atual, [chave]: valor }));
                          marcarAlterado();
                        }}
                      />
                    </div>
                  ))}
                </div>
              </details>
            ))}
          </CardContent>
        ) : null}
      </Card>

      <ApiErrorAlert error={erro} />

      {podeEditar ? (
        <div className="flex flex-wrap items-center gap-3">
          <Button type="submit" disabled={salvando}>
            {salvando ? <Loader2 className="animate-spin" aria-hidden="true" /> : <Save aria-hidden="true" />}
            {salvando ? "Salvando..." : "Salvar textos"}
          </Button>
          <p className="text-sm text-muted-foreground" role="status" aria-live="polite">
            {salvoEm ? (
              <span className="inline-flex items-center gap-1 text-foreground">
                <CheckCircle2 className="h-4 w-4 text-green-600" aria-hidden="true" />
                Textos salvos em {salvoEm}.
              </span>
            ) : dirty ? (
              "Há alterações não salvas."
            ) : base.salvo ? (
              "Conteúdo salvo para esta inspeção."
            ) : (
              "Usando os textos padrão (ainda não salvos)."
            )}
          </p>
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">Somente o auditor pode alterar os textos do relatório.</p>
      )}
    </form>
  );
}
