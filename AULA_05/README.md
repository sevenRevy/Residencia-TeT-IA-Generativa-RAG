# AULA 05

## Exercicio 1 - Documents na mao

## Onde procurar

| Item | Caminho |
| --- | --- |
| Script com dados reais da Aula 04 | `AULA_05/documents_langchain.py` |
| Script com dados reais da Aula 02 | `AULA_05/documents_langchain_aula02.py` |
| Exemplo manual | `AULA_05/manual_documents_langchain.py` |
| Relatorios de entrada | `corpus/reports/completo_corpus_processed_aula*_*.json` |
| Output completo Aula 04 | `corpus/metadata/aula05/documents_langchain_aula04.json` |
| Output completo Aula 02 | `corpus/metadata/aula05/documents_langchain_aula02.json` |
| Resumo dos experimentos | `corpus/reports/summary.json` |
| Fontes Markdown da Aula 04 | `corpus/processed/aula04/` |
| Fontes Markdown herdadas da Aula 02 | `corpus/processed/aula02/` |

### Explicacao do output

O script `documents_langchain.py` usa dados reais da Aula 04. A geracao atual da Aula 04 salva um arquivo por documento e estrategia em `corpus/reports/`, como `completo_corpus_processed_aula04_gpt3_language_models_md_fixo_1000.json`. Ao todo, a pasta atual tem 120 relatorios `completo_*.json` e o resumo `summary.json`. As fontes Markdown ficam em `corpus/processed/aula04/`, usando tambem `corpus/processed/aula02/` para documentos herdados das aulas anteriores.

No exemplo manual, o primeiro bloco mostra que a pasta `corpus/processed/aula04/` foi encontrada corretamente:

```text
total_arquivos_md: 9
```

Isso significa que o script localizou os arquivos Markdown processados da Aula 04. A lista logo abaixo mostra os nomes desses arquivos, como `attention_is_all_you_need.md`, `bert_pretraining.md` e `retrieval_augmented_generation.md`.

O bloco `Lista completa de Document` mostra os 5 objetos `Document` criados manualmente no script. Cada documento tem dois campos principais:

- `page_content`: o texto do documento.
- `metadata`: um dicionario com informacoes extras sobre esse texto.

Exemplo:

```python
Document(
    page_content="Embeddings sao representacoes vetoriais densas de texto.",
    metadata={
        "fonte": "gpt3_language_models.md",
        "pagina": 1,
        "tema": "embeddings",
        "autor": "Tom B. Brown et al.",
    },
)
```

Nesse exemplo, o texto fica em `page_content`. Tudo que descreve o texto, como fonte, pagina, tipo, tema e autor, fica em `metadata`.

O resultado:

```text
len(documentos): 5
```

confirma que a lista `documentos` contem 5 objetos `Document`.

### Resultados dos testes de metadata

- `metadata` aceita valores simples como `str`, `int`, `float`, `bool` e tambem estruturas como `list` e `dict`.
- No teste com lista, o campo `tags` foi aceito e preservado como `list`.
- No teste com dicionario aninhado, o campo `detalhes` foi aceito e preservado como `dict`.
- Ao criar um `Document` sem informar `metadata`, o LangChain cria um dicionario vazio: `{}`.

### Diferenca entre os tres casos

#### 1. Metadata com lista

Neste teste, o campo `tags` recebe uma lista:

```python
"tags": ["langchain", "document", "lista"]
```

O output mostra:

```text
tipo de metadata['tags']: list
```

Isso confirma que o LangChain preservou a lista dentro de `metadata`. Esse formato e util quando um documento pode ter varias categorias, palavras-chave, topicos ou marcadores.

#### 2. Metadata com dicionario aninhado

Neste teste, o campo `detalhes` recebe outro dicionario:

```python
"detalhes": {
    "curso": "RAG",
    "estrategia": "teste manual",
    "campos_testados": ["dict", "str", "int", "list"],
}
```

O output mostra:

```text
tipo de metadata['detalhes']: dict
```

Isso confirma que o LangChain aceitou um dicionario dentro de `metadata`. Esse formato e util quando os metadados precisam representar uma estrutura mais organizada, por exemplo dados de origem, configuracao de processamento ou informacoes agrupadas.

#### 3. Document sem metadata

Neste teste, o `Document` foi criado apenas com `page_content`:

```python
Document(page_content="Documento criado sem informar metadata.")
```

O output mostra:

```text
metadata: {}
tipo de metadata: dict
```

Isso significa que, quando `metadata` nao e informado, o LangChain nao deixa o campo inexistente. Ele cria automaticamente um dicionario vazio. Portanto, o documento continua tendo `metadata`, mas sem nenhuma informacao adicional.

## Exercicio 2 - Projetando o schema de metadados

O script `documents_langchain.py` usa todos os relatorios da Aula 04 em `corpus/reports/`, sem limitar a quantidade de chunks carregados. Na execucao validada, ele carregou 90 relatorios da Aula 04 e criou 26.490 objetos `Document`, salvos em `corpus/metadata/aula05/documents_langchain_aula04.json`. O script `documents_langchain_aula02.py` reaproveita o mesmo schema para a Aula 02; na execucao validada, ele carregou 30 relatorios e criou 2.874 objetos `Document`, salvos em `corpus/metadata/aula05/documents_langchain_aula02.json`.

### Schema final

