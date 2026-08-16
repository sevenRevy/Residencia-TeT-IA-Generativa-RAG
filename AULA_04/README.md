# AULA 04

Pasta com a rotina de conversao e os experimentos de chunking com LangChain. Os PDFs, Markdown, embeddings e relatorios ficam organizados em `corpus/`.

## Onde procurar

| Item | Caminho |
| --- | --- |
| PDFs originais | `corpus/raw/aula04/` |
| Markdown gerado pelo Docling | `corpus/processed/aula04/` |
| Markdown herdado da Aula 02 | `corpus/processed/aula02/` |
| Relatorios de chunking e embeddings | `corpus/reports/` |
| Resumo comparativo | `corpus/reports/summary.json` |
| Cache de embeddings Qwen | `corpus/embeddings/cache/` |
| Script de conversao | `AULA_04/a04_docling.py` |
| Script dos experimentos | `AULA_04/test_langchain.py` |

## Conteudo

- `a04_docling.py`: converte os PDFs de `corpus/raw/aula04/` em Markdown usando Docling.
- `test_langchain.py`: aplica 10 estrategias de chunking sobre os `.md` em `corpus/processed/`, gera embeddings com Qwen local e salva um JSON por documento e estrategia.

Os relatorios ficam no formato `corpus/reports/completo_<documento>_<estrategia>.json`. Ao todo, foram gerados 120 experimentos: 12 documentos Markdown x 10 estrategias, mais o resumo `corpus/reports/summary.json`. Pelo Git, estes arquivos aparecem como novos em `corpus/reports/`; a estrutura antiga `corpus/reports/aula04/` foi substituida.

## Relatório

### 10/08/2026 - AULA 4

Nessa aula, implementei a avaliacao de 10 estrategias de chunking com LangChain, partindo dos arquivos Markdown ja processados em `corpus/processed/aula02/` e `corpus/processed/aula04/`. O pipeline executa a divisao dos textos, gera embeddings para cada chunk com o modelo local `Qwen3-Embedding-0.6B.Q8_0.gguf` e salva os resultados em JSON. Os embeddings usam cache em `corpus/embeddings/cache/`, permitindo retomar a execucao sem recalcular vetores ja gerados.

Cada arquivo de saida em `corpus/reports/` identifica o documento e a estrategia usada. Cada chunk registra `chunk_id`, `document_id`, `document_name`, `test_id`, `strategy`, configuracao de chunking, texto, embedding e metadados. O arquivo `corpus/reports/summary.json` consolida as estatisticas comparativas dos 120 experimentos.

#### Configuracoes testadas

| Teste | Estrategia | Configuracao |
| --- | --- | --- |
| 1 | `fixo_200` | 200 caracteres, sem overlap |
| 2 | `fixo_500` | 500 caracteres, sem overlap |
| 3 | `fixo_1000` | 1000 caracteres, sem overlap |
| 4 | `fixo_2000` | 2000 caracteres, sem overlap |
| 5 | `fixo_500_overlap_50` | 500 caracteres, overlap 50 |
| 6 | `fixo_500_overlap_200` | 500 caracteres, overlap 200 |
| 7 | `paragrafo` | separacao por `\n\n`, priorizando paragrafos |
| 8 | `sentenca_3` | grupos de 3 sentencas |
| 9 | `recursivo` | separadores hierarquicos: paragrafos, linhas, sentencas, espacos e caracteres |
| 10 | `markdown_heading` | headings Markdown detectados automaticamente de `#` a `######` |

#### Estatisticas gerais

