import os
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENAI_API_KEY"),
)


output_folder = Path("Aula03_embedding_output")
output_folder.mkdir(exist_ok=True)



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

for termo in termos:

    response = client.embeddings.create(
        model="nvidia/nemotron-3-embed-1b:free",
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