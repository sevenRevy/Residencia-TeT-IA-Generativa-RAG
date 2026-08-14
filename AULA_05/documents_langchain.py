import json
import re
from pathlib import Path
from typing import Any, Dict, List

from langchain_core.documents import Document


REPO_DIR = Path(__file__).resolve().parents[1]
CORPUS_DIR = REPO_DIR / "corpus"
DOCUMENTOS_DIR = CORPUS_DIR / "processed" / "aula04"
DOCUMENTOS_FALLBACK_DIR = CORPUS_DIR / "processed" / "aula02"
RELATORIOS_DIR = CORPUS_DIR / "reports" / "aula04"
RELATORIO_ENTRADA = RELATORIOS_DIR / "completo_fixo_1000.json"
NUMERO_EMBEDDINGS = 5

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
    ("caminho_relativo", "str | None", "Caminho do arquivo dentro do repositorio, quando localizado."),
    ("fonte_online", "str | None", "Link online para a fonte original, quando disponivel."),
    ("titulo_secao", "str | None", "Cabecalho Markdown mais proximo antes do chunk."),
    ("posicao_inicio", "int | None", "Indice inicial do chunk no texto completo do documento."),
    ("posicao_fim", "int | None", "Indice final do chunk no texto completo do documento."),
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
    for pasta in (DOCUMENTOS_DIR, DOCUMENTOS_FALLBACK_DIR):
        caminho = pasta / nome_arquivo
        if caminho.exists():
            return caminho
    return None


def extrair_posicao_e_secao(caminho: Path | None, texto_chunk: str) -> Dict[str, Any]:
    if caminho is None:
        return {
            "titulo_secao": None,
            "posicao_inicio": None,
            "posicao_fim": None,
        }

    texto_completo = caminho.read_text(encoding="utf-8")
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


def carregar_chunks_do_relatorio(limite: int = NUMERO_EMBEDDINGS) -> List[Dict[str, Any]]:
    relatorio = json.loads(RELATORIO_ENTRADA.read_text(encoding="utf-8"))
    chunks = []

    for resultado_query in relatorio:
        estrategia = resultado_query["estrategia"]
        config = ESTRATEGIAS_CONFIG[estrategia]

        for item in resultado_query["resultados_completos"]:
            chunks.append({
                "query_origem": resultado_query["query"],
                "estrategia": estrategia,
                "chunk_size": config["chunk_size"],
                "chunk_overlap": config["chunk_overlap"],
                **item,
            })

            if len(chunks) >= limite:
                return chunks

    return chunks


def montar_documents_do_relatorio(limite: int = NUMERO_EMBEDDINGS) -> List[Document]:
    documentos = []

    for chunk in carregar_chunks_do_relatorio(limite):
        fonte = chunk["arquivo"]
        caminho = resolver_caminho_fonte(fonte)
        texto_chunk = chunk["texto"]
        contexto_fonte = extrair_posicao_e_secao(caminho, texto_chunk)

        metadata = {
            "fonte": fonte,
            "documento_id": slug_documento(fonte),
            "chunk_index": chunk["indice"],
            "estrategia": chunk["estrategia"],
            "chunk_size": chunk["chunk_size"],
            "chunk_overlap": chunk["chunk_overlap"],
            "n_caracteres": len(texto_chunk),
            "caminho_relativo": (
                str(caminho.relative_to(REPO_DIR)).replace("\\", "/")
                if caminho is not None
                else None
            ),
            "fonte_online": None,
            "titulo_secao": contexto_fonte["titulo_secao"],
            "posicao_inicio": contexto_fonte["posicao_inicio"],
            "posicao_fim": contexto_fonte["posicao_fim"],
            "score_similaridade": chunk.get("score_similaridade"),
            "query_origem": chunk["query_origem"],
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
        "caminho_relativo": (
            "Permite responder em qual caminho do repositorio a fonte original pode ser auditada."
        ),
        "fonte_online": (
            "Permite responder qual link publico o usuario pode abrir para consultar a fonte original."
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


if __name__ == "__main__":
    documentos = montar_documents_do_relatorio()

    print("=== 1. Schema final ===")
    imprimir_tabela_schema(SCHEMA_METADATA)
    print()

    print("=== 2. Justificativa dos campos proprios ===")
    imprimir_justificativas_campos_proprios()
    print()

    print("=== 3. Exemplos preenchidos em JSON com chunks reais ===")
    print(f"relatorio_entrada: {RELATORIO_ENTRADA.relative_to(REPO_DIR)}")
    print(f"numero_embeddings: {NUMERO_EMBEDDINGS}")
    print(f"documents_carregados: {len(documentos)}")
    print(json.dumps(
        [document_para_json(documento) for documento in documentos],
        ensure_ascii=False,
        indent=2,
    ))
    print()

    print("=== Respostas ===")
    print(
        "- Para citar a fonte na resposta final do RAG, eu incluiria "
        "`fonte_online` quando existir, junto de `fonte`, `caminho_relativo`, "
        "`titulo_secao`, `chunk_index`, `posicao_inicio` e `posicao_fim`. "
        "Neste exemplo, `fonte_online` fica `None` porque o link nao vem dos "
        "dados locais; ainda assim da para citar o arquivo, a secao e o intervalo "
        "do texto original."
    )
    print(
        "- `chunk_index` e util porque permite buscar os chunks vizinhos quando "
        "o trecho recuperado esta cortado no meio de uma explicacao. Por exemplo, "
        "se o chunk 18 foi recuperado, posso consultar os chunks 17 e 19 do mesmo "
        "documento e da mesma estrategia para reconstruir o contexto."
    )
