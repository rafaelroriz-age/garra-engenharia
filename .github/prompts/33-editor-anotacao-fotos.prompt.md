---
description: "Ativa o agente Engenheiro Frontend para implementar o editor de anotação de fotos (setas, formas, texto, traço livre) integrado ao upload de fotos do Sistema de Automação de Relatórios Prediais."
---
## Contexto
Tarefa BL-31 do backlog em `00_docs/projeto/backlog-tarefas.md`, Etapa 4.5 (RBAC, Editor de Anotação de Fotos e Portal do Cliente). Depende de BL-11 (upload de fotos, já concluída — `04_backend/app/api/v1/fotos.py`, componente de upload em `03_frontend/`).
Origem: esclarecimento direto do usuário (2026-07-24) — a função real do Lightshot no fluxo do auditor é desenhar setas, marcações e anotações sobre a foto, não apenas capturar a tela; o sistema deve oferecer essa mesma capacidade de edição diretamente, para simplificar a confecção dos relatórios.
Requisitos/decisões: RF-14, RN-15 (`00_docs/estudo-do-contexto.md`), DEC-19 (`00_docs/projeto/decisoes.md`), ADR-10 (`00_docs/arquitetura.md` Seção 9 e Stack Tecnológica).
**Importante:** esta tarefa é 100% frontend. Por decisão de arquitetura (ADR-10), a imagem anotada é achatada no browser (canvas) e enviada como arquivo comum aos endpoints de upload já existentes (`POST /api/v1/fotos/upload` e `/fotos/upload-clipboard`) — nenhuma mudança de backend é necessária.

## Tarefa
Assuma o papel de **Engenheiro Frontend**.

1. Adicione a dependência `fabric` (Fabric.js) ao `03_frontend/package.json`.
2. Implemente um componente `PhotoAnnotationEditor` (ou nome equivalente às convenções de `03_frontend/components/`) que recebe uma imagem (File/Blob/base64, vinda do upload manual ou do clipboard paste do componente de BL-11) e abre um canvas de edição com:
   - Ferramenta de seta (linha com ponta de seta)
   - Ferramentas de forma: retângulo e elipse (sem preenchimento, apenas contorno, cor configurável)
   - Ferramenta de texto (caixa de texto posicionável sobre a imagem)
   - Ferramenta de traço livre (freehand drawing)
   - Botão de desfazer (undo) da última marcação
   - Seletor de cor simples (ex.: vermelho, amarelo, azul, preto — cores comuns de marcação técnica)
3. Ao confirmar ("Salvar marcação"), achate o canvas (imagem de fundo + todas as marcações) em um único `Blob`/`File` via `canvas.toBlob()` (ou `fabric.Canvas.toDataURL()` convertido para Blob), substituindo a imagem original que será efetivamente enviada ao endpoint de upload existente.
4. Integre o editor ao componente de upload reutilizável de BL-11 (`24-upload-fotos-lightshot.prompt.md`), oferecendo um botão "Editar/Marcar foto" nas miniaturas antes ou depois do upload (ex.: abrir o editor na miniatura já enviada e reenviar a versão anotada, ou abrir o editor antes de confirmar o upload — escolha a abordagem mais simples de implementar dado o fluxo atual do componente).
5. Garanta que o editor funcione tanto para imagens vindas do clipboard paste (Lightshot) quanto do upload manual — ambas devem poder ser editadas/complementadas no sistema (RN-15).
6. Garanta responsividade mobile básica (RNF-01) — o canvas deve ser utilizável em tela de smartphone (≥ 5,5"), com controles de ferramenta acessíveis por toque.

## Saída Esperada
- Componente de editor de anotação funcionando (seta, forma, texto, traço livre, undo, cor)
- Integração com o fluxo de upload existente, sem exigir nenhuma mudança de backend
- Resumo: componente criado, como o achatamento (flatten) da imagem funciona, como testar manualmente (upload → editar → salvar → confirmar que a versão enviada ao backend já contém as marcações)

## Restrições
- NÃO crie nenhum endpoint novo de backend nem altere `app/api/v1/fotos.py` — a imagem anotada deve ser enviada pelos endpoints já existentes.
- NÃO tente reter a imagem original sem marcação automaticamente (RN-15) — é uma limitação documentada e aceita para o v1.0.
- SEMPRE valide que o resultado final enviado ao backend é uma imagem raster válida (mesmo mime-type aceito por `POST /fotos/upload`), já que o backend reprocessa via Pillow (mitigação A08) e rejeita formatos inesperados.
- Leia os arquivos antes de modificá-los.
