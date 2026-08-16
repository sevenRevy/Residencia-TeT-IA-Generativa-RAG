import hashlib
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from langchain_text_splitters import (
    CharacterTextSplitter,
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)
from openai import OpenAI


load_dotenv()

client = OpenAI(
    base_url=os.getenv("LOCAL_OPENAI_BASE_URL", "http://localhost:5001/v1/"),
    api_key=os.getenv("LOCAL_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") or "local",
)

REPO_DIR = Path(__file__).resolve().parents[1]
RELATORIOS_DOCUMENTOS_DIR = REPO_DIR / "corpus" / "reports"
EMBEDDINGS_CACHE_DIR = REPO_DIR / "corpus" / "embeddings" / "cache"
PASTAS_MARKDOWN_IGNORADAS = {
    "archive",
}
COMENTARIO_METADATA_RE = re.compile(
    r"<!--\s*(page_metadata|section_metadata|image_metadata):\s*(\{.*?\})\s*-->",
    flags=re.DOTALL,
)

ESTRATEGIAS = {
    1: {
        "nome": "fixo_200",
        "strategy": "fixed",
        "chunk_size": 200,
        "chunk_overlap": 0,
        "descricao": "200 caracteres, sem overlap",
    },
    2: {
        "nome": "fixo_500",
        "strategy": "fixed",
        "chunk_size": 500,
        "chunk_overlap": 0,
        "descricao": "500 caracteres, sem overlap",
    },
    3: {
        "nome": "fixo_1000",
        "strategy": "fixed",
        "chunk_size": 1000,
        "chunk_overlap": 0,
        "descricao": "1000 caracteres, sem overlap",
    },
    4: {
        "nome": "fixo_2000",
        "strategy": "fixed",
        "chunk_size": 2000,
        "chunk_overlap": 0,
        "descricao": "2000 caracteres, sem overlap",
    },
    5: {
        "nome": "fixo_500_overlap_50",
        "strategy": "fixed_with_overlap",
        "chunk_size": 500,
        "chunk_overlap": 50,
        "descricao": "500 caracteres, overlap 50",
    },
    6: {
        "nome": "fixo_500_overlap_200",
        "strategy": "fixed_with_overlap",
        "chunk_size": 500,
        "chunk_overlap": 200,
        "descricao": "500 caracteres, overlap 200",
    },
    7: {
        "nome": "paragrafo",
        "strategy": "paragraph",
        "chunk_size": 1000,
        "chunk_overlap": 0,
        "descricao": "separação por parágrafos",
    },
    8: {
        "nome": "sentenca_3",
        "strategy": "sentence_group",
        "chunk_size": None,
        "chunk_overlap": 0,
        "descricao": "sentenças agrupadas em 3",
    },
    9: {
        "nome": "recursivo",
        "strategy": "recursive",
        "chunk_size": 1000,
        "chunk_overlap": 0,
        "descricao": "separadores hierárquicos",
    },
    10: {
        "nome": "markdown_heading",
        "strategy": "markdown",
        "chunk_size": None,
        "chunk_overlap": 0,
        "descricao": "separação por headings/seções",
    },
}

def escolher_modelo_embedding() -> str:
    modelo_env = os.getenv("LOCAL_EMBEDDING_MODEL")
    if modelo_env and modelo_env.lower() != "inactive":
        return modelo_env

    modelos = client.models.list()
    ids_modelos = [modelo.id for modelo in modelos.data if getattr(modelo, "id", None)]
    for modelo_id in ids_modelos:
        modelo_lower = modelo_id.lower()
        if "qwen" in modelo_lower and "embed" in modelo_lower:
            return modelo_id

    raise RuntimeError("Nenhum modelo local de embedding Qwen foi encontrado.")


embedding_model = escolher_modelo_embedding()
embedding_cache: Dict[str, Dict[str, Any]] = {}


