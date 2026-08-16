import os
import gc
import base64
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from pathlib import Path
from pypdf import PdfReader, PdfWriter

from dotenv import load_dotenv
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling_core.types.doc import PictureItem
from openai import OpenAI
from docling_core.types.doc import ImageRefMode, PictureItem

load_dotenv()

REPO_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = REPO_DIR / "corpus" / "raw"
PROCESSED_DIR = REPO_DIR / "corpus" / "processed"
AULAS_PDF = ["aula02", "aula04"]
OPENROUTER_VISION_MODEL = os.getenv(
    "OPENROUTER_VISION_MODEL",
    "nvidia/nemotron-nano-12b-v2-vl:free",
)
OPENROUTER_VISION_FALLBACK_MODELS = [
    "meta-llama/llama-4-scout:free",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
]

os.environ["TORCH_COMPILE_DISABLE"] = "1"

PDF_PAGES_PER_BATCH = 5
OPENROUTER_TIMEOUT_SECONDS = 60
IMAGE_DESCRIPTION_CONCURRENCY = int(os.getenv("IMAGE_DESCRIPTION_CONCURRENCY", "1"))
FORCE_REPROCESS = False

pipeline_options = PdfPipelineOptions()
pipeline_options.do_table_structure = True   
pipeline_options.do_ocr = True                  
pipeline_options.generate_page_images = False    
pipeline_options.generate_picture_images = True

format_options = {
    InputFormat.PDF: PdfFormatOption(
        pipeline_options=pipeline_options,
        backend=PyPdfiumDocumentBackend
    )
}

converter = DocumentConverter(format_options=format_options)
openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
openrouter_client = (
    OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=openrouter_api_key,
        timeout=OPENROUTER_TIMEOUT_SECONDS,
    )
    if openrouter_api_key
    else None
)

MARKDOWN_IMAGE_MODE = ImageRefMode.PLACEHOLDER if ImageRefMode else None


def export_markdown(document, page_no: int | None = None) -> str:
    """Exporta Markdown preservando marcadores de imagem quando o Docling suportar."""
    if MARKDOWN_IMAGE_MODE is None:
        return document.export_to_markdown(page_no=page_no)
    return document.export_to_markdown(image_mode=MARKDOWN_IMAGE_MODE, page_no=page_no)


def metadados_secao(heading_stack: dict[int, str]) -> dict:
    heading_path = [
        heading_stack[nivel]
        for nivel in sorted(heading_stack)
        if heading_stack.get(nivel)
    ]

    return {
        "section": heading_path[0] if heading_path else None,
        "subsection": heading_path[-1] if len(heading_path) > 1 else None,
        "heading_path": heading_path,
    }


def inserir_metadados_secao_no_markdown(markdown: str, heading_stack: dict[int, str]) -> tuple[str, dict[int, str]]:
    linhas = []

    for linha in markdown.splitlines():
        linhas.append(linha)

        match = re.match(r"^(#{1,6})\s+(.+)$", linha)
        if not match:
            continue

        nivel = len(match.group(1))
        titulo = match.group(2).strip()
        heading_stack[nivel] = titulo

        for nivel_maior in range(nivel + 1, 7):
            heading_stack.pop(nivel_maior, None)

        linhas.append(comentario_json("section_metadata", metadados_secao(heading_stack)))

    return "\n".join(linhas), heading_stack


def montar_pdf_link(pdf_path: Path, page: int) -> str:
    caminho_relativo = pdf_path.relative_to(REPO_DIR).as_posix()
    return f"{caminho_relativo}#page={page}"


def serializar_bbox(bbox) -> dict | None:
    if bbox is None:
        return None

    dados = {}
    for nome in ("l", "t", "r", "b", "left", "top", "right", "bottom"):
        if hasattr(bbox, nome):
            dados[nome] = getattr(bbox, nome)

    if dados:
        return dados

    if hasattr(bbox, "model_dump"):
        return bbox.model_dump()

    return None


def extrair_bbox(elemento: PictureItem) -> dict | None:
    prov = getattr(elemento, "prov", None) or []
    if not prov:
        return None
    return serializar_bbox(getattr(prov[0], "bbox", None))


