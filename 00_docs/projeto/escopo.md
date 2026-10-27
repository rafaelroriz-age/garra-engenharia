---
title: Escopo do Projeto — Sistema de Automação de Relatórios Prediais
type: gestao
status: aprovado
owner: Garra Engenharia
last_updated: 2026-09-17
---

# Escopo do Projeto

## Identificação

| Campo | Valor |
|---|---|
| **Projeto** | Sistema de Automação de Relatórios Prediais — Garra Engenharia |
| **Cliente** | Eng. Civil Esp. Roniel Ribeiro Costa (CREA-GO nº 1020613386/D-GO) |
| **Responsável** | Garra Engenharia, Aparecida de Goiânia/GO |
| **Data de início** | 2026-07-08 |
| **Status** | Em andamento — Fase de Documentação concluída |

---

## O que está DENTRO do escopo

### Funcionalidades Core
- **Cadastro de edificações** com sistemas prediais, caracterização física e documentos técnicos
- **Contratos de serviço** com múltiplas partes (contratante, executoras, RTE, ARTs)
- **Relatório de Fiscalização de Obra (RFO)**: visitas diárias, mão de obra, medições, fotos
- **Laudo Técnico de Inspeção Predial (LTIP)**: ocorrências por sistema, classificação completa CMM + GUT
- **Vistoria Cautelar de Recebimento**: conformidade com projeto/contrato
- **Vistoria de Imóvel Residencial**: diagnóstico por cômodo/sistema
- **Relatório Fotográfico de Inspeção Predial (RFIP)**: fotos organizadas por sistema
- **Upload de imagens via Lightshot** (clipboard paste + upload manual)
- **Editor de anotação de fotos** integrado ao upload: setas, formas, texto e traço livre sobre a imagem — mesma função de marcação do Lightshot, disponibilizada dentro do próprio sistema (RF-14)
- **Geração automática de PDF** fiel ao template do cliente (WeasyPrint + HTML/CSS)
- **Geração de DOCX editável** via docxtpl com template Word do cliente
- **Dashboard de saúde** por edificação e sistema predial
- **Portal do Cliente**: área somente leitura para o contratante/síndico acompanhar a auditoria em andamento (dashboard) e acessar seus documentos/relatórios emitidos (RF-13), com controle de acesso por perfil (RBAC: auditor vs. cliente)
- **Histórico de inspeções** por edificação com versionamento de relatórios
- **Gabarito de sistemas prediais** pré-carregado conforme `RFO_INSPECAO.md`
- **Interface PWA** funcional em smartphone para uso em campo
- **Autenticação** com JWT + bcrypt

### Infraestrutura
- Frontend: Next.js 14 (PWA)
- Backend: FastAPI (Python 3.12)
- Banco: PostgreSQL 16
- Armazenamento de arquivos: MinIO (self-hosted) com compatibilidade S3
- Deploy: Docker Compose local; opção nuvem (Railway/Render) como extensão

---

## O que está FORA do escopo

| Item | Motivo |
|---|---|
| App nativo iOS/Android | PWA cobre os requisitos; custo 3x maior sem benefício proporcional |
| Integração API com CREA | **Confirmado fora de escopo (2026-09-17, DEC-29)** — lacuna #7: os números de CREA e ART são digitados manualmente |
| Módulo de assinatura digital ICP-Brasil | **Confirmado fora de escopo (2026-09-10, DEC-28)** — o cliente usa apenas CREA e ART impressos no documento |
| App desktop de pasta monitorada para Lightshot | **Confirmado fora de escopo (2026-09-17, DEC-29)** — lacuna #4: o fluxo permanece por clipboard/upload manual, com a marcação feita no editor interno (RF-14/BL-31) |
| Módulo financeiro / emissão de NF | Fora do domínio técnico |
| Integração com Power BI | Dados exportáveis via API; BI é responsabilidade do cliente |
| Suporte offline completo (Service Worker + IndexedDB) | **Confirmado fora de escopo (2026-09-10, DEC-26)** — há cobertura 4G/Wi-Fi em todas as edificações inspecionadas |
| Calendário/alertas de re-inspeção por grau de risco | **Confirmado fora de escopo (2026-09-17, DEC-29)** — lacuna #1: não há periodicidade obrigatória; o prazo de retorno é recomendação técnica escrita no laudo (RN-13) |
| Auto-cadastro público de usuários Cliente no Portal | [A ESCLARECER] lacuna #11 — posição interina: criação manual da credencial pelo engenheiro fiscal (ver `00_docs/estudo-do-contexto.md`) |

---

## Premissas

1. O Eng. Roniel utiliza Lightshot como ferramenta padrão de captura em campo e continuará usando.
2. O layout dos documentos atuais (DOCX/PDF) é o padrão definitivo — sem alterações de design.
3. O sistema será usado por um engenheiro responsável técnico e por auxiliares de campo, que também registram visitas/ocorrências/fotos com credencial própria (confirmado em 2026-09-10, DEC-27).
4. O engenheiro tem acesso a internet durante o uso (campo com 4G/Wi-Fi) — confirmado pelo cliente em 2026-09-10 (DEC-26).
5. Os templates Word/HTML serão fornecidos ou validados pelo cliente antes da implementação.
6. O gabarito de sistemas em `RFO_INSPECAO.md` é a fonte definitiva dos dados mestre.

---

## Restrições

1. **Fidelidade visual mandatória**: o relatório gerado deve ser visualmente indistinguível do modelo atual (RNF-03).
2. **Lightshot não negociável**: a integração com o fluxo de captura Lightshot é requisito mandatório.
3. **Python no backend**: as bibliotecas de geração de PDF/DOCX (WeasyPrint, docxtpl) exigem Python — não substituível por Node.js neste aspecto.
4. **Sem implementação sem validação de lacunas**: os itens `[A ESCLARECER]` devem ser resolvidos com o cliente antes do início de cada fase.

---

## Critérios de Aceitação da v1.0

- [ ] Geração de RFO completo (cabeçalho + N visitas + fotos) em PDF/DOCX fiel ao modelo
- [ ] Geração de LTIP completo (todas as seções + relatório fotográfico por sistema) em PDF/DOCX
- [ ] Upload de foto via clipboard paste (Lightshot) funcionando no browser
- [ ] Dashboard de saúde por edificação exibindo distribuição Mínimo/Médio/Crítico por sistema
- [ ] Interface usável em smartphone (tela 5,5") sem erros de layout
- [ ] Gabarito de 15 sistemas prediais pré-carregado conforme `RFO_INSPECAO.md`
- [ ] Autenticação funcionando com JWT
- [ ] Histórico de versões de relatórios por contrato
- [ ] Editor de anotação de fotos (setas, formas, texto, traço livre) funcionando no upload de fotos (RF-14)
- [ ] Portal do Cliente exibindo dashboard de acompanhamento e lista de documentos/relatórios escopados ao contratante logado, sem acesso a dados de outros clientes (RF-13, RN-14)
