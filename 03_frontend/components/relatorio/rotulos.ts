/**
 * Rótulos legíveis das chaves de `dados.textos` por tipo de relatório (V1-06).
 *
 * As CHAVES vêm sempre da API (`GET /inspecoes/{id}/conteudo/{tipo}`); aqui só há o
 * título de cada uma, copiado dos templates do backend
 * (`layout.json` de `04_backend/templates/vistoria_cautelar` e `vistoria_residencial`,
 * `ltip_pipeline.SECOES_TEXTO`),
 * e o agrupamento por seção numerada. Chave que a API devolver e não estiver
 * aqui aparece no grupo "Outros textos" com um rótulo derivado do nome.
 */

export const TIPOS_RELATORIO: Record<string, string> = {
  RFO: "Relatório de Fiscalização de Obra (RFO)",
  LTIP: "Laudo Técnico de Inspeção Predial (LTIP)",
  VISTORIA_CAUTELAR: "Vistoria Cautelar de Recebimento",
  VISTORIA_RESIDENCIAL: "Vistoria de Imóvel Residencial",
  RFIP: "Relatório Fotográfico de Inspeção Predial",
};

export interface GrupoTextos {
  titulo: string;
  chaves: { chave: string; rotulo: string }[];
}

type Secao = [titulo: string, chaves: [chave: string, rotulo: string][]];

const LTIP: Secao[] = [
  ["Introdução", [["introducao", "Introdução"]]],
  ["Considerações preliminares", [["consideracoes_preliminares", "Considerações preliminares"]]],
  ["Objetivo", [["objetivo", "Objetivo"]]],
  ["Objeto", [["objeto", "Objeto"]]],
  ["Metodologia", [["metodologia", "Metodologia"]]],
  ["Documentação analisada", [["documentacao_analisada", "Documentação analisada"]]],
  ["Conclusão", [["conclusao", "Conclusão"]]],
];

const VISTORIA_CAUTELAR: Secao[] = [
  ["1. Introdução", [
    ["introducao", "1. Introdução"],
    ["historico_e_contexto_da_diligencia", "1.1 Histórico e contexto da diligência"],
  ]],
  ["2. Considerações preliminares", [
    ["consideracoes_preliminares", "2. Considerações preliminares"],
    ["consideracoes_preliminares_geral", "2.1 Geral"],
    ["pressupostos_ressalvas_e_fatores_limitantes", "2.2 Pressupostos, ressalvas e fatores limitantes"],
  ]],
  ["3. Objetivo", [
    ["objetivo", "3. Objetivo"],
    ["objetivo_geral", "3.1 Geral"],
    ["especifico", "3.2 Específico"],
  ]],
  ["4. Objeto", [
    ["objeto", "4. Objeto"],
    ["objeto_geral", "4.1 Geral"],
    ["identificacao", "4.2 Identificação"],
  ]],
  ["5. Da realização da inspeção", [
    ["da_realizacao_da_inspecao", "5. Da realização da inspeção"],
    ["apresentacao_do_responsavel_tecnico", "5.1 Apresentação do responsável técnico"],
    ["datas_das_vistorias", "5.2 Datas das vistorias"],
  ]],
  ["6. Metodologia", [
    ["metodologia", "6. Metodologia"],
    ["classificacao_da_inspecao_quanto_ao_nivel", "6.1 Classificação da inspeção quanto ao nível"],
    ["criterio_de_classificacao_tecnica_dos_achados", "6.2 Critério de classificação técnica dos achados"],
    ["levantamento_de_dados_e_documentacao", "6.3 Levantamento de dados e documentação"],
    ["ensaios_tecnicos_instrumentais_realizados", "6.4 Ensaios técnicos instrumentais realizados"],
  ]],
  ["7. Desenvolvimento das atividades da inspeção", [
    ["desenvolvimento_das_atividades_da_inspecao", "7. Desenvolvimento das atividades da inspeção"],
    ["sistemas_construtivos_inspecionados", "7.1 Sistemas construtivos inspecionados"],
    ["dinamica_de_campo_e_correcoes_em_tempo_real", "7.2 Dinâmica de campo e correções em tempo real"],
  ]],
  ["8. Relatório fotográfico", [["relatorio_fotografico", "8. Relatório fotográfico"]]],
  ["9. Análise e considerações técnicas", [
    ["analise_e_consideracoes_tecnicas", "9. Análise e considerações técnicas"],
    [
      "correlacao_tecnica_entre_origem_provavel_repercussao_funcional_e_responsabilidade",
      "9.8 Correlação técnica entre origem provável, repercussão funcional e responsabilidade",
    ],
  ]],
  ["10. Conclusão e considerações finais", [
    ["conclusao_e_consideracoes_finais", "10. Conclusão e considerações finais"],
    ["parecer_tecnico", "10.1 Parecer técnico"],
    ["plano_de_correcoes_remanescentes", "10.2 Plano de correções remanescentes"],
    ["prazos_e_condicionantes_para_o_recebimento_definitivo", "10.3 Prazos e condicionantes para o recebimento definitivo"],
  ]],
  ["11. Encerramento", [["encerramento", "11. Encerramento"]]],
  ["12. Referências bibliográficas", [["referencias_bibliograficas", "12. Referências bibliográficas"]]],
];

