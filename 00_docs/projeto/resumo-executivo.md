---
title: Resumo Executivo — Sistema de Automação de Relatórios Prediais
type: gestao
status: ativo
owner: Garra Engenharia
audience: cliente / stakeholders não técnicos
last_updated: 2026-07-08
---

# Resumo Executivo

## O Problema

O **Eng. Civil Esp. Roniel Ribeiro Costa**, da Garra Engenharia, produz manualmente relatórios técnicos complexos de engenharia predial — laudos de inspeção, relatórios de fiscalização de obra e vistorias. Cada documento pode ter de 20 a 200+ páginas, centenas de fotos organizadas por sistema predial e tabelas técnicas de classificação de anomalias.

O processo atual envolve preencher planilhas Excel/XLSM em campo, transferir os dados para documentos Word, inserir fotos manualmente e ajustar o layout antes de cada entrega. Esse fluxo é **lento, propenso a erros e difícil de escalar** quando múltiplos contratos estão em andamento simultaneamente.

---

## A Solução

Um **sistema web** que automatiza a produção dos relatórios, mantendo fidelidade absoluta ao layout e terminologia dos documentos atuais do cliente. O engenheiro registra as informações diretamente pelo celular durante a vistoria e, ao final, gera o relatório completo em PDF e Word com um clique.

### O que o sistema faz

- **Registra edificações e contratos**: mantém o cadastro de todas as obras e clientes em um só lugar
- **Captura ocorrências em campo**: via smartphone, o engenheiro registra cada item inspecionado com sistema predial, classificação técnica e fotos (integrado ao Lightshot)
- **Organiza fotos automaticamente**: as imagens são organizadas por sistema predial, exatamente como exigido pela NBR 16747
- **Gera relatórios completos**: PDF e Word fiéis ao modelo atual, prontos para entrega ao cliente, em menos de 1 minuto
- **Exibe painel de saúde**: dashboard visual mostrando o estado de cada sistema predial da edificação (Mínimo / Médio / Crítico)
- **Mantém histórico**: todo o histórico de inspeções por edificação fica disponível para consulta e comparação

---

## Benefícios Esperados

| Benefício | Situação atual | Com o sistema |
|---|---|---|
| Tempo de produção de um LTIP | 8–16 horas de edição manual | < 2 horas (registro em campo + geração automática) |
| Erros de preenchimento | Frequentes (cópia manual entre planilha e Word) | Eliminados (dado inserido uma vez) |
| Organização de fotos | Manual, sujeita a perda | Automática, organizada por sistema e vinculada à ocorrência |
| Acesso a histórico | Arquivos locais no notebook | Centralizado e acessível de qualquer dispositivo |
| Escalabilidade | Difícil gerenciar 3+ contratos simultâneos | Múltiplos contratos gerenciados em paralelo |

---

## Tecnologias Utilizadas

> Esta seção é para informação; não é necessário conhecimento técnico.

O sistema é construído com tecnologias modernas, abertas e de baixo custo operacional. Funciona como um site que pode ser instalado no celular (sem precisar de app na loja). Os dados ficam armazenados com segurança, com backup automático. Os relatórios são gerados a partir dos mesmos modelos que o engenheiro já usa hoje.

---

## Cronograma Estimado por Fase

| Fase | Descrição | Duração estimada |
|---|---|---|
| ✅ Fase 1 | Levantamento e documentação | Concluída |
| ⏳ Fase 2 | Validação com cliente + protótipo de template | 1–2 semanas |
| ⬜ Fase 3 | Implementação do backend (API + banco de dados) | 3–4 semanas |
| ⬜ Fase 4 | Implementação do frontend (interface web/mobile) | 3–4 semanas |
| ⬜ Fase 5 | Integração, testes e ajustes de layout | 2 semanas |
| ⬜ Fase 6 | Deploy e treinamento | 1 semana |
| **Total** | | **~10–13 semanas** |

> Duração sujeita a confirmação após resolução das lacunas em aberto e validação dos templates.

---

## Decisões Pendentes do Cliente

Antes de iniciar a implementação, precisamos confirmar com o Eng. Roniel:

1. O sistema precisa funcionar **sem internet** (campo sem 4G)?
2. Haverá **outros usuários** além do engenheiro? (auxiliares, estagiários)
3. O cliente (síndico/proprietário) precisa **acessar o sistema** para ver relatórios, ou recebe sempre por e-mail?
4. É necessário **assinatura digital** (ICP-Brasil) nos PDFs?
5. Qual a **preferência de hospedagem**: notebook local ou servidor na internet?

---

## Próxima Ação Recomendada

**Agendar reunião de kickoff** com o Eng. Roniel para:
- Responder as 5 perguntas acima
- Entregar os arquivos `.docx` dos modelos atuais
- Validar o modelo de dados e os fluxos documentados
- Confirmar escopo e cronograma da v1.0
