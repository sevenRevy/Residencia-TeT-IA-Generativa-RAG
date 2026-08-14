# AULA 05

## Exercicio 1 - Documents na mao

## Onde procurar

| Item | Caminho |
| --- | --- |
| Script com dados reais | `AULA_05/documents_langchain.py` |
| Exemplo manual | `AULA_05/manual_documents_langchain.py` |
| Relatorio de entrada | `corpus/reports/aula04/completo_fixo_1000.json` |
| Fontes Markdown da Aula 04 | `corpus/processed/aula04/` |
| Fontes Markdown herdadas da Aula 02 | `corpus/processed/aula02/` |

### Explicacao do output

O script `documents_langchain.py` usa dados reais da Aula 04. Ele le o relatorio `corpus/reports/aula04/completo_fixo_1000.json` e resolve as fontes Markdown em `corpus/processed/aula04/`, usando `corpus/processed/aula02/` quando o relatorio referencia documentos herdados das aulas anteriores.

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
