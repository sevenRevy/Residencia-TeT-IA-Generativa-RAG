import json
import re
from pathlib import Path
from typing import Any, Dict, List

from langchain_core.documents import Document


REPO_DIR = Path(__file__).resolve().parents[1]
CORPUS_DIR = REPO_DIR / "corpus"
DOCUMENTOS_DIR = CORPUS_DIR / "processed" / "aula04"
DOCUMENTOS_FALLBACK_DIR = CORPUS_DIR / "processed" / "aula02"
RELATORIOS_DIR = CORPUS_DIR / "reports"
SAIDA_DOCUMENTS_DIR = CORPUS_DIR / "metadata" / "aula05"
AULA_RELATORIOS = "aula04"
NUMERO_EXEMPLOS_JSON = 1

ESTRATEGIAS_CONFIG = {
    "fixo_200": {"grupo": 1, "chunk_size": 200, "chunk_overlap": 0},
    "fixo_500": {"grupo": 2, "chunk_size": 500, "chunk_overlap": 0},
    "fixo_1000": {"grupo": 3, "chunk_size": 1000, "chunk_overlap": 0},
    "fixo_2000": {"grupo": 4, "chunk_size": 2000, "chunk_overlap": 0},
    "fixo_500_overlap_50": {"grupo": 5, "chunk_size": 500, "chunk_overlap": 50},
    "fixo_500_overlap_200": {"grupo": 6, "chunk_size": 500, "chunk_overlap": 200},
    "paragrafo": {"grupo": 7, "chunk_size": 1000, "chunk_overlap": 0},
    "sentenca_3": {"grupo": 8, "chunk_size": 3, "chunk_overlap": 0},
    "recursivo": {"grupo": 9, "chunk_size": 1000, "chunk_overlap": 0},
    "markdown_heading": {"grupo": 10, "chunk_size": None, "chunk_overlap": 0},
}

SCHEMA_METADATA = [
    ("fonte", "str", "Nome do arquivo .md de origem."),
    ("documento_id", "str", "Identificador estavel do documento."),
    ("chunk_index", "int", "Posicao do chunk dentro do documento."),
    ("estrategia", "str", "Estrategia da Aula 04 usada para gerar o chunk."),
    ("chunk_size", "int | None", "Configuracao de tamanho usada na estrategia."),
    ("chunk_overlap", "int", "Configuracao de sobreposicao usada na estrategia."),
    ("n_caracteres", "int", "Tamanho real do chunk em caracteres."),
    ("aula", "str | None", "Aula de origem do documento processado."),
    ("caminho_relativo", "str | None", "Caminho do arquivo dentro do repositorio, quando localizado."),
    ("fonte_online", "str | None", "Link online para a fonte original, quando disponivel."),
    ("pdf_link", "str | None", "Link local para o PDF original e pagina citavel, quando disponivel."),
    ("pagina_inicio", "int | None", "Primeira pagina de origem indicada nos metadados Docling."),
    ("pagina_fim", "int | None", "Ultima pagina de origem indicada nos metadados Docling."),
    ("secao", "str | None", "Secao Docling associada ao chunk, quando disponivel."),
    ("subsecao", "str | None", "Subsecao Docling associada ao chunk, quando disponivel."),
    ("heading_path", "list[str]", "Hierarquia de titulos Markdown associada ao chunk."),
    ("titulo_secao", "str | None", "Cabecalho Markdown mais proximo antes do chunk."),
    ("posicao_inicio", "int | None", "Indice inicial do chunk no texto completo do documento."),
    ("posicao_fim", "int | None", "Indice final do chunk no texto completo do documento."),
    ("chunk_id", "str | None", "Identificador unico do chunk no relatorio da Aula 04."),
    ("relatorio_origem", "str", "Relatorio JSON de onde o chunk foi carregado."),
    ("modelo_embedding", "str | None", "Modelo de embedding usado para gerar o relatorio."),
    ("score_similaridade", "float | None", "Score calculado na busca semantica da Aula 04."),
    ("query_origem", "str | None", "Pergunta usada para recuperar o chunk no relatorio da Aula 04."),
]


def slug_documento(nome_arquivo: str) -> str:
    return Path(nome_arquivo).stem.lower().replace("_", "-")


