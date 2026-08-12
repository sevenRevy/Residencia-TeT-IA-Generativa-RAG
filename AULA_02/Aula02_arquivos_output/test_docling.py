import os
from pathlib import Path
from docling.document_converter import DocumentConverter


## INPUT
input_file = Path("AULA_02/twitter_algoritmo.pdf")

## ENV
output_folder = Path("Aula02_arquivos_output")
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