const VISTORIA_RESIDENCIAL: Secao[] = [
  ["1. Introdução", [["s1", "1. Introdução"], ["s1_1", "1.1 Histórico"]]],
  ["2. Considerações preliminares", [
    ["s2", "2. Considerações preliminares"],
    ["s2_1", "2.1 Geral"],
    ["s2_2", "2.2 Pressupostos, ressalvas e fatores limitantes"],
  ]],
  ["3. Objetivo", [["s3", "3. Objetivo"], ["s3_1", "3.1 Geral"], ["s3_2", "3.2 Específico"]]],
  ["4. Objeto", [
    ["s4", "4. Objeto"],
    ["s4_1", "4.1 Geral"],
    ["s4_2", "4.2 Identificação"],
    ["s4_2_1", "4.2.1 Tipologia"],
    ["s4_2_2", "4.2.2 Caracterização"],
    ["s4_2_3", "4.2.3 Localização"],
    ["s4_2_4", "4.2.4 Descrição qualitativa"],
    ["s4_2_4_1", "4.2.4.1 Região"],
    ["s4_2_4_2", "4.2.4.2 Valorização imobiliária"],
  ]],
  ["5. Da realização da inspeção", [
    ["s5", "5. Da realização da inspeção"],
    ["s5_1", "5.1 Responsável técnico"],
    ["s5_2", "5.2 Datas das vistorias"],
  ]],
  ["6. Metodologia", [
    ["s6", "6. Metodologia"],
    ["s6_1", "6.1 Classificação da inspeção quanto ao nível"],
    ["s6_2", "6.2 Critério de classificação técnica dos achados"],
    ["s6_3", "6.3 Levantamento de dados e documentação"],
  ]],
  ["7. Desenvolvimento das atividades da inspeção", [
    ["s7", "7. Desenvolvimento das atividades da inspeção"],
    ["s7_1", "7.1 Sistemas construtivos inspecionados"],
  ]],
  ["8. Relatório fotográfico", [["s8", "8. Relatório fotográfico"]]],
  ["9. Análise e considerações técnicas", [["s9", "9. Análise e considerações técnicas"]]],
  ["10. Conclusão e considerações finais", [["s10", "10. Conclusão e considerações finais"]]],
  ["11. Encerramento", [["s11", "11. Encerramento"]]],
  ["12. Referências bibliográficas", [["s12", "12. Referências bibliográficas"]]],
];

const SECOES_POR_TIPO: Record<string, Secao[]> = { LTIP, VISTORIA_CAUTELAR, VISTORIA_RESIDENCIAL };

/** "consideracoes_preliminares" → "Consideracoes preliminares" (fallback sem acentos). */
export function rotuloDerivado(chave: string): string {
  const texto = chave.replace(/_/g, " ").trim();
  return texto.charAt(0).toUpperCase() + texto.slice(1);
}

/**
 * Agrupa as chaves devolvidas pela API nas seções do tipo, na ordem do laudo.
 * Só entram chaves presentes em `chaves`; as desconhecidas vão para "Outros textos".
 */
export function agruparTextos(tipo: string, chaves: string[]): GrupoTextos[] {
  const presentes = new Set(chaves);
  const usadas = new Set<string>();
  const grupos: GrupoTextos[] = [];

  for (const [titulo, itens] of SECOES_POR_TIPO[tipo] ?? []) {
    const doGrupo = itens
      .filter(([chave]) => presentes.has(chave))
      .map(([chave, rotulo]) => {
        usadas.add(chave);
        return { chave, rotulo };
      });
    if (doGrupo.length > 0) grupos.push({ titulo, chaves: doGrupo });
  }

  const restantes = chaves.filter((chave) => !usadas.has(chave));
  if (restantes.length > 0) {
    grupos.push({
      titulo: "Outros textos",
      chaves: restantes.map((chave) => ({ chave, rotulo: rotuloDerivado(chave) })),
    });
  }
  return grupos;
}
