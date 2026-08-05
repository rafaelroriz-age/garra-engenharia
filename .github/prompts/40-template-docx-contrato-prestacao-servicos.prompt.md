---
description: "Ativa o agente Engenheiro Backend para gerar um template DOCX reutilizável (Jinja/docxtpl) do Contrato de Prestação de Serviços a partir do documento revisado enviado pelo cliente."
---

## Contexto
Tarefa BL-40 do backlog em `00_docs/projeto/backlog-tarefas.md`, seção "Documentos Administrativos (Contratos)".
Documento de origem: `01_output-context/Contrato_Revisado_Garra_Software.md` (versão em Markdown do `.docx` revisado enviado pelo cliente).
Este template é de uso **administrativo/contratual** (contrato de prestação de serviços entre Garra Engenharia e o cliente) — **não deve ser confundido** com os templates de relatório técnico (RFO/LTIP/RFIP) referenciados em B-02/HT-02 (`backlog-tarefas-humanas.md`), que continuam bloqueados aguardando os `.docx` originais do cliente.
`docxtpl`/`jinja2`/`python-docx` já constam em `04_backend/requirements.txt` desde o scaffold (BL-02), sem uso efetivo até esta tarefa.

## Tarefa
Assuma o papel de **Engenheiro Backend** e produza um template DOCX parametrizável para o contrato:

1. Leia `01_output-context/Contrato_Revisado_Garra_Software.md` e identifique todos os trechos variáveis (partes, CNPJs, endereços, datas, prazos, percentuais, critérios de aceite da tabela do Anexo I).
2. Escreva um script determinístico (não copiar/colar manual) em `04_backend/app/scripts/build_contract_template_docx.py` que:
   - Converta o Markdown para um `.docx` (`python-docx`), preservando títulos, parágrafos, listas e a tabela do Anexo I.
   - Substitua os trechos variáveis por placeholders Jinja2 (`{{ nome_da_variavel }}`) compatíveis com `docxtpl`.
   - Gere também um guia de placeholders (`.md`) listando todas as variáveis usadas, para quem for preencher o contexto de renderização.
3. Salve os artefatos gerados em `04_backend/templates/contracts/`:
   - `contrato_revisado_template.docx`
   - `contrato_revisado_template.placeholders.md`
4. Rode o script (`.venv\Scripts\python.exe -m app.scripts.build_contract_template_docx` a partir de `04_backend/`) e confirme que os dois arquivos são gerados sem erro.
5. Documente no `04_backend/README.md` (ou seção equivalente) como o template é gerado/regenerado e como ele deve ser consumido futuramente com `docxtpl.DocxTemplate(...).render(contexto)`.

## Saída Esperada
- Script reprodutível `04_backend/app/scripts/build_contract_template_docx.py`.
- Template `04_backend/templates/contracts/contrato_revisado_template.docx` com placeholders Jinja2.
- Guia de placeholders `04_backend/templates/contracts/contrato_revisado_template.placeholders.md`.
- Backlog (`backlog-tarefas.md`) e status (`status.md`) atualizados referenciando esta tarefa como concluída.

## Restrições
- NÃO usar isso como resolução de B-02/HT-02 (templates de relatório técnico) — são documentos e finalidades diferentes.
- NÃO transcrever o contrato manualmente célula por célula — o script deve derivar o `.docx` do Markdown de forma determinística.
- NÃO substituir termos genéricos (ex.: "CONTRATADO") de forma ampla o suficiente para corromper cláusulas jurídicas que usam a mesma palavra como termo definido — usar substituições de trechos completos e específicos.
- Leia os arquivos antes de modificá-los.
