# AULA 03

Pasta com os scripts e resultados da atividade de embeddings e busca semantica manual.

## Conteudo

- `test_embeddings.py`: gera embeddings para os termos de exemplo.
- `fun_distancia.py`: calcula distancias euclidiana e cosseno entre os embeddings.
- `busca_semantica_manual.py`: compara consultas com os documentos convertidos da Aula 2.
- `*.json`: resultados gerados pelos experimentos.

Os graficos de PCA ficam em `Aula03_graficos/`.

## Relatório

### 07/08/2026 - AULA 3

Nessa aula, explorei embeddings e comparação semântica entre termos. O script `AULA_03/test_embeddings.py` gera embeddings para palavras como `gato`, `felino`, `carro` e `banana`, salvando cada vetor em arquivos `.json` dentro de `AULA_03`.

Também adicionei o script `AULA_03/busca_semantica_manual.py`, que gera o teste com `frase_ancora` e `frases_comparacao` e produz um relatório de busca semântica manual sobre os arquivos `.md` da aula 2, comparando trechos por linha, parágrafo e capítulo.

Depois, o script `AULA_03/fun_distancia.py` calcula distâncias euclidiana e cosseno entre todos os pares de termos e grava o resultado consolidado em `Aula03_distancias.json`. Para visualizar a distribuição dos vetores, o script `Aula03_graficos/visualizar_embeddings.py` aplica PCA em 2D e 3D e exporta os gráficos em `Aula03_graficos/embeddings_pca_2d.png` e `Aula03_graficos/embeddings_pca_3d.html`.