def extrair_titulo_secao(texto_ate_chunk: str) -> str | None:
    titulos = re.findall(r"(?m)^#{1,6}\s+(.+)$", texto_ate_chunk)
    if not titulos:
        return None
    return titulos[-1].strip()


def resolver_caminho_fonte(nome_arquivo: str) -> Path | None:
    caminho_informado = Path(nome_arquivo)
    candidatos = [
        caminho_informado,
        REPO_DIR / caminho_informado,
        DOCUMENTOS_DIR / caminho_informado.name,
        DOCUMENTOS_FALLBACK_DIR / caminho_informado.name,
    ]

    for caminho in candidatos:
        if caminho.exists():
            return caminho.resolve()

    for pasta in (DOCUMENTOS_DIR, DOCUMENTOS_FALLBACK_DIR):
        caminho = pasta / nome_arquivo
        if caminho.exists():
            return caminho.resolve()
    return None


def extrair_posicao_e_secao(
    caminho: Path | None,
    texto_chunk: str,
    textos_cache: Dict[Path, str] | None = None,
) -> Dict[str, Any]:
    if caminho is None:
        return {
            "titulo_secao": None,
            "posicao_inicio": None,
            "posicao_fim": None,
        }

    if textos_cache is None:
        texto_completo = caminho.read_text(encoding="utf-8")
    else:
        texto_completo = textos_cache.setdefault(caminho, caminho.read_text(encoding="utf-8"))
    posicao_inicio = texto_completo.find(texto_chunk)
    if posicao_inicio == -1:
        return {
            "titulo_secao": None,
            "posicao_inicio": None,
            "posicao_fim": None,
        }

    posicao_fim = posicao_inicio + len(texto_chunk)
    return {
        "titulo_secao": extrair_titulo_secao(texto_completo[:posicao_inicio]),
        "posicao_inicio": posicao_inicio,
        "posicao_fim": posicao_fim,
    }


def montar_chunk_real(
    nome_arquivo: str = "retrieval_augmented_generation.md",
    estrategia: str = "fixo_1000",
    chunk_index: int = 18,
) -> Document:
    caminho = DOCUMENTOS_DIR / nome_arquivo
    texto_completo = caminho.read_text(encoding="utf-8")
    config = ESTRATEGIAS_CONFIG[estrategia]
    chunk_size = config["chunk_size"]
    chunk_overlap = config["chunk_overlap"]

    if chunk_size is None:
        raise ValueError("Este exemplo usa uma estrategia com chunk_size numerico.")

    passo = chunk_size - chunk_overlap
    posicao_inicio = (chunk_index - 1) * passo
    posicao_fim = min(posicao_inicio + chunk_size, len(texto_completo))
    texto_chunk = texto_completo[posicao_inicio:posicao_fim]

    metadata = {
        "fonte": nome_arquivo,
        "documento_id": slug_documento(nome_arquivo),
        "chunk_index": chunk_index,
        "estrategia": estrategia,
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
        "n_caracteres": len(texto_chunk),
        "caminho_relativo": str(caminho.relative_to(REPO_DIR)).replace("\\", "/"),
        "fonte_online": None,
        "titulo_secao": extrair_titulo_secao(texto_completo[:posicao_inicio]),
        "posicao_inicio": posicao_inicio,
        "posicao_fim": posicao_fim,
    }

    return Document(page_content=texto_chunk, metadata=metadata)


def listar_relatorios(aula: str = AULA_RELATORIOS) -> List[Path]:
    return sorted(RELATORIOS_DIR.glob(f"completo_corpus_processed_{aula}_*.json"))