def slug_modelo(modelo: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", modelo).strip("_")


def caminho_cache_embeddings() -> Path:
    return EMBEDDINGS_CACHE_DIR / f"{slug_modelo(embedding_model)}.json"


def chave_texto_embedding(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def carregar_cache_embeddings() -> None:
    global embedding_cache

    arquivo_cache = caminho_cache_embeddings()
    if not arquivo_cache.exists():
        embedding_cache = {}
        return

    try:
        with arquivo_cache.open("r", encoding="utf-8") as f:
            dados = json.load(f)
    except json.JSONDecodeError:
        arquivo_corrompido = arquivo_cache.with_suffix(".corrompido.json")
        arquivo_cache.replace(arquivo_corrompido)
        print(f"Cache de embeddings corrompido movido para: {arquivo_corrompido}")
        embedding_cache = {}
        return

    embedding_cache = dados.get("items", {})


def salvar_cache_embeddings() -> None:
    EMBEDDINGS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    arquivo_cache = caminho_cache_embeddings()
    arquivo_tmp = arquivo_cache.with_name(f"{arquivo_cache.stem}.{os.getpid()}.{time.time_ns()}.tmp")

    with arquivo_tmp.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "modelo": embedding_model,
                "items": embedding_cache,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    for tentativa in range(5):
        try:
            arquivo_tmp.replace(arquivo_cache)
            return
        except PermissionError:
            if tentativa == 4:
                raise
            time.sleep(0.5)


def caminho_deve_ser_ignorado(caminho: Path) -> bool:
    partes = set(caminho.relative_to(REPO_DIR).parts)
    return bool(partes & PASTAS_MARKDOWN_IGNORADAS)


def slug_documento(caminho_relativo: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", caminho_relativo).strip("_")


def document_id(caminho_relativo: str) -> str:
    return slug_documento(Path(caminho_relativo).with_suffix("").as_posix())


def detectar_headers_markdown(texto: str) -> List[tuple[str, str]]:
    niveis = sorted({
        len(match.group(1))
        for match in re.finditer(r"^(#{1,6})\s+", texto, flags=re.MULTILINE)
    })

    if not niveis:
        niveis = [1, 2, 3]

    return [("#" * nivel, f"h{nivel}") for nivel in niveis]


def limpar_comentarios_metadata(texto: str) -> tuple[str, List[int]]:
    partes = []
    mapa_posicoes = []
    posicao_atual = 0

    for match in COMENTARIO_METADATA_RE.finditer(texto):
        trecho = texto[posicao_atual:match.start()]
        partes.append(trecho)
        mapa_posicoes.extend(range(posicao_atual, match.start()))
        posicao_atual = match.end()

    trecho_final = texto[posicao_atual:]
    partes.append(trecho_final)
    mapa_posicoes.extend(range(posicao_atual, len(texto)))

    return "".join(partes), mapa_posicoes


def posicao_original(mapa_posicoes: List[int], posicao_limpa: int) -> int:
    if posicao_limpa < 0 or posicao_limpa >= len(mapa_posicoes):
        return -1

    return mapa_posicoes[posicao_limpa]


def extrair_metadados_documento(texto: str) -> Dict[str, List[Dict[str, Any]]]:
    """Extrai os metadados gerados pelo Docling nos comentários do markdown."""
    metadados = []
    imagens = []

    for match in COMENTARIO_METADATA_RE.finditer(texto):
        try:
            dados = json.loads(match.group(2))
        except json.JSONDecodeError:
            continue

        dados["_posicao"] = match.start()
        dados["_tipo"] = match.group(1)
        if dados["_tipo"] == "image_metadata":
            imagens.append(dados)
        else:
            metadados.append(dados)

    return {
        "metadados": metadados,
        "imagens": imagens,
    }


def limpar_metadados_internos(dados: Dict[str, Any]) -> Dict[str, Any]:
    return {
        chave: valor
        for chave, valor in dados.items()
        if not chave.startswith("_")
    }


def metadados_para_posicao(metadados: List[Dict[str, Any]], posicao: int) -> Dict[str, Any]:
    if not metadados or posicao < 0:
        return {}

    metadado_atual = {}
    for metadado in metadados:
        if metadado["_posicao"] > posicao:
            break
        metadado_atual.update(limpar_metadados_internos(metadado))

    return metadado_atual


def imagens_para_intervalo(imagens: List[Dict[str, Any]], inicio: int, fim: int) -> List[Dict[str, Any]]:
    if not imagens or inicio < 0 or fim < inicio:
        return []

    return [
        limpar_metadados_internos(imagem)
        for imagem in imagens
        if inicio <= imagem["_posicao"] <= fim
    ]


def localizar_trecho(texto: str, trecho: str, posicao_inicio: int = 0) -> int:
    posicao = texto.find(trecho, posicao_inicio)
    if posicao != -1:
        return posicao

    return texto.find(trecho)


def ler_documentos_markdown(diretorio: Path = REPO_DIR / "corpus") -> List[Dict[str, str]]:
    """Lê todos os arquivos .md do corpus, ignorando arquivos arquivados."""
    documentos = []
    arquivos = [
        caminho
        for caminho in diretorio.rglob("*.md")
        if caminho.is_file() and not caminho_deve_ser_ignorado(caminho)
    ]

    for caminho in sorted(arquivos):
        with open(caminho, "r", encoding="utf-8") as f:
            texto_original = f.read()
            texto_limpo, mapa_posicoes = limpar_comentarios_metadata(texto_original)
            metadados_documento = extrair_metadados_documento(texto_original)
            caminho_relativo = caminho.relative_to(REPO_DIR).as_posix()
            documentos.append({
                "arquivo": caminho_relativo,
                "texto": texto_limpo,
                "texto_original": texto_original,
                "mapa_posicoes": mapa_posicoes,
                "metadados": metadados_documento["metadados"],
                "imagens": metadados_documento["imagens"],
            })
    return documentos


def criar_splitter(grupo: int):
    """Fábrica de TextSplitters para os grupos padrão (1 a 7 e 9)."""
    config = ESTRATEGIAS[grupo]

    if grupo == 1:
        return CharacterTextSplitter(separator="", chunk_size=config["chunk_size"], chunk_overlap=config["chunk_overlap"])
    elif grupo == 2:
        return CharacterTextSplitter(separator="", chunk_size=config["chunk_size"], chunk_overlap=config["chunk_overlap"])
    elif grupo == 3:
        return CharacterTextSplitter(separator="", chunk_size=config["chunk_size"], chunk_overlap=config["chunk_overlap"])
    elif grupo == 4:
        return CharacterTextSplitter(separator="", chunk_size=config["chunk_size"], chunk_overlap=config["chunk_overlap"])
    elif grupo == 5:
        return CharacterTextSplitter(separator="", chunk_size=config["chunk_size"], chunk_overlap=config["chunk_overlap"])
    elif grupo == 6:
        return CharacterTextSplitter(separator="", chunk_size=config["chunk_size"], chunk_overlap=config["chunk_overlap"])
    elif grupo == 7:
        return CharacterTextSplitter(separator="\n\n", chunk_size=config["chunk_size"], chunk_overlap=config["chunk_overlap"])
    elif grupo == 9:
        return RecursiveCharacterTextSplitter(
            chunk_size=config["chunk_size"],
            chunk_overlap=config["chunk_overlap"],
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    raise ValueError(f"Grupo inválido para a fábrica criar_splitter: {grupo}")


def montar_trechos(documentos: List[Dict[str, str]], grupo: int) -> List[Dict[str, Any]]:
    """Gera chunks usando os splitters baseados no LangChain (Grupos 1-7 e 9)."""
    splitter = criar_splitter(grupo)
    trechos = []

    for documento in documentos:
        partes = splitter.split_text(documento["texto"])
        posicao_busca = 0
        for indice, parte in enumerate(partes, start=1):
            posicao = localizar_trecho(documento["texto"], parte, posicao_busca)
            if posicao != -1:
                posicao_busca = posicao + max(1, len(parte) - ESTRATEGIAS[grupo]["chunk_overlap"])

            inicio_original = posicao_original(documento.get("mapa_posicoes", []), posicao)
            fim_original = posicao_original(documento.get("mapa_posicoes", []), posicao + len(parte) - 1)
            metadata = metadados_para_posicao(documento.get("metadados", []), inicio_original)
            imagens = imagens_para_intervalo(documento.get("imagens", []), inicio_original, fim_original)
            if imagens:
                metadata["images"] = imagens

            trechos.append({
                "arquivo": documento["arquivo"],
                "indice": indice,
                "grupo": grupo,
                "tamanho": len(parte),
                "texto": parte,
                "metadata": metadata,
            })
    return trechos


def montar_trechos_sentencas(documentos: List[Dict[str, str]], tamanho_grupo: int = 3) -> List[Dict[str, Any]]:
    """Grupo 8: Quebra o texto em sentenças e junta em blocos de N sentenças."""
    trechos = []

    for documento in documentos:
        sentencas = [s.strip() for s in re.split(r'(?<=[.!?])\s+', documento["texto"]) if s.strip()]

        chunk_indice = 1
        posicao_busca = 0
        for i in range(0, len(sentencas), tamanho_grupo):
            bloco = " ".join(sentencas[i : i + tamanho_grupo])
            posicao = localizar_trecho(documento["texto"], bloco, posicao_busca)
            if posicao != -1:
                posicao_busca = posicao + len(bloco)

            inicio_original = posicao_original(documento.get("mapa_posicoes", []), posicao)
            fim_original = posicao_original(documento.get("mapa_posicoes", []), posicao + len(bloco) - 1)
            metadata = metadados_para_posicao(documento.get("metadados", []), inicio_original)
            imagens = imagens_para_intervalo(documento.get("imagens", []), inicio_original, fim_original)
            if imagens:
                metadata["images"] = imagens

            trechos.append({
                "arquivo": documento["arquivo"],
                "indice": chunk_indice,
                "grupo": 8,
                "tamanho": len(bloco),
                "texto": bloco,
                "metadata": metadata,
            })
            chunk_indice += 1

    return trechos


def montar_trechos_markdown(documentos: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """Grupo 10: Usa MarkdownHeaderTextSplitter preservando os níveis de cabeçalho encontrados."""
    trechos = []

    for documento in documentos:
        headers_to_split_on = detectar_headers_markdown(documento["texto"])
        splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
        partes = splitter.split_text(documento["texto"])
        posicao_busca = 0
        for indice, parte in enumerate(partes, start=1):
            posicao = localizar_trecho(documento["texto"], parte.page_content, posicao_busca)
            if posicao != -1:
                posicao_busca = posicao + len(parte.page_content)

            inicio_original = posicao_original(documento.get("mapa_posicoes", []), posicao)
            fim_original = posicao_original(documento.get("mapa_posicoes", []), posicao + len(parte.page_content) - 1)
            metadata = metadados_para_posicao(documento.get("metadados", []), inicio_original)
            metadata.update(parte.metadata)
            imagens = imagens_para_intervalo(documento.get("imagens", []), inicio_original, fim_original)
            if imagens:
                metadata["images"] = imagens
            trechos.append({
                "arquivo": documento["arquivo"],
                "indice": indice,
                "grupo": 10,
                "tamanho": len(parte.page_content),
                "texto": parte.page_content,
                "metadata": metadata,
            })
    return trechos


def gerar_embeddings_em_lote(textos: List[str], lote_tamanho: int = 64) -> Dict[str, List[float]]:
    """Gera embeddings em lote utilizando a API local compatível com OpenAI."""
    embeddings = {}
    textos_unicos = list(dict.fromkeys(texto.strip() for texto in textos if texto and texto.strip()))
    textos_pendentes = []

    for texto in textos_unicos:
        chave = chave_texto_embedding(texto)
        item_cache = embedding_cache.get(chave)
        if item_cache:
            embeddings[texto] = item_cache["embedding"]
        else:
            textos_pendentes.append(texto)

    for inicio in range(0, len(textos_pendentes), lote_tamanho):
        lote = textos_pendentes[inicio : inicio + lote_tamanho]
        response = client.embeddings.create(
            model=embedding_model,
            input=lote,
            encoding_format="float",
        )

        for texto, item in zip(lote, response.data):
            embeddings[texto] = item.embedding
            embedding_cache[chave_texto_embedding(texto)] = {
                "texto": texto,
                "embedding": item.embedding,
            }

        salvar_cache_embeddings()

    return embeddings


def montar_resultados_embeddings(
    test_id: int,
    config: Dict[str, Any],
    trechos: List[Dict[str, Any]],
    embeddings: Dict[str, List[float]]
) -> List[Dict[str, Any]]:
    resultados = []

    for trecho in trechos:
        texto_key = trecho["texto"].strip()
        if not texto_key:
            continue

        doc_id = document_id(trecho["arquivo"])
        indice = trecho["indice"]
        metadata = {
            "source_path": trecho["arquivo"],
            "page": None,
            "section": None,
        }
        if "metadata" in trecho and trecho["metadata"]:
            metadata.update(trecho["metadata"])
            if not metadata.get("section"):
                headers = [
                    valor
                    for chave, valor in trecho["metadata"].items()
                    if re.fullmatch(r"h[1-6]", chave) and valor
                ]
                metadata["section"] = " > ".join(headers) if headers else None

        document_name = metadata.get("document_name") or Path(trecho["arquivo"]).name

        item_resultado = {
            "chunk_id": f"{doc_id}_test{test_id:02d}_chunk{indice:03d}",
            "document_id": doc_id,
            "document_name": document_name,
            "test_id": test_id,
            "strategy": config["strategy"],
            "strategy_name": config["nome"],
            "chunk_size": config["chunk_size"],
            "chunk_overlap": config["chunk_overlap"],
            "arquivo": trecho["arquivo"],
            "indice": indice,
            "tamanho": trecho["tamanho"],
            "estimated_tokens": len(trecho["texto"].split()),
            "texto": trecho["texto"],
            "text": trecho["texto"],
            "embedding": embeddings[texto_key],
            "metadata": metadata,
        }

        resultados.append(item_resultado)

    return resultados


def calcular_estatisticas_chunks(resultados: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
    tamanhos = [item["tamanho"] for item in resultados]
    tokens_estimados = [item["estimated_tokens"] for item in resultados]
    embedding_dimension = len(resultados[0]["embedding"]) if resultados else 0
    chunk_overlap = config["chunk_overlap"] or 0

    return {
        "num_chunks": len(resultados),
        "avg_chunk_size": round(sum(tamanhos) / len(tamanhos), 2) if tamanhos else 0,
        "min_chunk_size": min(tamanhos) if tamanhos else 0,
        "max_chunk_size": max(tamanhos) if tamanhos else 0,
        "avg_estimated_tokens": round(sum(tokens_estimados) / len(tokens_estimados), 2) if tokens_estimados else 0,
        "min_estimated_tokens": min(tokens_estimados) if tokens_estimados else 0,
        "max_estimated_tokens": max(tokens_estimados) if tokens_estimados else 0,
        "overlap_chunks": max(len(resultados) - 1, 0) if chunk_overlap > 0 else 0,
        "overlap_percent": round((chunk_overlap / config["chunk_size"]) * 100, 2) if config["chunk_size"] else 0,
        "embedding_dimension": embedding_dimension,
    }


def salvar_summary(summary: List[Dict[str, Any]]) -> None:
    RELATORIOS_DOCUMENTOS_DIR.mkdir(parents=True, exist_ok=True)
    arquivo_saida = RELATORIOS_DOCUMENTOS_DIR / "summary.json"

    with open(arquivo_saida, "w", encoding="utf-8") as f:
        json.dump(
            {
                "modelo_embedding": embedding_model,
                "total_documentos": len({item["document_id"] for item in summary}),
                "total_experimentos": len(summary),
                "experiments": summary,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )


def caminho_relatorio_documento(nome_estrategia: str, arquivo: str) -> Path:
    return RELATORIOS_DOCUMENTOS_DIR / f"completo_{slug_documento(arquivo)}_{nome_estrategia}.json"


def montar_item_summary(relatorio_documento: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "document_id": relatorio_documento["document_id"],
        "document_name": relatorio_documento["document_name"],
        "arquivo": relatorio_documento["arquivo"],
        "test_id": relatorio_documento["test_id"],
        "strategy": relatorio_documento["strategy"],
        "strategy_name": relatorio_documento["estrategia"],
        "chunk_size": relatorio_documento["chunk_size"],
        "chunk_overlap": relatorio_documento["chunk_overlap"],
        **relatorio_documento["estatisticas"],
    }


def carregar_summary_existente() -> List[Dict[str, Any]]:
    arquivo_summary = RELATORIOS_DOCUMENTOS_DIR / "summary.json"
    if not arquivo_summary.exists():
        return []

    with arquivo_summary.open("r", encoding="utf-8") as f:
        dados = json.load(f)

    return dados.get("experiments", [])


def carregar_relatorio_concluido(nome_estrategia: str, arquivo: str) -> Dict[str, Any] | None:
    caminho = caminho_relatorio_documento(nome_estrategia, arquivo)
    if not caminho.exists():
        return None

    with caminho.open("r", encoding="utf-8") as f:
        relatorio = json.load(f)

    if "estatisticas" not in relatorio or "resultados_completos" not in relatorio:
        return None

    resultados = relatorio.get("resultados_completos") or []
    if resultados and "embedding" not in resultados[0]:
        return None

    return relatorio


def gerar_relatorio_embeddings() -> None:
    """Gera embeddings para todos os documentos do corpus usando as 10 estratégias de chunking."""
    documentos = ler_documentos_markdown()
    summary = carregar_summary_existente()
    summary_keys = {
        (item["arquivo"], item["test_id"])
        for item in summary
    }

    for grupo in range(1, 11):
        config = ESTRATEGIAS[grupo]
        nome_estrategia = config["nome"]

        for documento in documentos:
            relatorio_existente = carregar_relatorio_concluido(nome_estrategia, documento["arquivo"])
            if relatorio_existente:
                summary_key = (documento["arquivo"], grupo)
                if summary_key not in summary_keys:
                    summary.append(montar_item_summary(relatorio_existente))
                    summary_keys.add(summary_key)
                    salvar_summary(summary)
                print(f"Já processado: {documento['arquivo']} ({nome_estrategia})")
                continue

            documento_unico = [documento]

            if grupo == 8:
                trechos = montar_trechos_sentencas(documento_unico, tamanho_grupo=3)
            elif grupo == 10:
                trechos = montar_trechos_markdown(documento_unico)
            else:
                trechos = montar_trechos(documento_unico, grupo)

            if not trechos:
                continue

            textos_para_embedding = [trecho["texto"] for trecho in trechos]
            embeddings = gerar_embeddings_em_lote(textos_para_embedding)
            resultados_embeddings = montar_resultados_embeddings(grupo, config, trechos, embeddings)
            estatisticas = calcular_estatisticas_chunks(resultados_embeddings, config)
            relatorio_documento = {
                "test_id": grupo,
                "estrategia": nome_estrategia,
                "strategy": config["strategy"],
                "chunk_size": config["chunk_size"],
                "chunk_overlap": config["chunk_overlap"],
                "modelo_embedding": embedding_model,
                "document_id": document_id(documento["arquivo"]),
                "document_name": resultados_embeddings[0]["document_name"],
                "arquivo": documento["arquivo"],
                "total_chunks": len(resultados_embeddings),
                "estatisticas": estatisticas,
                "resultados_completos": resultados_embeddings,
            }

            salvar_relatorio_documento(nome_estrategia, documento["arquivo"], relatorio_documento)
            summary_key = (documento["arquivo"], grupo)
            summary = [item for item in summary if (item["arquivo"], item["test_id"]) != summary_key]
            summary.append(montar_item_summary(relatorio_documento))
            summary_keys.add(summary_key)
            salvar_summary(summary)
            print(f"Documento processado: {documento['arquivo']} ({nome_estrategia})")


def salvar_relatorio_documento(nome_estrategia: str, arquivo: str, relatorio: Dict[str, Any]) -> None:
    RELATORIOS_DOCUMENTOS_DIR.mkdir(parents=True, exist_ok=True)

    arquivo_saida = caminho_relatorio_documento(nome_estrategia, arquivo)
    with open(arquivo_saida, "w", encoding="utf-8") as f:
        json.dump(relatorio, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    carregar_cache_embeddings()
    print(f"Gerando embeddings locais com {embedding_model} para os documentos do corpus...")
    gerar_relatorio_embeddings()
