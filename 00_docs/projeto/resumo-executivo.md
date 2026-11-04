---
title: Resumo Executivo — Sistema de Automação de Relatórios Prediais
type: gestao
status: ativo
owner: Garra Engenharia
audience: cliente / stakeholders não técnicos
last_updated: 2026-11-03
---

# Resumo Executivo

## O Problema

O **Eng. Civil Esp. Roniel Ribeiro Costa**, da Garra Engenharia, produz manualmente relatórios técnicos complexos de engenharia predial — laudos de inspeção, relatórios de fiscalização de obra e vistorias. Cada documento pode ter de 20 a 200+ páginas, centenas de fotos organizadas por sistema predial e tabelas técnicas de classificação de anomalias.

O processo atual envolve preencher planilhas Excel/XLSM em campo, transferir os dados para documentos Word, inserir fotos manualmente e ajustar o layout antes de cada entrega. Esse fluxo é **lento, propenso a erros e difícil de escalar** quando múltiplos contratos estão em andamento simultaneamente.

---

## A Solução

Um **sistema web** que automatiza a produção dos relatórios, mantendo fidelidade absoluta ao layout e terminologia dos documentos atuais do cliente. O engenheiro registra as informações diretamente pelo celular durante a vistoria e, ao final, gera o relatório completo em PDF e Word com um clique.

> **Situação em novembro de 2026:** o cadastro, o registro de visitas, ocorrências e fotos, o painel de saúde e o portal do cliente já funcionam. A **geração do relatório em PDF e Word pelo próprio sistema é a principal entrega pendente**: os modelos do RFO e do LTIP já foram reproduzidos a partir dos originais do cliente, mas o botão de gerar ainda não está disponível na tela. Detalhes em [status.md](status.md).

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

## Estado Atual

| Frente | Situação |
|---|---|
| Levantamento, documentação e validação com o cliente | Concluídos (validação encerrada em 17/09/2026) |
| Sistema (servidor e banco de dados) | Em funcionamento: cadastros, visitas, ocorrências, fotos, classificação de risco, painel e portal |
| Telas (web e celular) | Em funcionamento para os mesmos fluxos; a tela de relatório ainda está em construção |
| Modelos de relatório | RFO e LTIP reproduzidos a partir dos originais do cliente; relatório fotográfico (RFIP) pendente |
| Geração de PDF e Word pelo sistema | **Pendente** — hoje só é feita por ferramenta interna da equipe |
| Publicação na internet | Configurada no Render |

> O cronograma e o percentual de avanço atualizados ficam em [status.md](status.md) e [cronograma.md](cronograma.md).

---

## Decisões do Cliente (já respondidas)

As cinco perguntas feitas antes da implementação já foram respondidas (registro em [decisoes.md](decisoes.md)):

1. **Sem internet?** Não: há 4G/Wi-Fi em campo; o sistema funciona online (DEC-26).
2. **Outros usuários?** Sim: perfil de auxiliar de campo, com escrita limitada (DEC-27).
3. **Cliente acessa o sistema?** Sim: portal do cliente, só leitura e só das próprias edificações (DEC-18).
4. **Assinatura digital ICP-Brasil?** Não na v1.0: CREA e ART impressos no documento (DEC-28).
5. **Hospedagem?** Servidor na internet (Render), definido em 21/07/2026.

Os modelos originais do cliente também já estão com a equipe; não é preciso enviar os `.docx` (DEC-25, DEC-30).

---

## Próxima Ação

Entregar a geração de PDF e Word pelo sistema e o relatório fotográfico (RFIP). A escolha do provedor de IA para as legendas assistidas segue pendente. Acompanhamento em [status.md](status.md).
