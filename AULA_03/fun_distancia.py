import json
import math
from pathlib import Path
from itertools import combinations

embedding_folder = Path("AULA_03")


def carregar_embedding(nome):
    arquivo = embedding_folder / f"{nome}.json"

    with arquivo.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict) and "embedding" in data:
        return data["embedding"]

    raise ValueError(f"Formato inválido em {arquivo}. Esperado um dict com a chave 'embedding'.")


def distancia_euclidiana(embedding_a, embedding_b):
    if len(embedding_a) != len(embedding_b):
        raise ValueError("Embeddings precisam ter a mesma dimensão")

    soma = 0
    for a, b in zip(embedding_a, embedding_b):
        soma += (a - b) ** 2

    return math.sqrt(soma)


def distancia_cosseno(embedding_a, embedding_b):
    if len(embedding_a) != len(embedding_b):
        raise ValueError("Embeddings precisam ter a mesma dimensão")

    produto_escalar = 0
    norma_a = 0
    norma_b = 0

    for a, b in zip(embedding_a, embedding_b):
        produto_escalar += a * b
        norma_a += a ** 2
        norma_b += b ** 2

    similaridade = produto_escalar / (math.sqrt(norma_a) * math.sqrt(norma_b))
    return 1 - similaridade


termos = [
    "gato",
    "felino",
    "cachorro",
    "carro",
    "caminhão",
    "moto",
    "banana",
    "maçã",
    "goiaba"
]

embeddings = {}
for termo in termos:
    embeddings[termo] = carregar_embedding(termo)

resultados = []

for termo_a, termo_b in combinations(termos, 2):
    emb_a = embeddings[termo_a]
    emb_b = embeddings[termo_b]

    resultado = {
        "termo_a": termo_a,
        "termo_b": termo_b,
        "distancia_euclidiana": distancia_euclidiana(emb_a, emb_b),
        "distancia_cosseno": distancia_cosseno(emb_a, emb_b),
    }
    resultados.append(resultado)

resultados.sort(key=lambda x: x["distancia_cosseno"])

for item in resultados:
    print("-" * 50)
    print(f"{item['termo_a']} x {item['termo_b']}")
    print(f"Euclidiana: {item['distancia_euclidiana']:.4f}")
    print(f"Cosseno: {item['distancia_cosseno']:.4f}")

output_file = embedding_folder / "Aula03_distancias.json"
with output_file.open("w", encoding="utf-8") as f:
    json.dump(resultados, f, ensure_ascii=False, indent=2)

print("\nResultado salvo em:", output_file)