| Estrategia | Total de chunks | Media por documento | Tamanho medio | Min | Max | Tokens medios | Dimensao |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `fixo_200` | 7295 | 607.92 | 192.46 | 1 | 200 | 28.95 | 1024 |
| `fixo_500` | 2967 | 247.25 | 487.13 | 3 | 500 | 70.77 | 1024 |
| `fixo_1000` | 1488 | 124.00 | 982.08 | 25 | 1000 | 140.43 | 1024 |
| `fixo_2000` | 747 | 62.25 | 1963.79 | 25 | 2000 | 278.44 | 1024 |
| `fixo_500_overlap_50` | 3292 | 274.33 | 487.74 | 3 | 500 | 70.86 | 1024 |
| `fixo_500_overlap_200` | 4927 | 410.58 | 487.88 | 3 | 500 | 70.99 | 1024 |
| `paragrafo` | 1462 | 121.83 | 972.98 | 3 | 42227 | 136.71 | 1024 |
| `sentenca_3` | 4445 | 370.42 | 342.66 | 5 | 42586 | 48.56 | 1024 |
| `recursivo` | 2083 | 173.58 | 708.08 | 1 | 999 | 100.06 | 1024 |
| `markdown_heading` | 658 | 54.83 | 2425.71 | 3 | 51682 | 335.74 | 1024 |

#### Exemplos observados

No documento `corpus/processed/aula02/bioetica_e_ia.md`, `fixo_200` gerou 251 chunks com media de 198.92 caracteres. O primeiro chunk corta rapidamente o trecho inicial do documento, preservando pouco contexto por causa do limite baixo. Com `fixo_1000`, o mesmo documento gerou 51 chunks com media de 980.45 caracteres, mantendo mais contexto por bloco.

A estrategia `paragrafo` gerou 61 chunks para esse documento, com media de 817.43 caracteres, mas pode criar blocos muito grandes quando o Markdown tem paragrafos longos. A estrategia `sentenca_3` gerou 139 chunks e manteve unidades menores de leitura, mas ainda depende da qualidade da pontuacao extraida do PDF. O `recursivo` gerou 72 chunks com media de 692.65 caracteres e foi mais equilibrado porque tenta preservar paragrafos, linhas e sentencas antes de cortar por caracteres.

O `markdown_heading` gerou 22 chunks para `bioetica_e_ia.md`, com media de 2222.00 caracteres, agrupando conteudo por secoes. Ele preserva melhor a estrutura semantica quando o Markdown tem headings confiaveis, mas pode criar chunks muito grandes em secoes extensas.

#### Analise da conversao PDF -> Markdown

A conversao foi feita por `AULA_04/a04_docling.py`, em lotes de ate 20 paginas por PDF. O script usa Docling com `do_table_structure=True`, `do_ocr=False`, `generate_page_images=False` e `generate_picture_images=True`. O Markdown recebe comentarios JSON com metadados de pagina e, quando ha figuras, metadados de imagem com pagina, secao, link para o PDF e caixa delimitadora quando disponivel.

Nos 12 documentos usados no `summary.json`, o corpus convertido soma 1.936.998 caracteres, 704 headings Markdown, 1.648 linhas de tabela, 420 comentarios `page_metadata`, 171 comentarios `image_metadata` e 542 referencias textuais a figuras/imagens. As tabelas foram preservadas principalmente como tabelas Markdown, mas algumas sofreram degradacao de alinhamento, celulas vazias ou quebras de palavras por causa da estrutura original dos PDFs academicos. As imagens foram preservadas como metadados, descricoes e legendas quando disponiveis; a imagem binaria em si nao entra como conteudo vetorial textual equivalente.

As principais perdas na conversao PDF -> Markdown foram layout bidimensional, posicao visual fina de elementos, qualidade integral de figuras, formulas complexas, relacao espacial entre legenda e imagem, marcadores de pagina como sinal semantico forte e parte da fidelidade de tabelas largas. Isso afeta especialmente artigos com muitas tabelas, graficos e equacoes, porque o chunking textual nao recupera automaticamente a informacao visual que estava no PDF.

#### Analise obrigatoria

1. **Qual estrategia gerou mais chunks?** `fixo_200`, com 7295 chunks no total. O resultado e esperado porque o limite de 200 caracteres forca muitas quebras.

