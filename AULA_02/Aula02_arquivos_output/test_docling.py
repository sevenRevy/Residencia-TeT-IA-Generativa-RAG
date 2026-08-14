import os
from pathlib import Path
from docling.document_converter import DocumentConverter


## INPUT
REPO_DIR = Path(__file__).resolve().parents[2]
input_file = REPO_DIR / "corpus" / "raw" / "aula02" / "twitter_algoritmo.pdf"

## ENV
output_folder = REPO_DIR / "corpus" / "processed" / "aula02"
output_folder.mkdir(parents=True, exist_ok=True)
os.environ["TORCH_COMPILE_DISABLE"] = "1"

### 

converter = DocumentConverter()

result = converter.convert(input_file)

markdown = result.document.export_to_markdown()

## Output

output_file = output_folder / f"{input_file.stem}.md"

output_file.write_text(
    markdown,
    encoding="utf-8"
)

print(f"Saved to: {output_file}")
