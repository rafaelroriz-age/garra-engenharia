from pathlib import Path
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

out_path = Path('00_docs/cliente/relatorio-situacao-mvp.docx')
out_path.parent.mkdir(parents=True, exist_ok=True)

document = Document()
styles = document.styles
style = styles['Normal']
style.font.name = 'Calibri'
style.font.size = Pt(11)

p = document.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('Relatório de Situação do Projeto\n')
run.bold = True
run.font.size = Pt(20)
run = p.add_run('Sistema de Automação de Relatórios Prediais')
run.font.size = Pt(14)

p = document.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.add_run('Garra Engenharia — acompanhamento executivo · atualizado em 12/08/2026').italic = True

document.add_heading('Resumo executivo', level=1)
for text in [
    'O projeto está em fase avançada, com aproximadamente 85% concluído. O sistema já funciona de ponta a ponta nos fluxos principais: cadastro de edificações e contratos, registro de inspeções e visitas, lançamento de ocorrências, fotos com anotação, painel de saúde por edificação e portal do cliente.',
    'O trabalho restante não é reconstruir o que já foi feito, mas concluir três frentes: a validação final das definições de negócio que ficaram em aberto, a montagem dos cinco modelos de relatório a partir dos arquivos que o engenheiro já utiliza, e os ajustes finais de implantação no ambiente de produção (Render).',
    'Com isso, o MVP pode ser entregue em um prazo curto, desde que a validação final e a configuração de produção ocorram de forma ágil.'
]:
    document.add_paragraph(text)

document.add_heading('Onde o projeto está hoje', level=1)
document.add_paragraph('A base técnica e os principais módulos de negócio já foram construídos e testados. As etapas de análise, arquitetura e modelagem estão concluídas, e o backend e o frontend estão em grande parte finalizados.')
for item in [
    'Análise, estudo de contexto e arquitetura do sistema: concluídos.',
    'Backend (~90%): APIs de edificações, contratos, inspeções, visitas, ocorrências, fotos, dashboard, portal do cliente e autenticação já implementadas e integradas.',
    'Frontend (~85%): login, dashboard, cadastros, visitas, ocorrências, upload e anotação de fotos e portal do cliente já presentes na interface.',
    'Segurança (revisão OWASP), backups automatizados e automação de implantação (CI/CD) já configurados.',
    'Infraestrutura de produção no Render provisionada; falta apenas a configuração final de segredos e validação em produção.'
]:
    document.add_paragraph(item, style='List Bullet')

document.add_heading('Em que fase estamos', level=1)
document.add_paragraph('Estamos na fase de consolidação e preparação para a homologação do MVP. Abaixo, o avanço por etapa:')

table = document.add_table(rows=1, cols=3)
table.style = 'Table Grid'
headers = ['Etapa', 'Status', 'Observação']
for i, h in enumerate(headers):
    table.cell(0, i).text = h
rows = [
    ['Conversão de documentos', 'Concluída (100%)', 'Documentos originais convertidos e organizados.'],
    ['Estudo do contexto e arquitetura', 'Concluída (100%)', 'Requisitos, modelo de dados e decisões técnicas definidos.'],
    ['Backend (API + banco de dados)', 'Em grande parte concluída (90%)', 'Módulos principais implementados e testados.'],
    ['Frontend (interface web/mobile)', 'Em grande parte concluída (85%)', 'Telas principais funcionais; refinamentos em andamento.'],
    ['Integração e testes', 'Em andamento (75%)', 'Testes automatizados rodando; falta fechar o fluxo de geração de relatório.'],
    ['Implantação e documentação final', 'Em andamento (80%)', 'Produção no Render provisionada; falta configuração final.'],
]
for row in rows:
    cells = table.add_row().cells
    for i, value in enumerate(row):
        cells[i].text = value

document.add_heading('O que precisa da sua atenção', level=1)
document.add_paragraph('Para liberar o MVP, restam algumas definições que dependem de decisão ou confirmação sua:')
for item in [
    'Validação das definições de negócio em aberto: funcionamento sem internet em campo, inclusão de outros usuários além do engenheiro e necessidade de assinatura digital nos relatórios.',
    'Confirmação de que os arquivos-modelo atuais (planilhas e PDFs) são a versão vigente e envio da logo em alta resolução/vetorial para aplicação nos relatórios e no aplicativo.',
    'Escolha do provedor de inteligência artificial para as legendas técnicas das fotos (envolve privacidade dos dados e custo por uso).'
]:
    document.add_paragraph(item, style='List Bullet')

document.add_heading('Próximos passos', level=1)
for item in [
    'Agendar a reunião de validação das definições de negócio em aberto.',
    'Montar os cinco modelos de relatório (RFO, LTIP, vistorias e relatório fotográfico) a partir dos arquivos já disponíveis.',
    'Definir o provedor de IA para as legendas técnicas.',
    'Concluir a configuração de produção no Render (segredos e validação final).',
    'Homologar visualmente os relatórios gerados e liberar o sistema para uso.'
]:
    document.add_paragraph(item, style='List Number')

document.add_heading('Conclusão', level=1)
document.add_paragraph('O projeto está em posição muito favorável: o trabalho técnico principal já foi realizado e a entrega do MVP depende agora da validação das definições de negócio, da montagem dos modelos de relatório e da finalização da configuração operacional.')

document.save(str(out_path))
print(f'Arquivo criado em {out_path}')
