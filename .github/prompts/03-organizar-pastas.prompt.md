---
description: "Ativa o agente Organizador de Pastas para inventariar e reorganizar a estrutura de diretórios do repositório."
---
## Contexto
Repositório em `c:\Users\dynatest\OneDrive - Dynatest Engenharia\Área de Trabalho\Novos_proj\garra-engenharia`.
Podem existir scripts soltos na raiz, arquivos temporários e pastas sem convenção.

## Tarefa
Assuma o papel de **Organizador de Pastas** e:

1. Faça um inventário completo da estrutura atual (liste tudo).
2. Identifique: arquivos soltos na raiz, temporários, duplicados e sem categorização.
3. Proponha a estrutura-alvo com convenções `kebab-case` e agrupamento por domínio:
   ```
   01_output-context/   ← documentos de origem e .md convertidos
   00_docs/             ← estudo do contexto, arquitetura, projeto
   02_prototipos/       ← wireframes e HTML estático
   scripts/          ← scripts Python/PowerShell utilitários
   src/              ← código-fonte da aplicação
   .github/          ← agents, prompts, instructions
   ```
4. Apresente a proposta antes de mover qualquer arquivo.
5. Após aprovação, aplique as mudanças e atualize referências.

## Saída Esperada
- Estrutura de pastas reorganizada
- Tabela: arquivo/pasta anterior → novo local
- Convenções adotadas documentadas

## Restrições
- NÃO exclua arquivos sem confirmar.
- NÃO mova `.github/`, `package.json`, `.git/` sem aviso.
- NÃO altere o conteúdo interno dos arquivos.
