from pathlib import Path

from langchain_core.documents import Document


REPO_DIR = Path(__file__).resolve().parents[1]
CORPUS_DIR = REPO_DIR / "corpus" / "processed" / "aula04"


documentos = [
    Document(
        page_content="Embeddings sao representacoes vetoriais densas de texto.",
        metadata={
            "fonte": "gpt3_language_models.md",
            "pagina": 1,
            "tipo": "teoria",
            "tema": "embeddings",
            "autor": "Tom B. Brown et al.",
        },
    ),
    Document(
        page_content="Chunking divide textos longos em partes menores para recuperacao.",
        metadata={
            "fonte": "retrieval_augmented_generation.md",
            "pagina": 2,
            "tipo": "pratica",
            "tema": "chunking",
            "autor": "Patrick Lewis et al.",
        },
    ),
    Document(
        page_content="RAG combina recuperacao de contexto com geracao de respostas.",
        metadata={
            "fonte": "retrieval_augmented_generation.md",
            "pagina": 3,
            "tipo": "teoria",
            "tema": "RAG",
            "autor": "Patrick Lewis et al.",
        },
    ),
    Document(
        page_content="Tokenizacao transforma texto em unidades processadas pelo modelo.",
        metadata={
            "fonte": "bert_pretraining.md",
            "pagina": 4,
            "tipo": "teoria",
            "tema": "tokenizacao",
            "autor": "Jacob Devlin et al.",
        },
    ),
    Document(
        page_content="A busca vetorial compara a consulta com documentos usando similaridade.",
        metadata={
            "fonte": "attention_is_all_you_need.md",
            "pagina": 5,
            "tipo": "pratica",
            "tema": "busca vetorial",
            "autor": "Ashish Vaswani et al.",
        },
    ),
]


def imprimir_documentos(lista_documentos):
    for indice, documento in enumerate(lista_documentos, start=1):
        print(f"Documento {indice}")
        print(f"page_content: {documento.page_content}")
        print(f"metadata: {documento.metadata}")
        print()


def testar_metadata_com_lista():
    return Document(
        page_content="Metadados tambem podem guardar tags em lista.",
        metadata={
            "fonte": "teste_lista.md",
            "pagina": 6,
            "tema": "metadata",
            "tags": ["langchain", "document", "lista"],
            "observacao": "campo sintetico usado para testar listas",
        },
    )


def testar_metadata_com_dicionario_aninhado():
    return Document(
        page_content="Metadados podem conter estruturas aninhadas em memoria.",
        metadata={
            "fonte": "teste_aninhado.md",
            "pagina": 7,
            "tema": "metadata",
            "detalhes": {
                "curso": "RAG",
                "estrategia": "teste manual",
                "campos_testados": ["dict", "str", "int", "list"],
            },
        },
    )


def testar_document_sem_metadata():
    return Document(page_content="Documento criado sem informar metadata.")


if __name__ == "__main__":
    arquivos_corpus = sorted(caminho.name for caminho in CORPUS_DIR.glob("*.md"))

    print("=== Markdown processado da Aula 04 ===")
    print(f"pasta: {CORPUS_DIR}")
    print(f"total_arquivos_md: {len(arquivos_corpus)}")
    for arquivo in arquivos_corpus:
        print(f"- {arquivo}")
    print()

    print("=== Lista completa de Document ===")
    imprimir_documentos(documentos)
    print(f"len(documentos): {len(documentos)}")
    print()

    print("=== Teste de metadata com lista ===")
    documento_com_lista = testar_metadata_com_lista()
    print(f"page_content: {documento_com_lista.page_content}")
    print(f"metadata: {documento_com_lista.metadata}")
    print(f"tipo de metadata['tags']: {type(documento_com_lista.metadata['tags']).__name__}")
    print()

    print("=== Teste de metadata com dicionario aninhado ===")
    documento_com_dicionario = testar_metadata_com_dicionario_aninhado()
    print(f"page_content: {documento_com_dicionario.page_content}")
    print(f"metadata: {documento_com_dicionario.metadata}")
    print(
        "tipo de metadata['detalhes']: "
        f"{type(documento_com_dicionario.metadata['detalhes']).__name__}"
    )
    print()

    print("=== Teste de Document sem metadata ===")
    documento_sem_metadata = testar_document_sem_metadata()
    print(f"page_content: {documento_sem_metadata.page_content}")
    print(f"metadata: {documento_sem_metadata.metadata}")
    print(f"tipo de metadata: {type(documento_sem_metadata.metadata).__name__}")
