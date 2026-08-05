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
p.add_run('Garra Engenharia — acompanhamento executivo').italic = True

document.add_heading('Resumo executivo', level=1)
for text in [
    'O projeto está em uma fase muito avançada de desenvolvimento. A base técnica já foi montada, os principais módulos de negócio foram estruturados e a solução já está preparada para ser validada em ambiente de produção.',
    'Em termos práticos, o trabalho principal que resta não é reconstruir o sistema do zero, mas concluir a etapa operacional de implantação no Render: criar os serviços, ligar o backend e o frontend ao banco e preencher os segredos e variáveis de ambiente.',
    'Com isso, o MVP pode ser entregue em um prazo mais otimista, desde que a validação final e a configuração de produção ocorram de forma ágil.'
]:
    document.add_paragraph(text)

document.add_heading('Onde o projeto está hoje', level=1)
document.add_paragraph('O desenvolvimento está em uma etapa de consolidação e finalização operacional. A solução já passou pela fundação técnica, pela modelagem do sistema, pela autenticação, pelo armazenamento de arquivos e pela estrutura inicial das telas principais.')
for item in [
    'Infraestrutura do projeto organizada e pronta para execução.',
    'Backend com estrutura inicial implementada e com fluxo de dados preparado.',
    'Frontend com telas principais já iniciadas e com navegação básica definida.',
    'Blueprint de deploy preparado no Render, incluindo backend, frontend e banco.',
    'O que falta, de forma objetiva, é a configuração final dos serviços e dos segredos no ambiente de produção.'
]:
    document.add_paragraph(item, style='List Bullet')

document.add_heading('Em que fase estamos', level=1)
document.add_paragraph('Estamos na fase de conclusão da implementação base e de preparação para a validação do MVP. O projeto já passou pelas etapas de análise, arquitetura, modelagem, configuração inicial e estruturação das funções centrais.')

table = document.add_table(rows=1, cols=3)
table.style = 'Table Grid'
headers = ['Etapa', 'Status', 'Observação']
for i, h in enumerate(headers):
    table.cell(0, i).text = h
rows = [
    ['Análise e arquitetura', 'Concluída', 'Requisitos, contexto e estrutura do sistema já definidos.'],
    ['Fundação técnica', 'Concluída', 'Backend, banco, autenticação e armazenamento preparados.'],
    ['Interface inicial', 'Em andamento', 'Telas principais já estruturadas e em refinamento.'],
    ['Implantação no Render', 'Pendente de conclusão', 'Falta criar os serviços e preencher os segredos e variáveis.'],
    ['MVP funcional', 'Próximo passo', 'Pode ser liberado após a validação final e configuração operacional.'],
]
for row in rows:
    cells = table.add_row().cells
    for i, value in enumerate(row):
        cells[i].text = value

document.add_heading('Prazo mais otimista para o MVP', level=1)
document.add_paragraph('Considerando que a maior parte do desenvolvimento já está pronta e que a implantação no Render está muito próxima da etapa final, um prazo mais otimista para o MVP seria de cerca de 7 a 10 dias úteis, desde que a configuração dos serviços e segredos seja concluída de forma rápida.')
document.add_paragraph('Se os serviços forem criados e as variáveis de ambiente preenchidas em um fluxo direto, o sistema pode entrar em validação funcional em pouco tempo, com foco em: login, cadastro de dados básicos, fluxo principal de vistoria e geração do relatório inicial.')

document.add_heading('Próximos passos', level=1)
for item in [
    'Criar os serviços no Render para backend, frontend e banco.',
    'Preencher os segredos e variáveis de ambiente: JWT, conexão com banco, URL da API e segredos de armazenamento.',
    'Validar a comunicação entre frontend e backend em ambiente real.',
    'Testar o fluxo principal do MVP com foco em uso do cliente.',
    'Definir a data de homologação e a liberação inicial do sistema.'
]:
    document.add_paragraph(item, style='List Number')

document.add_heading('Conclusão', level=1)
document.add_paragraph('O projeto está em uma posição muito favorável. O trabalho técnico principal já foi realizado e a entrega do MVP depende agora da finalização da camada de implantação e configuração operacional.')

document.save(str(out_path))
print(f'Arquivo criado em {out_path}')
