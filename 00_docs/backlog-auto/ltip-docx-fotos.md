# LTIP: fotos no DOCX (BL-22)

Fecha a pendência "foto no DOCX do LTIP" deixada pela T20 (`ltip-desempenho.md`).

## O que mudou

- `04_backend/app/scripts/build_ltip_templates.py`: a ficha do DOCX ganhou `{{ ocorrencia.foto }}` e a legenda (`{%p if ocorrencia.legenda_foto %}`), logo abaixo do rótulo "Foto nº NN". O HTML/PDF não foi tocado.
- `04_backend/templates/ltip/ltip_template.docx`: regenerado a partir do `layout.json` versionado (sem usar o original do cliente; `01_output-context/` intacto). O `pdfplumber` não está instalado nesta máquina, então o gerador foi chamado com o módulo stubado, só para `gerar_docx`. O `.html.j2` não foi regerado.
- `04_backend/app/services/report_generator/ltip_pipeline.py` (`gerar_docx`):
  - cada ocorrência recebe `foto` e `legenda_foto` (legenda aprovada/manual via `legenda_foto.py`; `legenda_ia_sugerida` nunca entra, DEC-37 DP-9);
  - `reduzir_foto_docx`: lado maior ≤ 640 px (80 mm a ~200 dpi), JPEG q80, com `exif_transpose`. Foto já ≤ 640 px segue sem recodificar. As fotos de 1200 px (DEC-40) são reduzidas aqui;
  - a redução roda em 4 threads (`THREADS_REDUCAO_FOTOS`; Pillow libera o GIL);
  - foto ausente de `fotos_bytes` ou ilegível: placeholder `[foto indisponível]` e `logger.warning`; o DOCX sai. Ocorrência sem foto cadastrada fica sem nada, como no PDF.
- `normalizar_contexto`, o PDF e `renderizar_html` não foram alterados. No PDF, foto ausente continua levantando `KeyError` (teste existente). Só o DOCX tolera.
- Nada de `foto_fetcher.py` foi usado: ele serve ao `url_fetcher` do WeasyPrint. Os bytes continuam vindo de `fotos_bytes`, montado pelo chamador, como no `rfo_pipeline`. Padrão de embutir copiado do RFO (`add_picture`/`InlineImage` com largura fixa), mas com redução prévia, que o RFO não faz.

## Testes

`04_backend/tests/test_ltip_docx_fotos.py` (6 testes, sem banco e sem rede; imagens com Pillow):
foto reduzida + legenda no template versionado; legenda de IA ausente; foto pequena não recodificada; placeholder + aviso no log (ausente e corrompida); `normalizar_contexto` e contexto original intactos; desempenho com 239 fotos.

```
python -m pytest tests/test_ltip_docx_fotos.py tests/test_ltip_pipeline.py -q
19 passed, 2 skipped
```

Os 2 skips são os testes de PDF/fetcher, porque o WeasyPrint 70 não carrega as bibliotecas GTK/Pango no Windows (só no container). O PDF não foi exercitado aqui; o código dele não mudou.

`tests/test_ltip_templates.py` não pôde ser coletado nesta máquina (`ModuleNotFoundError: pdfplumber`, ambiente sem a dependência de `requirements.txt`). Não foi executado; o `gerar_docx` do template foi validado indiretamente pelos testes acima, que renderizam o `.docx` regenerado.

`ruff check .` em `04_backend`: 7 erros, todos pré-existentes e em arquivos que não toquei (`alembic/versions/e5a1f0c2b7d4_...`, `tests/test_portal_versoes_relatorio.py`, `tests/test_relatorio_unicidade.py`; 7 são auto-corrigíveis). Nos arquivos alterados/criados: `All checks passed!`.

## Tempos (239 fotos sintéticas de 1200×900, esta máquina: Windows, OneDrive, Python 3.14)

Só `gerar_docx`, sem banco e sem rede:

| Cenário | total | montagem das fotos | render+salvar | DOCX | fotos de entrada |
|---|---|---|---|---|---|
| Reduzida a 640 px, 4 threads (implementado) | **11,0 s** | 4,7 s | 6,3 s | **17,8 MB** | 42,9 MB |
| Sem redução (embute o original) | 12,8 s | 0,1 s | 12,8 s | 42,9 MB | 42,9 MB |
| Reduzida a 640 px, 1 thread (1ª versão) | 21,7 s | 15,4 s | 6,3 s | 17,8 MB | 42,9 MB |
| Pior caso (ruído em resolução total, 145 MB de entrada), 4 threads | 15,8 s | 6,1 s | 9,7 s | 30,8 MB | 145,5 MB |

Observações:

- **Os números absolutos ficaram bem acima dos ~2 s que a T17 estimou** (`ltip-desempenho.md`). Aquela estimativa vinha de outra máquina e de fotos reais pequenas; aqui até o DOCX sem redução leva 12,8 s. A comparação válida é relativa: a redução, em paralelo, não custa tempo e corta o arquivo em ~60 %.
- As fotos sintéticas não são fotos de obra; o tempo real depende do tamanho dos JPEG de entrada. Convém repetir a medida no container com fotos reais antes de concluir sobre RNF-06.
- O teste de desempenho só falha acima de 30 s ou se o DOCX ficar maior que as fotos originais; não fixa o tempo medido, por variar com a máquina.
- Pico de memória do DOCX não foi medido.

## Propostas e pontos para o fechamento de lote (não registrados em `decisoes.md`)

- **Proposta DEC-T56-a**: fotos embutidas no DOCX do LTIP são reduzidas a 640 px de lado maior (JPEG q80). Se o cliente quiser impressão em alta resolução do DOCX, subir `LADO_MAX_FOTO_DOCX_PX`.
- O mesmo `reduzir_foto_docx` serviria ao DOCX do RFIP, da Vistoria Cautelar e da Residencial, onde `add_picture` embute o original; fica para tarefa própria. No RFO há `otimizar_imagem` (1200 px), que não reduz para a largura da página.
- Atualizar o item "DOCX do LTIP ainda sem foto" de `ltip-desempenho.md` e a lacuna de BL-17 em `ltip-pipeline.md`.
- O template `.docx` agora diverge do que o `build_ltip_templates` gerava antes; quem regenerar a partir do PDF do cliente já obtém o placeholder.
