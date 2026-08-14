import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

model = os.getenv("OPENAI_MODEL")

response = client.chat.completions.create(
    model=model,
    messages=[
        {
            "role": "user",
            "content": "Qual a capital do Brasil?"
        }
    ],
    max_tokens=1024
)

print(response.choices[0].message.content)