def carregar_chunks_do_relatorio(caminho_relatorio: Path) -> List[Dict[str, Any]]:
    relatorio = json.loads(caminho_relatorio.read_text(encoding="utf-8"))
    chunks = []

    if isinstance(relatorio, dict):
        estrategia = relatorio.get("estrategia") or relatorio.get("strategy_name")
        chunk_size = relatorio.get("chunk_size")
        chunk_overlap = relatorio.get("chunk_overlap")

        for item in relatorio["resultados_completos"]:
            chunks.append({
                "query_origem": item.get("query_origem"),
                "estrategia": item.get("strategy_name") or estrategia,
                "chunk_size": item.get("chunk_size", chunk_size),
                "chunk_overlap": item.get("chunk_overlap", chunk_overlap),
                "documento_id": item.get("document_id") or relatorio.get("document_id"),
                "document_name": item.get("document_name") or relatorio.get("document_name"),
                "modelo_embedding": relatorio.get("modelo_embedding"),
                "relatorio_origem": str(caminho_relatorio.relative_to(REPO_DIR)).replace("\\", "/"),
                **item,
            })

        return chunks

    for resultado_query in relatorio:
        estrategia = resultado_query["estrategia"]
        config = ESTRATEGIAS_CONFIG[estrategia]

        for item in resultado_query["resultados_completos"]:
            chunks.append({
                "query_origem": resultado_query["query"],
                "estrategia": estrategia,
                "chunk_size": config["chunk_size"],
                "chunk_overlap": config["chunk_overlap"],
                "relatorio_origem": str(caminho_relatorio.relative_to(REPO_DIR)).replace("\\", "/"),
                **item,
            })

    return chunks


def carregar_chunks_dos_relatorios(aula: str = AULA_RELATORIOS) -> List[Dict[str, Any]]:
    chunks = []

    for caminho_relatorio in listar_relatorios(aula):
        chunks.extend(carregar_chunks_do_relatorio(caminho_relatorio))

    return chunks


def extrair_aula(caminho_fonte: str) -> str | None:
    partes = Path(caminho_fonte).parts
    for parte in partes:
        if parte.startswith("aula"):
            return parte
    return None


def montar_documents_do_relatorio(aula: str = AULA_RELATORIOS) -> List[Document]:
    documentos = []
    textos_cache: Dict[Path, str] = {}

    for chunk in carregar_chunks_dos_relatorios(aula):
        caminho_fonte = chunk["arquivo"]
        fonte = Path(caminho_fonte).name
        caminho = resolver_caminho_fonte(caminho_fonte)
        texto_chunk = chunk.get("texto") or chunk["text"]
        metadata_docling = chunk.get("metadata") or {}
        contexto_fonte = extrair_posicao_e_secao(caminho, texto_chunk, textos_cache)

        metadata = {
            "fonte": fonte,
            "documento_id": chunk.get("documento_id") or slug_documento(fonte),
            "chunk_index": chunk["indice"],
            "estrategia": chunk["estrategia"],
            "chunk_size": chunk["chunk_size"],
            "chunk_overlap": chunk["chunk_overlap"],
            "n_caracteres": len(texto_chunk),
            "aula": extrair_aula(caminho_fonte),
            "caminho_relativo": (
                str(caminho.relative_to(REPO_DIR)).replace("\\", "/")
                if caminho is not None
                else None
            ),
            "fonte_online": None,
            "pdf_link": metadata_docling.get("pdf_link"),
            "pagina_inicio": metadata_docling.get("page_start") or metadata_docling.get("page"),
            "pagina_fim": metadata_docling.get("page_end") or metadata_docling.get("page"),
            "secao": metadata_docling.get("section"),
            "subsecao": metadata_docling.get("subsection"),
            "heading_path": metadata_docling.get("heading_path") or [],
            "titulo_secao": contexto_fonte["titulo_secao"],
            "posicao_inicio": contexto_fonte["posicao_inicio"],
            "posicao_fim": contexto_fonte["posicao_fim"],
            "chunk_id": chunk.get("chunk_id"),
            "relatorio_origem": chunk["relatorio_origem"],
            "modelo_embedding": chunk.get("modelo_embedding"),
            "score_similaridade": chunk.get("score_similaridade"),
            "query_origem": chunk.get("query_origem"),
        }
        documentos.append(Document(page_content=texto_chunk, metadata=metadata))

    return documentos


def imprimir_tabela_schema(schema: List[tuple[str, str, str]]) -> None:
    print("| Campo | Tipo | Descricao |")
    print("| --- | --- | --- |")
    for campo, tipo, descricao in schema:
        print(f"| `{campo}` | `{tipo}` | {descricao} |")


