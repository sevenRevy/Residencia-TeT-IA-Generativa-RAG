import os
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url=os.getenv("LOCAL_OPENAI_BASE_URL", "http://localhost:5001/v1/"),
    api_key=os.getenv("LOCAL_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") or "local",
)


REPO_DIR = Path(__file__).resolve().parents[1]
output_folder = REPO_DIR / "corpus" / "embeddings" / "aula03"
output_folder.mkdir(exist_ok=True)


def escolher_modelo_embedding():
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

embedding_model = escolher_modelo_embedding()
print(f"Modelo local de embedding: {embedding_model}")

for termo in termos:

    response = client.embeddings.create(
        model=embedding_model,
        input=termo,
        encoding_format="float"
    )

    embedding = response.data[0].embedding

    arquivo = output_folder / f"{termo}.json"

    with arquivo.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "texto": termo,
                "embedding": embedding
            },
            f,
            ensure_ascii=False,
            indent=2
        )

    print(f"Salvo: {arquivo}")
