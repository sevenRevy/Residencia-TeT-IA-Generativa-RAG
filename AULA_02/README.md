# AULA 02

Pasta com os scripts da atividade de conversao de PDFs e extracao de informacoes estruturadas. Os dados gerados e consumidos pela aula ficam em `corpus/`.

## Onde procurar

| Item | Caminho |
| --- | --- |
| PDFs originais | `corpus/raw/aula02/` |
| Markdown convertido | `corpus/processed/aula02/` |
| JSONs de metadados | `corpus/metadata/aula02/` |
| Relatorios posteriores que reutilizam estes Markdown | `corpus/reports/` |
| Scripts da aula | `AULA_02/Aula02_arquivos_output/` |

## Conteudo

- `Aula02_arquivos_output/test_docling.py`: converte PDFs de `corpus/raw/aula02/` para Markdown em `corpus/processed/aula02/`.
- `Aula02_arquivos_output/test_json_extractor.py`: le Markdown de `corpus/processed/aula02/` e salva metadados em `corpus/metadata/aula02/`.

## Relatório

### 05/08/2026 - AULA 2

Nessa aula, trabalhei com extração estruturada de informações a partir de arquivos `.md`. O script `Aula02_arquivos_output/test_json_extractor.py` lê o conteúdo de um documento de entrada em `corpus/processed/aula02/`, envia o texto para um modelo via OpenRouter/OpenAI e solicita a geração de um JSON seguindo um schema fixo com os campos `titulo`, `autores` e `ano`.

O resultado é salvo em `corpus/metadata/aula02/`, gerando um arquivo `.json` para cada documento processado. A proposta da atividade foi transformar texto livre em dados estruturados, facilitando o uso posterior em pipelines de RAG, análise de conteúdo e organização automática de documentos.

Os Markdown desta aula também entram na geração atual de `corpus/reports/`, junto com os documentos da Aula 04. Por isso, alguns relatórios de chunking e embeddings têm origem em `corpus/processed/aula02/`.