def descrever_imagem(pil_image) -> tuple[str | None, str | None]:
    if openrouter_client is None:
        return None, None

    buffer = BytesIO()
    pil_image.save(buffer, format="PNG")
    imagem_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "Descreva objetivamente esta imagem extraida de um PDF academico. "
                        "Inclua texto visivel, tipo de figura, e relacao provavel com o documento. "
                        "Responda em portugues em ate 3 frases."
                    ),
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{imagem_base64}",
                    },
                },
            ],
        }
    ]

    ultimo_erro = None
    for modelo in [OPENROUTER_VISION_MODEL, *OPENROUTER_VISION_FALLBACK_MODELS]:
        try:
            response = openrouter_client.chat.completions.create(
                model=modelo,
                messages=messages,
            )
            return response.choices[0].message.content, modelo
        except Exception as e:
            ultimo_erro = e

    raise RuntimeError(f"Falha ao descrever imagem com todos os modelos vision: {ultimo_erro}")


def pagina_original(elemento: PictureItem, batch_start_page: int) -> int:
    prov = getattr(elemento, "prov", None) or []
    if not prov:
        return batch_start_page

    page_no = getattr(prov[0], "page_no", 1) or 1
    return batch_start_page + page_no - 1


def montar_metadados_imagens(document, pdf_path: Path, page: int, section_data: dict | None) -> list[dict]:
    imagens = []
    contador = 1
    section_data = section_data or {}

    for elemento, _level in document.iterate_items():
        if not isinstance(elemento, PictureItem):
            continue

        imagem_page = pagina_original(elemento, page)

        item = {
            "image_id": f"{pdf_path.stem}_page{imagem_page:03d}_image{contador:03d}",
            "document_name": pdf_path.name,
            "page": imagem_page,
            "section": section_data.get("section"),
            "subsection": section_data.get("subsection"),
            "heading_path": section_data.get("heading_path", []),
            "pdf_link": montar_pdf_link(pdf_path, imagem_page),
            "bbox": extrair_bbox(elemento),
            "image_description": None,
            "image_description_model": None,
            "image_description_skipped": False,
            "image_description_primary_model": OPENROUTER_VISION_MODEL,
            "_picture_item": elemento,
        }

        imagens.append(item)
        contador += 1

    return imagens


def descrever_item_imagem(item: dict) -> dict:
    pil_image = item.pop("_pil_image", None)
    item.pop("_picture_item", None)

    if pil_image is None:
        item["image_description_skipped"] = True
        item["image_description_skip_reason"] = "imagem_indisponivel"
        return item

    if openrouter_client is None:
        item["image_description_skipped"] = True
        item["image_description_skip_reason"] = "OPENROUTER_API_KEY_ausente"
        return item

    try:
        descricao, modelo_usado = descrever_imagem(pil_image)
        item["image_description"] = descricao
        item["image_description_model"] = modelo_usado
    except Exception as e:
        item["image_description_error"] = str(e)

    return item


def descrever_imagens_do_pdf(image_metadata: list[dict]) -> None:
    if IMAGE_DESCRIPTION_CONCURRENCY <= 1:
        for item in image_metadata:
            descrever_item_imagem(item)
        return

    with ThreadPoolExecutor(max_workers=IMAGE_DESCRIPTION_CONCURRENCY) as executor:
        futuros = {
            executor.submit(descrever_item_imagem, item): indice
            for indice, item in enumerate(image_metadata)
        }
        for futuro in as_completed(futuros):
            indice = futuros[futuro]
            image_metadata[indice] = futuro.result()



def comentario_json(prefixo: str, dados) -> str:
    return f"<!-- {prefixo}: {json.dumps(dados, ensure_ascii=False)} -->"


def inserir_metadados_imagens_no_markdown(markdown: str, image_metadata: list[dict]) -> str:
    partes = markdown.split("<!-- image -->")
    if len(partes) == 1:
        return markdown

    resultado = [partes[0]]
    for indice, parte in enumerate(partes[1:]):
        if indice < len(image_metadata):
            resultado.append(comentario_json("image_metadata", image_metadata[indice]))
        else:
            resultado.append("<!-- image -->")
        resultado.append(parte)

    return "".join(resultado)


