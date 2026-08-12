# AULA 02

Pasta com os arquivos PDF originais usados na atividade de extracao de informacoes estruturadas.

## Conteudo

- `bioetica_e_ia.pdf`
- `escrita_academica_ia.pdf`
- `twitter_algoritmo.pdf`

Os arquivos convertidos para Markdown e JSON ficam em `Aula02_arquivos_output/`.

## Relatório

### 05/08/2026 - AULA 2

Nessa aula, trabalhei com extração estruturada de informações a partir de arquivos `.md`. O script `Aula02_arquivos_output/test_json_extractor.py` lê o conteúdo de um documento de entrada, envia o texto para um modelo via OpenRouter/OpenAI e solicita a geração de um JSON seguindo um schema fixo com os campos `titulo`, `autores` e `ano`.

O resultado é salvo na própria pasta `Aula02_arquivos_output`, gerando um arquivo `.json` para cada documento processado. A proposta da atividade foi transformar texto livre em dados estruturados, facilitando o uso posterior em pipelines de RAG, análise de conteúdo e organização automática de documentos.
