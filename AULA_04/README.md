# AULA 04

Pasta com a rotina de conversao e os experimentos de chunking e busca semantica com LangChain. Os PDFs, Markdown e relatorios ficam organizados em `corpus/`.

## Onde procurar

| Item | Caminho |
| --- | --- |
| PDFs originais | `corpus/raw/aula04/` |
| Markdown gerado pelo Docling | `corpus/processed/aula04/` |
| Relatorios completos e filtrados | `corpus/reports/aula04/` |
| Script de conversao | `AULA_04/a04_docling.py` |

## Conteudo

- `a04_docling.py`: converte os PDFs de `corpus/raw/aula04/` em Markdown usando Docling.

Os relatorios consolidados e filtrados ficam em `corpus/reports/aula04/`.

## Relatório

### 10/08/2026 - AULA 4

Nessa aula, avancei na implementação da busca semântica utilizando LangChain e embeddings gerados através da API da OpenAI. O projeto passou a trabalhar diretamente com os documentos em formato `.md` de `corpus/processed/aula04/`, realizando a leitura e divisão dos textos em diferentes estratégias de chunking, permitindo comparar formas distintas de segmentação dos documentos.

Também implementei a geração de embeddings em lotes e o cálculo de similaridade por cosseno entre os vetores. A partir desses recursos, foi criada uma função de busca semântica capaz de receber uma consulta e recuperar os trechos mais semelhantes dentro do corpus de documentos.

Por fim, desenvolvi a geração de relatórios para múltiplas consultas, salvando os resultados da busca em arquivos `.json` dentro de `corpus/reports/aula04/`. Durante a implementação, também foram adicionados tratamentos para erros relacionados à chave da API e à dimensão dos embeddings. Além da implementação da busca semântica, ampliei o corpus utilizado nos testes com novos documentos, permitindo avaliar o funcionamento da recuperação semântica em uma base maior e mais diversificada.
