---
description: "Ativa os agentes Engenheiro Backend e Engenheiro Frontend para implementar o upload de fotos (clipboard paste do Lightshot + upload manual) vinculado a Visitas e Ocorrências do Sistema de Automação de Relatórios Prediais."
---
## Contexto
Tarefa BL-11 do backlog em `00_docs/projeto/backlog-tarefas.md`, Etapa 3 (Incremento RFO) de `00_docs/projeto/ciclo-de-vida.md`. Depende de BL-07 (storage service MinIO, `20-storage-service-minio.prompt.md`) e de BL-10 (registro de visitas).
Requisito RF-05 de `00_docs/estudo-do-contexto.md` e RNF-02 (parcial): upload e vinculação de imagens capturadas com Lightshot (via clipboard paste no browser ou upload manual) a Ocorrências e Visitas.
Estratégia de integração com Lightshot detalhada em `00_docs/arquitetura.md` Seção 6 (Opção A — clipboard paste, recomendada; Opção B — upload manual de arquivo). Diagrama de sequência do fluxo em `00_docs/arquitetura.md` Seção 10.6(b).
Mitigação de segurança obrigatória (A08 OWASP, `00_docs/arquitetura.md` Seção 10.1): validar mime-type real (magic bytes) e reprocessar a imagem via Pillow antes de persistir, removendo metadados/EXIF e payloads embutidos.
**A Opção C (pasta monitorada) está fora de escopo desta tarefa** (fora de escopo v1.0, ver `00_docs/projeto/backlog-tarefas.md`).

## Tarefa
Execute em duas etapas sequenciais, uma por agente.

### Etapa 1 — Assuma o papel de **Engenheiro Backend**
1. Implemente os endpoints conforme `00_docs/arquitetura.md` Seção 4:
   - `POST /api/v1/fotos/upload` (multipart/form-data — upload manual, Opção B)
   - `POST /api/v1/fotos/upload-clipboard` (recebe imagem base64 do clipboard paste — Opção A)
   - `POST /api/v1/ocorrencias/{id}/fotos` (vincula foto existente a uma Ocorrência com legenda)
   - `POST /api/v1/visitas/{id}/fotos` (vincula foto existente a uma Visita)
   - `PUT /api/v1/fotos/{id}` (atualiza legenda ou ordem)
   - `DELETE /api/v1/fotos/{id}` (remove vínculo e objeto do storage)
2. Valide o mime-type real do arquivo (magic bytes, não apenas a extensão) e o tamanho máximo permitido; rejeite arquivos que não sejam imagens.
3. Reprocesse toda imagem recebida via Pillow antes de enviar ao storage (recodificação, removendo metadados/EXIF e qualquer payload embutido), conforme mitigação A08.
4. Use o `StorageClient` de `20-storage-service-minio.prompt.md` para persistir o arquivo e gerar a URL (pré-assinada) de acesso.
5. Escreva testes de integração cobrindo: upload manual válido, upload clipboard válido, rejeição de arquivo com mime-type inválido, rejeição de arquivo acima do tamanho máximo, vinculação a Ocorrência e a Visita.

### Etapa 2 — Assuma o papel de **Engenheiro Frontend**
1. Implemente um componente de upload reutilizável com duas ações lado a lado: "Colar da área de transferência" (`navigator.clipboard.read()`, Opção A) e "Enviar arquivo" (input de arquivo com drag-and-drop e seleção múltipla, Opção B).
2. Integre o componente nas telas de Visita (`03_frontend/app/inspecoes/[id]/`) e, quando a tela de Ocorrência existir (BL-14), preveja o mesmo componente para reuso.
3. Exiba miniaturas das fotos vinculadas com opção de editar legenda, reordenar e remover.
4. Trate o requisito de HTTPS da Clipboard API — exiba mensagem clara caso o navegador/contexto não suporte `navigator.clipboard.read()` (ex.: HTTP em vez de HTTPS), orientando o uso da Opção B como alternativa.
5. Trate erros da API no formato RFC 7807 (DEC-11).

## Saída Esperada
- Endpoints de upload/vinculação/gestão de fotos implementados, validados (mime-type, tamanho, reprocessamento Pillow) e testados
- Componente de upload reutilizável (clipboard paste + upload manual) integrado à tela de Visita
- Resumo: endpoints criados, limites de tamanho/mime-type adotados, como testar o paste do clipboard localmente (requisito de HTTPS)

## Restrições
- NÃO aceite upload de foto via URL fornecida pelo cliente (mitigação A10 — SSRF).
- NÃO persista a imagem original sem reprocessamento via Pillow (mitigação A08).
- NÃO permita a Opção C (pasta monitorada) nesta tarefa — está fora de escopo.
- SEMPRE valide mime-type real e tamanho máximo antes de persistir.
- Proteja os endpoints com autenticação (BL-06).
- Leia os arquivos antes de modificá-los.
