import json
import os

from dotenv import load_dotenv
from openai import OpenAI


PALAVRAS_TESTE = [
    "banana",
    "cachorro",
    "caminhão",
    "carro",
    "felino",
    "gato",
    "goiaba",
    "maçã",
    "moto",
]


def escolher_modelo(client: OpenAI) -> str:
    modelo_env = os.getenv("LOCAL_EMBEDDING_MODEL")
    if modelo_env and modelo_env.lower() != "inactive":
        return modelo_env

    modelos = client.models.list()
    ids_modelos = [modelo.id for modelo in modelos.data if getattr(modelo, "id", None)]
    for modelo_id in ids_modelos:
        modelo_lower = modelo_id.lower()
        if "qwen" in modelo_lower and "embed" in modelo_lower:
            return modelo_id

    raise RuntimeError("Nenhum modelo local de embedding Qwen foi encontrado.")


def main() -> None:
    load_dotenv()

    base_url = os.getenv("LOCAL_OPENAI_BASE_URL", "http://localhost:5001/v1/")
    api_key = os.getenv("LOCAL_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") or "local"

    client = OpenAI(base_url=base_url, api_key=api_key)
    modelo = escolher_modelo(client)

    print(f"API local: {base_url}")
    print(f"Modelo: {modelo}")

    response = client.embeddings.create(
        model=modelo,
        input=PALAVRAS_TESTE,
    )

    for palavra, item in zip(PALAVRAS_TESTE, response.data):
        resultado = {
            "texto": palavra,
            "dimensoes": len(item.embedding),
            "embedding": item.embedding,
        }

        print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