2. **Qual gerou menos chunks?** `markdown_heading`, com 658 chunks. Ela agrupa texto por secoes, gerando menos blocos e blocos mais longos.

3. **Como o tamanho dos chunks variou?** Os tamanhos medios foram de 192.46 caracteres em `fixo_200` ate 2425.71 em `markdown_heading`. As estrategias fixas respeitaram teto rigido de 200, 500, 1000 ou 2000 caracteres; `paragrafo`, `sentenca_3` e `markdown_heading` tiveram outliers grandes, chegando a 42227, 42586 e 51682 caracteres.

4. **Qual estrategia preservou melhor a estrutura dos documentos?** `markdown_heading` preservou melhor a estrutura semantica de secoes porque usa headings Markdown como fronteiras. Porem, ela precisa de uma segunda divisao para secoes longas. Entre as estrategias com limite controlado, `recursivo` foi a mais equilibrada.

5. **Como tabelas foram tratadas?** O Docling converteu muitas tabelas para sintaxe Markdown. Isso preserva linhas e colunas basicas, mas tabelas largas ou com cabecalhos agrupados podem ficar desalinhadas. Splitters por caracteres podem cortar uma tabela no meio; `recursivo` reduz esse risco, e `markdown_heading` tende a manter tabelas dentro da secao original.

6. **Como imagens foram tratadas?** As imagens apareceram no Markdown como comentarios `image_metadata`, com pagina, secao, link para o PDF, bbox e descricao visual quando o modelo vision conseguiu processar a figura. Sem descricao visual, o embedding textual representa apenas metadados e legenda, nao o conteudo visual real.

7. **Quais informacoes foram perdidas durante a conversao PDF -> Markdown?** Foram perdidos ou enfraquecidos layout, coordenadas visuais precisas, imagens rasterizadas, detalhes de graficos, relacoes espaciais, parte de formulas, hifenizacao correta e fidelidade de tabelas complexas. O Markdown e adequado para texto corrido, mas nao substitui perfeitamente o PDF original.

8. **O chunking por caracteres fragmentou conceitos ou estruturas importantes?** Sim. `fixo_200` foi o caso mais critico: o primeiro chunk de `bioetica_e_ia.md`, por exemplo, corta logo apos autores e afiliacao. Mesmo `fixo_500` pode quebrar paragrafos, tabelas e frases no meio, porque nao respeita fronteiras semanticas.

9. **O chunking por paragrafo produziu chunks muito grandes?** Sim. Embora a media tenha sido 972.98 caracteres, o maior chunk chegou a 42227 caracteres. Isso indica que paragrafos extraidos de PDF podem conter blocos longos demais, tabelas ou secoes coladas.

10. **O chunking por sentenca conseguiu preservar melhor o contexto?** Parcialmente. `sentenca_3` gerou chunks menores em media, com 342.66 caracteres, e manteve unidade linguistica melhor que o corte fixo curto. Mas tambem teve outlier de 42586 caracteres, mostrando dependencia da pontuacao e da qualidade da extracao do PDF.

11. **O Recursive Splitter apresentou vantagens?** Sim. `recursivo` manteve media de 708.08 caracteres, teto de 999 e 2083 chunks. Ele preserva paragrafos, linhas e sentencas quando possivel, mas ainda impede chunks muito grandes. Foi a melhor combinacao entre controle de tamanho e preservacao de contexto.

12. **O Markdown Splitter conseguiu preservar a estrutura semantica?** Sim, especialmente nos artigos com headings confiaveis. A desvantagem e que secoes extensas viram chunks muito grandes, como o maximo de 51682 caracteres em `gpt3_language_models.md`.

13. **Qual estrategia parece mais adequada para um sistema de RAG?** `recursivo` e a melhor escolha geral para o RAG deste corpus, porque oferece chunks semanticamente mais coerentes que cortes fixos e evita os blocos enormes de `paragrafo` e `markdown_heading`. Para preservar trilhas semanticas, a melhor evolucao seria combinar `markdown_heading` para metadados de secao com `recursivo` dentro de cada secao.

