import os
import gc
from pathlib import Path
from pypdf import PdfReader, PdfWriter

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend

input_folder = Path(".")
output_folder = Path("./aula04_arquivos_output")
output_folder.mkdir(parents=True, exist_ok=True)

os.environ["TORCH_COMPILE_DISABLE"] = "1"

CHUNK_SIZE = 10  

## 1. PIPELINE DE ALTA PERFORMANCE
pipeline_options = PdfPipelineOptions()
pipeline_options.do_table_structure = True     # Desativa IA pesada de tabelas
pipeline_options.do_ocr = False                  # Desativa OCR
pipeline_options.generate_page_images = False    # Desativa imagens
pipeline_options.generate_picture_images = False

format_options = {
    InputFormat.PDF: PdfFormatOption(
        pipeline_options=pipeline_options,
        backend=PyPdfiumDocumentBackend
    )
}

converter = DocumentConverter(format_options=format_options)

def process_pdf_in_chunks(pdf_path: Path, chunk_size: int) -> str:
    """Divide o PDF em lotes de páginas, converte cada lote e junta tudo no final."""
    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)
    full_markdown_parts = []

    print(f"Total de páginas em '{pdf_path.name}': {total_pages}")

    for start_page in range(0, total_pages, chunk_size):
        end_page = min(start_page + chunk_size, total_pages)
        print(f"  -> Processando páginas {start_page + 1} até {end_page} de {total_pages}...")

        # 1. Extrai o bloco de páginas atual
        writer = PdfWriter()
        for page_num in range(start_page, end_page):
            writer.add_page(reader.pages[page_num])

        temp_chunk_path = pdf_path.parent / f"_temp_{pdf_path.stem}_{start_page}.pdf"
        with open(temp_chunk_path, "wb") as f:
            writer.write(f)

        try:
            # 2. Converte apenas o lote atual
            result = converter.convert(temp_chunk_path)
            md_part = result.document.export_to_markdown()
            full_markdown_parts.append(md_part)

        finally:
            # 3. Limpa o arquivo temporário e força a liberação de memória
            if temp_chunk_path.exists():
                temp_chunk_path.unlink()
            if 'result' in locals():
                del result
            gc.collect()

    # Junta todas as partes com uma separação visual
    return "\n\n---\n\n".join(full_markdown_parts)


START_FROM = "instruct_gpt.pdf"
started = False if START_FROM else True

pdf_files = sorted(list(input_folder.glob("*.pdf")))
print(f"Encontrados {len(pdf_files)} arquivo(s) PDF.\n")

for input_file in pdf_files:
    if input_file.name.startswith("_temp_"):
        continue

    if not started:
        if input_file.name == START_FROM:
            started = True
        else:
            print(f"Pulando (anterior a {START_FROM}): {input_file.name}")
            continue

    output_file = output_folder / f"{input_file.stem}.md"

    if output_file.exists():
        print(f"Pulando (já convertido): {input_file.name}")
        continue

    try:
        print(f"Iniciando conversão completa em lotes de: {input_file.name}")
        
        # Converte o documento por inteiro em lotes sem estourar a RAM
        markdown_completo = process_pdf_in_chunks(input_file, CHUNK_SIZE)

        output_file.write_text(markdown_completo, encoding="utf-8")
        print(f"Sucesso! Arquivo completo salvo em: {output_file}\n")

    except Exception as e:
        print(f"Erro ao processar {input_file.name}: {e}\n")