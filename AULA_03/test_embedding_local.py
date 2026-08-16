import math
import os
from typing import List

from dotenv import load_dotenv
from openai import OpenAI


TESTE_QUERY = "Como a inteligencia artificial pode apoiar a escrita academica?"

TEXTOS_TESTES = [
    "Modelos de linguagem auxiliam pesquisadores na organizacao de textos.",
    "Uma banana madura tem sabor doce.",
    "Ferramentas de IA ajudam na revisao e estruturacao de artigos academicos.",
]


def escolher_modelo(client: OpenAI) -> str:
    modelo_env = os.getenv("LOCAL_EMBEDDING_MODEL")
    if modelo_env and modelo_env.lower() != "inactive":
        return modelo_env

    modelos = client.models.list()
    ids_modelos = [modelo.id for modelo in modelos.data if getattr(modelo, "id", None)]
    if not ids_modelos:
        raise RuntimeError("Nenhum modelo foi retornado pela API local.")

    for modelo_id in ids_modelos:
        modelo_lower = modelo_id.lower()
        if "qwen" in modelo_lower and "embed" in modelo_lower:
            return modelo_id

    raise RuntimeError("Nenhum modelo local de embedding Qwen foi encontrado.")


def similaridade_cosseno(embedding_a: List[float], embedding_b: List[float]) -> float:
    produto = 0.0
    norma_a = 0.0
    norma_b = 0.0

    for valor_a, valor_b in zip(embedding_a, embedding_b):
        produto += valor_a * valor_b
        norma_a += valor_a * valor_a
        norma_b += valor_b * valor_b

    if norma_a == 0 or norma_b == 0:
        return 0.0

    return produto / (math.sqrt(norma_a) * math.sqrt(norma_b))


def main() -> None:
    load_dotenv()

    base_url = os.getenv("LOCAL_OPENAI_BASE_URL", "http://localhost:5001/v1/")
    api_key = os.getenv("LOCAL_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") or "local"

    client = OpenAI(base_url=base_url, api_key=api_key)
    modelo = escolher_modelo(client)

    print(f"API local: {base_url}")
    print(f"Modelo: {modelo}")
    print("Solicitando embeddings...")

    response = client.embeddings.create(
        model=modelo,
        input=[TESTE_QUERY] + TEXTOS_TESTES,
    )

    embeddings = [item.embedding for item in response.data]
    dimensoes = [len(embedding) for embedding in embeddings]
    query_embedding = embeddings[0]
    textos_embeddings = embeddings[1:]

    print(f"Query de teste: {TESTE_QUERY}")
    print(f"Total de textos comparados: {len(TEXTOS_TESTES)}")
    print(f"Dimensoes retornadas: {dimensoes}")
    print(f"Primeiros valores do embedding da query: {query_embedding[:5]}")

    resultados = []
    for texto, texto_embedding in zip(TEXTOS_TESTES, textos_embeddings):
        score = similaridade_cosseno(query_embedding, texto_embedding)
        resultados.append((score, texto))

    print("Similaridades com a query:")
    for score, texto in sorted(resultados, reverse=True):
        print(f"- {score:.6f}: {texto}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("Falha ao testar embeddings locais.")
        print(f"Erro: {exc}")
        raise SystemExit(1)