def process_pdf_in_chunks(pdf_path: Path, chunk_size: int) -> str:
    """Divide o PDF em páginas/lotes, converte cada parte e preserva metadados no Markdown."""
    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)
    full_markdown_parts = []
    heading_stack = {}

    print(f"Total de páginas em '{pdf_path.name}': {total_pages}")

    for start_page in range(0, total_pages, chunk_size):
        end_page = min(start_page + chunk_size, total_pages)
        print(f"  -> Processando páginas {start_page + 1} até {end_page} de {total_pages}...")

        writer = PdfWriter()
        for page_num in range(start_page, end_page):
            writer.add_page(reader.pages[page_num])

        temp_chunk_path = pdf_path.parent / f"_temp_{pdf_path.stem}_{start_page}.pdf"
        with open(temp_chunk_path, "wb") as f:
            writer.write(f)

        try:
            result = converter.convert(temp_chunk_path)
            image_metadata = montar_metadados_imagens(result.document, pdf_path, start_page + 1, None)
            for item in image_metadata:
                try:
                    elemento = item.pop("_picture_item")
                    item["_pil_image"] = elemento.get_image(result.document)
                except Exception as e:
                    item["image_description_error"] = str(e)
            descrever_imagens_do_pdf(image_metadata)

            for relative_page, original_page in enumerate(range(start_page + 1, end_page + 1), start=1):
                md_part = export_markdown(result.document, page_no=relative_page)
                md_part, heading_stack = inserir_metadados_secao_no_markdown(md_part, heading_stack)
                section_data = metadados_secao(heading_stack)
                page_metadata = {
                    "document_name": pdf_path.name,
                    "page": original_page,
                    "page_start": original_page,
                    "page_end": original_page,
                    "pdf_link": montar_pdf_link(pdf_path, original_page),
                    **section_data,
                }
                page_image_metadata = [
                    {
                        **item,
                        "section": item["section"] or section_data["section"],
                        "subsection": item["subsection"] or section_data["subsection"],
                        "heading_path": item["heading_path"] or section_data["heading_path"],
                    }
                    for item in image_metadata
                    if item["page"] == original_page
                ]
                md_part = inserir_metadados_imagens_no_markdown(md_part, page_image_metadata)
                metadata_comments = [comentario_json("page_metadata", page_metadata)]
                full_markdown_parts.append("\n".join(metadata_comments) + f"\n\n{md_part}")

        finally:
            if temp_chunk_path.exists():
                temp_chunk_path.unlink()
            if 'result' in locals():
                del result
            gc.collect()

    return "\n\n---\n\n".join(full_markdown_parts)


pdf_files = []
for aula in AULAS_PDF:
    input_folder = RAW_DIR / aula
    output_folder = PROCESSED_DIR / aula
    output_folder.mkdir(parents=True, exist_ok=True)

    for pdf_path in sorted(input_folder.glob("*.pdf")):
        pdf_files.append((aula, pdf_path, output_folder / f"{pdf_path.stem}.md"))

print(f"Encontrados {len(pdf_files)} arquivo(s) PDF em {', '.join(AULAS_PDF)}.\n")

for aula, input_file, output_file in pdf_files:
    if input_file.name.startswith("_temp_"):
        continue

    if output_file.exists():
        if not FORCE_REPROCESS:
            print(f"Pulando (já convertido em {aula}): {input_file.name}")
            continue
        print(f"Reprocessando arquivo existente em {aula}: {input_file.name}")

    try:
        print(f"Iniciando conversão completa em lotes de {aula}: {input_file.name}")
        
        markdown_completo = process_pdf_in_chunks(input_file, PDF_PAGES_PER_BATCH)

        output_file.write_text(markdown_completo, encoding="utf-8")
        print(f"Sucesso! Arquivo completo salvo em: {output_file}\n")

    except Exception as e:
        print(f"Erro ao processar {input_file.name}: {e}\n")
