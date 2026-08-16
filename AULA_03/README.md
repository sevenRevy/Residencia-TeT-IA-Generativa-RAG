# AULA 03

Pasta com os scripts da atividade de embeddings e busca semantica manual. Os JSONs atuais foram regenerados com o modelo local `Qwen3-Embedding-0.6B.Q8_0.gguf` e ficam em `corpus/embeddings/aula03/`.

## Onde procurar

| Item | Caminho |
| --- | --- |
| Entrada textual da Aula 02 | `corpus/processed/aula02/` |
| Embeddings, distancias e busca semantica | `corpus/embeddings/aula03/` |
| Embeddings antigos Nemotron arquivados | `corpus/archive/embeddings/aula03/nemotron-3-embed-1b/` |
| Relatorios atuais de chunking da Aula 04 | `corpus/reports/` |
| Scripts da aula | `AULA_03/` |
| Graficos PCA | `AULA_03/Aula03_graficos/` |

## Conteudo

- `test_embeddings.py`: gera embeddings para os termos de exemplo.
- `fun_distancia.py`: calcula distancias euclidiana e cosseno entre os embeddings.
- `busca_semantica_manual.py`: compara consultas com os documentos convertidos da Aula 2.

Os graficos de PCA ficam em `Aula03_graficos/`.

## Relatório

### 07/08/2026 - AULA 3

Nessa aula, explorei embeddings e comparação semântica entre termos. O script `AULA_03/test_embeddings.py` gera embeddings para palavras como `gato`, `felino`, `carro` e `banana`, usando o modelo local Qwen configurado no `.env` e salvando cada vetor em arquivos `.json` dentro de `corpus/embeddings/aula03/`. Os embeddings antigos feitos com Nemotron foram preservados em `corpus/archive/embeddings/aula03/nemotron-3-embed-1b/`.

Também adicionei o script `AULA_03/busca_semantica_manual.py`, que gera o teste com `frase_ancora` e `frases_comparacao` e produz um relatório de busca semântica manual sobre os arquivos `.md` da aula 2 em `corpus/processed/aula02/`, comparando trechos por linha, parágrafo e capítulo.

Depois, o script `AULA_03/fun_distancia.py` calcula distâncias euclidiana e cosseno entre todos os pares de termos e grava o resultado consolidado em `corpus/embeddings/aula03/Aula03_distancias.json`. Para visualizar a distribuição dos vetores, o script `Aula03_graficos/visualizar_embeddings.py` aplica PCA em 2D e 3D e exporta os gráficos em `Aula03_graficos/embeddings_pca_2d.png` e `Aula03_graficos/embeddings_pca_3d.html`.

Os relatórios de chunking e embeddings usados nas aulas seguintes não ficam mais em `corpus/reports/aula04/`. A versão atual está consolidada em `corpus/reports/`, com 120 arquivos `completo_*.json` e o resumo `corpus/reports/summary.json`.
