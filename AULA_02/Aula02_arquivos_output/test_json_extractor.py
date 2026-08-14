from pathlib import Path
import json
from openai import OpenAI
import os
from dotenv import load_dotenv


load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

model = os.getenv("OPENAI_MODEL")


REPO_DIR = Path(__file__).resolve().parents[2]
input_file = REPO_DIR / "corpus" / "processed" / "aula02" / "twitter_algoritmo.md"

text = input_file.read_text(encoding="utf-8")

response = client.chat.completions.create(
    model,
    messages=[
        {
            "role": "system",
            "content": "Extraia as informações do documento."
        },
        {
            "role": "user",
            "content": text
        }
    ],
    max_tokens=1024,
    response_format={
        "type": "json_schema",
        "json_schema": {
            "name": "paper_metadata",
            "strict": True,
            "schema": {
                "type": "object",
                "properties": {
                    "titulo": {
                        "type": "string",
                        "description": "Título do trabalho"
                    },
                    "autores": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "Lista de autores"
                    },
                    "ano": {
                        "type": "integer",
                        "description": "Ano de publicação"
                    }
                },
                "required": [
                    "titulo",
                    "autores",
                    "ano"
                ],
                "additionalProperties": False
            }
        }
    }
)



data = json.loads(response.choices[0].message.content)

output_folder = REPO_DIR / "corpus" / "metadata" / "aula02"
output_folder.mkdir(exist_ok=True)

output_file = output_folder / f"{input_file.stem}.json"

with output_file.open("w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Salvo em: {output_file}")

print(response.choices[0].message.content)