def imprimir_justificativas_campos_proprios() -> None:
    justificativas = {
        "aula": (
            "Permite filtrar resultados por etapa do curso, separando Aula 02 de Aula 04."
        ),
        "caminho_relativo": (
            "Permite responder em qual caminho do repositorio a fonte original pode ser auditada."
        ),
        "fonte_online": (
            "Permite responder qual link publico o usuario pode abrir para consultar a fonte original."
        ),
        "pdf_link": (
            "Permite responder exatamente qual PDF e pagina devem ser citados na resposta final."
        ),
        "pagina_inicio": (
            "Permite responder em qual pagina o trecho comeca no documento original."
        ),
        "pagina_fim": (
            "Permite responder se o chunk atravessa mais de uma pagina."
        ),
        "secao": (
            "Permite responder em qual secao do documento a informacao foi encontrada."
        ),
        "subsecao": (
            "Permite responder em qual recorte interno da secao a informacao apareceu."
        ),
        "heading_path": (
            "Permite reconstruir a hierarquia de titulos usada para contextualizar a citacao."
        ),
        "titulo_secao": (
            "Permite responder em qual secao conceitual o trecho apareceu, mesmo sem numero de pagina."
        ),
        "posicao_inicio": (
            "Permite recuperar contexto anterior ao chunk quando a resposta precisar citar ou explicar melhor."
        ),
        "posicao_fim": (
            "Permite recuperar contexto posterior ao chunk quando o trecho terminar cortado."
        ),
        "chunk_id": (
            "Permite rastrear o mesmo chunk dentro dos relatorios e em uma futura base vetorial."
        ),
        "relatorio_origem": (
            "Permite auditar qual experimento da Aula 04 gerou o chunk carregado."
        ),
        "modelo_embedding": (
            "Permite responder qual modelo vetorial produziu os embeddings daquele relatorio."
        ),
        "score_similaridade": (
            "Permite responder o quanto aquele chunk foi proximo da pergunta na busca semantica."
        ),
        "query_origem": (
            "Permite responder para qual pergunta aquele chunk foi recuperado no relatorio."
        ),
    }

    for campo, justificativa in justificativas.items():
        print(f"- `{campo}`: {justificativa}")


def document_para_json(documento: Document) -> Dict[str, Any]:
    return {
        "page_content": documento.page_content,
        "metadata": documento.metadata,
    }


def caminho_saida_documents(aula: str) -> Path:
    return SAIDA_DOCUMENTS_DIR / f"documents_langchain_{aula}.json"


def salvar_documents(aula: str, documentos: List[Document]) -> Path:
    SAIDA_DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
    caminho_saida = caminho_saida_documents(aula)
    payload = {
        "aula": aula,
        "total_documents": len(documentos),
        "documents": [document_para_json(documento) for documento in documentos],
    }
    caminho_saida.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return caminho_saida


def executar_exercicio(aula: str = AULA_RELATORIOS) -> None:
    relatorios = listar_relatorios(aula)
    documentos = montar_documents_do_relatorio(aula)
    caminho_saida = salvar_documents(aula, documentos)

    print("=== 1. Schema final ===")
    imprimir_tabela_schema(SCHEMA_METADATA)
    print()

    print("=== 2. Justificativa dos campos proprios ===")
    imprimir_justificativas_campos_proprios()
    print()

    print("=== 3. Exemplos preenchidos em JSON com chunks reais ===")
    print(f"aula: {aula}")
    print(f"relatorios_carregados: {len(relatorios)}")
    print(f"documents_carregados: {len(documentos)}")
    print(f"arquivo_saida: {caminho_saida.relative_to(REPO_DIR)}")
    print(json.dumps(
        [document_para_json(documento) for documento in documentos[:NUMERO_EXEMPLOS_JSON]],
        ensure_ascii=False,
        indent=2,
    ))
    print()

    print("=== Respostas ===")
    print(
        "- Para citar a fonte na resposta final do RAG, eu incluiria "
        "`pdf_link`, junto de `fonte`, `pagina_inicio`, `pagina_fim`, "
        "`secao`, `heading_path` e `chunk_index`. Assim a resposta pode apontar "
        "para o PDF, a pagina e o trecho recuperado."
    )
    print(
        "- `chunk_index` e util porque permite buscar os chunks vizinhos quando "
        "o trecho recuperado esta cortado no meio de uma explicacao. Por exemplo, "
        "se o chunk 18 foi recuperado, posso consultar os chunks 17 e 19 do mesmo "
        "documento e da mesma estrategia para reconstruir o contexto."
    )


if __name__ == "__main__":
    executar_exercicio()