| Campo | Tipo | Descricao |
| --- | --- | --- |
| `fonte` | `str` | Nome do arquivo .md de origem. |
| `documento_id` | `str` | Identificador estavel do documento. |
| `chunk_index` | `int` | Posicao do chunk dentro do documento. |
| `estrategia` | `str` | Estrategia da Aula 04 usada para gerar o chunk. |
| `chunk_size` | `int \| None` | Configuracao de tamanho usada na estrategia. |
| `chunk_overlap` | `int` | Configuracao de sobreposicao usada na estrategia. |
| `n_caracteres` | `int` | Tamanho real do chunk em caracteres. |
| `aula` | `str \| None` | Aula de origem do documento processado. |
| `caminho_relativo` | `str \| None` | Caminho do arquivo dentro do repositorio, quando localizado. |
| `fonte_online` | `str \| None` | Link online para a fonte original, quando disponivel. |
| `pdf_link` | `str \| None` | Link local para o PDF original e pagina citavel, quando disponivel. |
| `pagina_inicio` | `int \| None` | Primeira pagina de origem indicada nos metadados Docling. |
| `pagina_fim` | `int \| None` | Ultima pagina de origem indicada nos metadados Docling. |
| `secao` | `str \| None` | Secao Docling associada ao chunk, quando disponivel. |
| `subsecao` | `str \| None` | Subsecao Docling associada ao chunk, quando disponivel. |
| `heading_path` | `list[str]` | Hierarquia de titulos Markdown associada ao chunk. |
| `titulo_secao` | `str \| None` | Cabecalho Markdown mais proximo antes do chunk. |
| `posicao_inicio` | `int \| None` | Indice inicial do chunk no texto completo do documento. |
| `posicao_fim` | `int \| None` | Indice final do chunk no texto completo do documento. |
| `chunk_id` | `str \| None` | Identificador unico do chunk no relatorio da Aula 04. |
| `relatorio_origem` | `str` | Relatorio JSON de onde o chunk foi carregado. |
| `modelo_embedding` | `str \| None` | Modelo de embedding usado para gerar o relatorio. |
| `score_similaridade` | `float \| None` | Score calculado na busca semantica da Aula 04. |
| `query_origem` | `str \| None` | Pergunta usada para recuperar o chunk no relatorio da Aula 04. |

### Justificativa dos campos proprios

- `aula`: permite filtrar resultados por etapa do curso, separando Aula 02 de Aula 04.
- `caminho_relativo`: permite auditar o arquivo Markdown de origem dentro do repositorio.
- `pdf_link`: permite citar exatamente o PDF e a pagina de origem.
- `pagina_inicio` e `pagina_fim`: permitem saber se o chunk veio de uma pagina ou atravessou mais de uma pagina.
- `secao`, `subsecao` e `heading_path`: permitem responder em que parte conceitual do documento o trecho apareceu.
- `posicao_inicio` e `posicao_fim`: permitem recuperar texto anterior ou posterior ao chunk quando ele vier cortado.
- `chunk_id`: permite rastrear o mesmo chunk no relatorio e em uma futura base vetorial.
- `relatorio_origem`: permite auditar qual experimento gerou o chunk.
- `modelo_embedding`: permite saber qual modelo vetorial foi usado no relatorio.
- `query_origem` e `score_similaridade`: permitem explicar por qual pergunta o chunk apareceu e com que proximidade semantica, quando esses campos existirem.

### Exemplo preenchido em JSON

```json
{
  "page_content": "olutions entirely. Experiments on two machine translation tasks show these models to be superior in quality while being more parallelizable and requiring significantly less time to train. Our model achieves 28.4 BLEU on the WMT 2014 Englishto-German translation task, improving over the existing best results, including ensembles, by over 2 BLEU. On the WMT 2014 English-to-French translation task, our model establishes a new single-model state-of-the-art BLEU score of 41.8 after training for 3.5 d",
  "metadata": {
    "fonte": "attention_is_all_you_need.md",
    "documento_id": "corpus_processed_aula04_attention_is_all_you_need",
    "chunk_index": 3,
    "estrategia": "fixo_500",
    "chunk_size": 500,
    "chunk_overlap": 0,
    "n_caracteres": 500,
    "aula": "aula04",
    "caminho_relativo": "corpus/processed/aula04/attention_is_all_you_need.md",
    "fonte_online": null,
    "pdf_link": "corpus/raw/aula04/attention_is_all_you_need.pdf#page=1",
    "pagina_inicio": 1,
    "pagina_fim": 1,
    "secao": "Abstract",
    "subsecao": null,
    "heading_path": [
      "Abstract"
    ],
    "titulo_secao": "Abstract",
    "posicao_inicio": 1494,
    "posicao_fim": 1994,
    "chunk_id": "corpus_processed_aula04_attention_is_all_you_need_test02_chunk003",
    "relatorio_origem": "corpus/reports/completo_corpus_processed_aula04_attention_is_all_you_need_md_fixo_500.json",
    "modelo_embedding": "Qwen3-Embedding-0.6B.Q8_0.gguf",
    "score_similaridade": null,
    "query_origem": null
  }
}
```

### Respostas

- Para citar a fonte na resposta final do RAG, eu incluiria `pdf_link`, junto de `fonte`, `pagina_inicio`, `pagina_fim`, `secao`, `heading_path` e `chunk_index`. Assim a resposta pode apontar para o PDF, a pagina e o trecho recuperado.
- `chunk_index` e util porque permite buscar os chunks vizinhos quando o trecho recuperado esta cortado no meio de uma explicacao. Por exemplo, se o chunk 18 foi recuperado, posso consultar os chunks 17 e 19 do mesmo documento e da mesma estrategia para reconstruir o contexto.