14. **Quais estrategias devem ser descartadas?** `fixo_200` deve ser descartada por fragmentar demais o contexto. `fixo_2000` deve ser evitada para busca precisa porque gera blocos longos e menos especificos. `paragrafo` e `sentenca_3` nao devem ser usadas sozinhas sem limite maximo, por causa dos outliers. `fixo_500_overlap_200` tambem deve ser evitada como padrao porque aumenta muito a redundancia.

15. **Quais estrategias devem ser utilizadas nos proximos experimentos?** Usaria `recursivo` como baseline principal, `fixo_500_overlap_50` como baseline simples com continuidade, e uma estrategia hibrida `markdown_heading + recursivo` para preservar secao, subtitulo e hierarquia sem gerar chunks gigantes. Tambem vale testar overlap pequeno no `recursivo`, por exemplo 50 a 100 caracteres.

#### Comparacao final das estrategias

`fixo_200` oferece alta granularidade, mas baixa preservacao de contexto. `fixo_500` e `fixo_500_overlap_50` sao baselines simples e previsiveis, com custo moderado. `fixo_500_overlap_200` aumenta continuidade, mas quase dobra a quantidade de chunks em relacao a `fixo_500`, elevando redundancia. `fixo_1000` e `fixo_2000` preservam mais contexto, porem perdem precisao de recuperacao em perguntas especificas.

`paragrafo` e interpretavel, mas depende muito da qualidade da conversao PDF -> Markdown. `sentenca_3` melhora a unidade linguistica, mas falha quando a extracao cria sentencas artificialmente longas. `markdown_heading` e a melhor para preservar estrutura documental, mas nao controla tamanho. `recursivo` foi a estrategia mais robusta experimentalmente, porque manteve o limite de tamanho sem ignorar completamente a estrutura textual.

#### Conclusao para RAG

A melhor representacao para RAG nao e a que gera mais ou menos chunks, e sim a que equilibra recuperacao precisa, contexto suficiente, metadados e baixo ruido. Com os resultados atuais, `recursivo` e a estrategia mais adequada para indexacao vetorial geral. A escolha recomendada para os proximos experimentos e uma abordagem hibrida: usar headings Markdown como metadados de secao e aplicar splitter recursivo dentro de cada secao, com limite aproximado de 800 a 1000 caracteres e overlap pequeno.

#### Entrega

| Item exigido | Situacao | Caminho |
| --- | --- | --- |
| Codigo PDF -> Markdown | Entregue | `AULA_04/a04_docling.py` |
| Codigo Markdown -> 10 estrategias -> embeddings -> JSON | Entregue | `AULA_04/test_langchain.py` |
| PDFs originais | Entregue | `corpus/raw/aula04/` e `corpus/raw/aula02/` |
| Markdown gerado | Entregue | `corpus/processed/aula04/` e `corpus/processed/aula02/` |
| Chunks dos 10 experimentos | Entregue nos JSONs por documento/estrategia | `corpus/reports/completo_*.json` |
| Embeddings dos 10 experimentos | Entregue no campo `embedding` de cada chunk | `corpus/reports/completo_*.json` |
| Metadados | Entregue em cada chunk e nos comentarios do Markdown convertido | `metadata`, `page_metadata`, `image_metadata` |
| Estatisticas comparativas | Entregue | `corpus/reports/summary.json` |
| Relatorio analitico | Entregue | `AULA_04/README.md` |

Resultado experimental: para este corpus, a estrategia `recursivo` produz a melhor representacao geral dos documentos para um sistema de RAG. Ela nao maximiza o numero de chunks, mas preserva melhor o contexto util, limita o tamanho dos blocos, reduz outliers e gera embeddings mais coerentes para recuperacao semantica do que cortes fixos curtos ou secoes Markdown muito extensas.
