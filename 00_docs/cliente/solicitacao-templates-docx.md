---
title: Solicitação formal de templates .docx e logo ao cliente — HT-02 / BL-19
type: gestao
status: draft
owner: Garra Engenharia
related:
  - 00_docs/projeto/backlog-tarefas-humanas.md
  - 00_docs/projeto/status.md
last_updated: 2026-08-07
---

# Solicitação de templates originais (HT-02)

> Minuta pronta para envio pelo gestor do projeto (e-mail ou WhatsApp). O envio, o recebimento e o arquivamento dos arquivos continuam sendo ação humana. Resolve o bloqueio B-02, que hoje prende BL-12 (fidelidade total), BL-13, BL-17, BL-19, BL-33 (download real) e HT-09.

---

## Assunto

`Garra Engenharia — envio dos modelos originais (.docx/.xlsm) e do logo para o sistema de relatórios`

## Corpo da mensagem

Prezado Eng. Roniel,

Para que o sistema gere os relatórios **visualmente idênticos** aos que a Garra Engenharia já entrega hoje, precisamos dos arquivos **originais editáveis** de cada modelo. As versões que temos hoje são conversões em texto (`.md`), que preservam o conteúdo, mas não o layout — fontes, margens, estilos, quebras de página e cabeçalho não são recuperáveis a partir delas.

Seguem exatamente os arquivos necessários:

| # | Documento | Formato esperado | Referência que já temos |
|---|---|---|---|
| 1 | RFO — Relatório de Fiscalização de Obra | `.xlsm` e/ou `.docx` original | `Relatorio_de_Fiscalizacao_1.md` |
| 2 | LTIP — Laudo Técnico de Inspeção Predial | `.docx` original | `Laudo_Tecnico_de_Inspecao_Predial_2026_-_Cond_Cortina_DAmpezzo.md` |
| 3 | Laudo de Vistoria Cautelar de Recebimento | `.docx` original | `Laudo_Tecnico_de_Vistoria_Cautelar_de_Recebimento_-_Reforma_New_York_-_V01.md` |
| 4 | Vistoria de Imóvel Residencial | `.docx` original | `Laudo_Tecnico_de_Vistoria_de_Imovel_Residencial_-_Ap_1404.md` |
| 5 | RFIP — Relatório Fotográfico de Inspeção Predial | `.docx` original | `Relatorio_Fotografico_de_Inspecao_Predial_-_CORTINA_DAMPAREZZO_-_Versao_Final.md` |
| 6 | Logo da Garra Engenharia | Vetor `.svg`/`.ai`, ou `.png` com fundo transparente em alta resolução | — |

Três observações que ajudam a evitar retrabalho:

1. **Envie a versão mais recente que já foi entregue a um cliente real** — é ela que será usada como template oficial do sistema. Se houver mais de uma variação em uso, envie todas e indique qual é a padrão.
2. **Não é necessário limpar os dados** do documento. Preferimos um exemplo preenchido: ele mostra como cada campo se comporta na prática (tabelas que crescem, legendas de foto, quebras de seção).
3. **Cabeçalho e rodapé** são a parte mais sensível. Se o logo, o CREA ou a numeração de página estiverem em um estilo específico, mantenha o arquivo exatamente como está — não converta para PDF antes de enviar.

Assim que recebermos, a equipe converte cada arquivo em um template com marcadores automáticos e devolve um relatório de teste gerado pelo sistema para o senhor comparar lado a lado com o original antes de qualquer uso em produção.

Fico à disposição.

Atenciosamente,
Rafael Roriz — desenvolvimento do Sistema de Automação de Relatórios Prediais

---

## Checklist interno após o recebimento

- [ ] Salvar os arquivos em `01_output-context/` (local/OneDrive) — **não commitar** binários do cliente no Git (ver `.gitignore`).
- [ ] Conferir se os 6 itens chegaram completos; cobrar os que faltarem antes de iniciar BL-12/BL-13.
- [ ] Acionar o agente conversor para gerar/atualizar as referências `.md` em `00_docs/convertidos/`.
- [ ] Remover B-02 de [status.md](status.md#bloqueios-ativos) e marcar HT-02 como ✅ em [backlog-tarefas-humanas.md](backlog-tarefas-humanas.md).
- [ ] Desbloquear BL-12, BL-13, BL-17, BL-19 e a parte de download de BL-33 em [backlog-tarefas.md](backlog-tarefas.md).
