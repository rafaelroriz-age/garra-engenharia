---
description: "Ativa o agente Conversor de Documentos para Markdown para converter todos os documentos de 01_output-context/ em arquivos .md estruturados."
---
## Contexto
Documentos de origem estão em `01_output-context/` (formatos: `.xlsm`, `.xlsx`, `.docx`, `.pdf`, `.csv`, `.pptx`).
Python com `openpyxl` e `pandas` disponível via conda.

## Tarefa
Assuma o papel de **Conversor de Documentos para Markdown** e:

1. Liste todos os documentos em `01_output-context/` e identifique os formatos.
2. Para cada documento `.xlsm`/`.xlsx`: extraia todas as abas usando Python (`openpyxl`/`pandas`) e converta para tabelas Markdown.
3. Para cada aba, use o nome da aba como título `##` e preserve cabeçalhos, valores e notas.
4. Salve cada resultado como `01_output-context/<NomeDoDocumento>.md`.
5. Gere ou atualize `01_output-context/README.md` com índice dos arquivos convertidos.

## Saída Esperada
- Um arquivo `.md` por documento em `01_output-context/`
- `01_output-context/README.md` atualizado com índice

## Restrições
- NÃO invente dados — transcreva exatamente o que está no documento.
- NÃO altere valores numéricos, datas ou unidades.
- Registre no README qualquer conteúdo que não pôde ser extraído (imagens, macros, gráficos).
