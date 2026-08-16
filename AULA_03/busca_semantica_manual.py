import glob
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

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
DOCUMENTOS_DIR = REPO_DIR / "corpus" / "processed" / "aula02"
EMBEDDINGS_DIR = REPO_DIR / "corpus" / "embeddings" / "aula03"

ESTRATEGIAS = {
    1: "fixo_200",
    2: "fixo_500",
    3: "fixo_1000",
    4: "fixo_2000",
    5: "fixo_500_overlap_50",
    6: "fixo_500_overlap_200",
    7: "paragrafo",
    8: "sentenca_3",
    9: "recursivo",
    10: "markdown_heading",
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


def ler_documentos_markdown(diretorio: Path = DOCUMENTOS_DIR) -> List[Dict[str, str]]:
    """Lê todos os arquivos .md presentes na pasta informada."""
    documentos = []
    padrao = os.path.join(str(diretorio), "*.md")
    arquivos = glob.glob(padrao)

    for caminho in sorted(arquivos):
        with open(caminho, "r", encoding="utf-8") as f:
            documentos.append({
                "arquivo": os.path.basename(caminho),
                "texto": f.read()
            })
    return documentos


def criar_splitter(grupo: int):
    """Fábrica de TextSplitters para os grupos padrão (1 a 7 e 9)."""
    if grupo == 1:
        return CharacterTextSplitter(separator="", chunk_size=200, chunk_overlap=0)
    elif grupo == 2:
        return CharacterTextSplitter(separator="", chunk_size=500, chunk_overlap=0)
    elif grupo == 3:
        return CharacterTextSplitter(separator="", chunk_size=1000, chunk_overlap=0)
    elif grupo == 4:
        return CharacterTextSplitter(separator="", chunk_size=2000, chunk_overlap=0)
    elif grupo == 5:
        return CharacterTextSplitter(separator="", chunk_size=500, chunk_overlap=50)
    elif grupo == 6:
        return CharacterTextSplitter(separator="", chunk_size=500, chunk_overlap=200)
    elif grupo == 7:
        return CharacterTextSplitter(separator="\n\n", chunk_size=1000, chunk_overlap=0)
    elif grupo == 9:
        return RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=0,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
    raise ValueError(f"Grupo inválido para a fábrica criar_splitter: {grupo}")


def montar_trechos(documentos: List[Dict[str, str]], grupo: int) -> List[Dict[str, Any]]:
    """Gera chunks usando os splitters baseados no LangChain (Grupos 1-7 e 9)."""
    splitter = criar_splitter(grupo)
    trechos = []

    for documento in documentos:
        partes = splitter.split_text(documento["texto"])
        for indice, parte in enumerate(partes, start=1):
            trechos.append({
                "arquivo": documento["arquivo"],
                "indice": indice,
                "grupo": grupo,
                "tamanho": len(parte),
                "texto": parte,
            })
    return trechos


def montar_trechos_linhas(documentos: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """Quebra os documentos linha por linha para a busca semântica manual."""
    trechos = []

    for documento in documentos:
        indice = 1
        for linha in documento["texto"].splitlines():
            texto = linha.strip()
            if not texto:
                continue

            trechos.append({
                "arquivo": documento["arquivo"],
                "indice": indice,
                "grupo": "linha",
                "tamanho": len(texto),
                "texto": texto,
            })
            indice += 1

    return trechos


def montar_trechos_sentencas(documentos: List[Dict[str, str]], tamanho_grupo: int = 3) -> List[Dict[str, Any]]:
    """Grupo 8: Quebra o texto em sentenças e junta em blocos de N sentenças."""
    trechos = []

    for documento in documentos:
        sentencas = [s.strip() for s in re.split(r'(?<=[.!?])\s+', documento["texto"]) if s.strip()]

        chunk_indice = 1
        for i in range(0, len(sentencas), tamanho_grupo):
            bloco = " ".join(sentencas[i : i + tamanho_grupo])
            trechos.append({
                "arquivo": documento["arquivo"],
                "indice": chunk_indice,
                "grupo": 8,
                "tamanho": len(bloco),
                "texto": bloco,
            })
            chunk_indice += 1

    return trechos


def montar_trechos_markdown(documentos: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """Grupo 10: Usa MarkdownHeaderTextSplitter preservando a estrutura de cabeçalhos."""
    headers_to_split_on = [
        ("#", "h1"),
        ("##", "h2"),
        ("###", "h3"),
    ]
    splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    trechos = []

    for documento in documentos:
        partes = splitter.split_text(documento["texto"])
        for indice, parte in enumerate(partes, start=1):
            trechos.append({
                "arquivo": documento["arquivo"],
                "indice": indice,
                "grupo": 10,
                "tamanho": len(parte.page_content),
                "texto": parte.page_content,
                "metadata": parte.metadata,
            })
    return trechos

def gerar_embeddings_em_lote(textos: List[str], lote_tamanho: int = 64) -> Dict[str, List[float]]:
    """Gera embeddings em lote utilizando a API local compatível com OpenAI."""
    embeddings = {}
    textos_unicos = list(dict.fromkeys(texto.strip() for texto in textos if texto and texto.strip()))

    for inicio in range(0, len(textos_unicos), lote_tamanho):
        lote = textos_unicos[inicio : inicio + lote_tamanho]
        response = client.embeddings.create(
            model=embedding_model,
            input=lote,
            encoding_format="float",
        )

        for texto, item in zip(lote, response.data):
            embeddings[texto] = item.embedding

    return embeddings


def similaridade_cosseno(embedding_a: List[float], embedding_b: List[float]) -> float:
    """Calcula a similaridade de cosseno entre dois vetores de embedding."""
    if len(embedding_a) != len(embedding_b):
        raise ValueError("Embeddings precisam ter a mesma dimensão")

    produto_escalar = 0.0
    norma_a = 0.0
    norma_b = 0.0

    for a, b in zip(embedding_a, embedding_b):
        produto_escalar += a * b
        norma_a += a ** 2
        norma_b += b ** 2

    if norma_a == 0 or norma_b == 0:
        return 0.0

    return produto_escalar / ((norma_a ** 0.5) * (norma_b ** 0.5))


def distancia_euclidiana(embedding_a: List[float], embedding_b: List[float]) -> float:
    """Calcula a distância euclidiana entre dois vetores de embedding."""
    if len(embedding_a) != len(embedding_b):
        raise ValueError("Embeddings precisam ter a mesma dimensão")

    return sum((a - b) ** 2 for a, b in zip(embedding_a, embedding_b)) ** 0.5


def distancia_cosseno(embedding_a: List[float], embedding_b: List[float]) -> float:
    """Calcula a distância de cosseno entre dois vetores de embedding."""
    return 1.0 - similaridade_cosseno(embedding_a, embedding_b)


def buscar_top_k(
    query: str,
    trechos: List[Dict[str, Any]],
    embeddings: Dict[str, List[float]],
    k: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Ordena os trechos por similaridade de cosseno com a query."""
    query_key = query.strip()
    query_embedding = embeddings[query_key]
    resultados = []

    for trecho in trechos:
        texto_key = trecho["texto"].strip()
        if not texto_key:
            continue

        trecho_embedding = embeddings[texto_key]
        score = similaridade_cosseno(query_embedding, trecho_embedding)

        item_resultado = {
            "arquivo": trecho["arquivo"],
            "indice": trecho["indice"],
            "tamanho": trecho["tamanho"],
            "score_similaridade": round(score, 4),
            "texto": trecho["texto"],
        }

        if "metadata" in trecho and trecho["metadata"]:
            item_resultado["metadata"] = trecho["metadata"]

        resultados.append(item_resultado)

    resultados.sort(key=lambda x: x["score_similaridade"], reverse=True)
    return resultados[:k] if k is not None else resultados


def gerar_relatorio_busca_semantica(
    queries: List[str],
    k: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Gera o relatório executando os 10 experimentos para todas as queries."""
    documentos = ler_documentos_markdown()
    relatorio = []

    for grupo in range(1, 11):
        nome_estrategia = ESTRATEGIAS[grupo]

        if grupo == 8:
            trechos = montar_trechos_sentencas(documentos, tamanho_grupo=3)
        elif grupo == 10:
            trechos = montar_trechos_markdown(documentos)
        else:
            trechos = montar_trechos(documentos, grupo)

        if not trechos:
            continue

        textos_para_embedding = list(queries) + [trecho["texto"] for trecho in trechos]
        embeddings = gerar_embeddings_em_lote(textos_para_embedding)

        for query in queries:
            resultado_query = next(
                (item for item in relatorio if item["query"] == query),
                None
            )

            if resultado_query is None:
                resultado_query = {
                    "query": query,
                    "resultados": {}
                }
                relatorio.append(resultado_query)

            resultado_query["resultados"][nome_estrategia] = buscar_top_k(
                query,
                trechos,
                embeddings,
                k=k
            )

    return relatorio


def comparar_frases_teste() -> Dict[str, Any]:
    """Compara a frase âncora com exemplos de sentidos diferentes."""
    frase_ancora = "O cachorro correu no parque e brincou com a bola."
    frases_comparacao = [
        ("Similar (mesmo sentido, palavras diferentes)", "Um cão estava correndo no jardim e brincando com seu brinquedo."),
        ("Relacionado (mesmo contexto de animais)", "O gato dormiu na almofada da sala durante toda a tarde."),
        ("Diferente (outro domínio - economia)", "A taxa de juros do banco central subiu dois pontos percentuais."),
        ("Oposto/Negação", "Nenhum animal esteve no parque e o cão permaneceu preso em casa."),
    ]

    textos = [frase_ancora] + [frase for _, frase in frases_comparacao]
    embeddings = gerar_embeddings_em_lote(textos)
    embedding_ancora = embeddings[frase_ancora]

    resultados = []
    for rotulo, frase in frases_comparacao:
        embedding_comparacao = embeddings[frase]
        resultados.append({
            "rotulo": rotulo,
            "frase": frase,
            "distancia_euclidiana": round(distancia_euclidiana(embedding_ancora, embedding_comparacao), 4),
            "similaridade_cosseno": round(similaridade_cosseno(embedding_ancora, embedding_comparacao), 4),
            "distancia_cosseno": round(distancia_cosseno(embedding_ancora, embedding_comparacao), 4),
        })

    return {
        "frase_ancora": frase_ancora,
        "resultados": resultados,
    }


def gerar_relatorio_top3_busca_manual(queries: List[str]) -> List[Dict[str, Any]]:
    """Executa a busca semântica manual em linhas, parágrafos e capítulos."""
    documentos = ler_documentos_markdown()
    estrategias = {
        "linha": montar_trechos_linhas(documentos),
        "paragrafo": montar_trechos(documentos, 7),
        "capitulo": montar_trechos_markdown(documentos),
    }
    textos_para_embedding = list(queries)
    for trechos in estrategias.values():
        textos_para_embedding.extend(trecho["texto"] for trecho in trechos)

    embeddings = gerar_embeddings_em_lote(textos_para_embedding)
    relatorio = []

    for query in queries:
        item_query = {
            "query": query,
            "top_3_por_estrategia": {},
        }

        for nome_estrategia, trechos in estrategias.items():
            item_query["top_3_por_estrategia"][nome_estrategia] = buscar_top_k(
                query,
                trechos,
                embeddings,
                k=3,
            )

        relatorio.append(item_query)

    return relatorio


if __name__ == "__main__":
    queries_teste = [
        "O que é autonomia e opacidade algorítmica?",
        "O que é o diário de bordo da IA?",
        "Quais são os principais problemas éticos em modelos de linguagem?",
    ]

    print(f"Gerando embeddings locais com {embedding_model}...")
    EMBEDDINGS_DIR.mkdir(parents=True, exist_ok=True)

    relatorio_comparacao = comparar_frases_teste()
    arquivo_comparacao = EMBEDDINGS_DIR / "Aula03_comparacao_frases.json"
    with open(arquivo_comparacao, "w", encoding="utf-8") as f:
        json.dump(relatorio_comparacao, f, indent=2, ensure_ascii=False)

    relatorio_top3 = gerar_relatorio_top3_busca_manual(queries_teste)
    arquivo_top3 = EMBEDDINGS_DIR / "Aula03_busca_semantica_manual.json"
    with open(arquivo_top3, "w", encoding="utf-8") as f:
        json.dump(relatorio_top3, f, indent=2, ensure_ascii=False)

    relatorio_completo = gerar_relatorio_busca_semantica(queries_teste, k=None)

    LIMIAR = 0.6
    relatorio_maiores = []
    relatorio_menores = []

    for item in relatorio_completo:
        res_maiores = {}
        res_menores = {}

        for estrategia, chunks in item["resultados"].items():
            res_maiores[estrategia] = [c for c in chunks if c["score_similaridade"] >= LIMIAR]
            res_menores[estrategia] = [c for c in chunks if c["score_similaridade"] < LIMIAR]

        relatorio_maiores.append({
            "query": item["query"],
            "fator_filtro": f"score_similaridade >= {LIMIAR}",
            "resultados": res_maiores
        })

        relatorio_menores.append({
            "query": item["query"],
            "fator_filtro": f"score_similaridade < {LIMIAR}",
            "resultados": res_menores
        })

    arquivo_maiores = EMBEDDINGS_DIR / "relatorio_maiores_ou_igual_06.json"
    arquivo_menores = EMBEDDINGS_DIR / "relatorio_menores_06.json"

    with open(arquivo_maiores, "w", encoding="utf-8") as f:
        json.dump(relatorio_maiores, f, indent=2, ensure_ascii=False)

    with open(arquivo_menores, "w", encoding="utf-8") as f:
        json.dump(relatorio_menores, f, indent=2, ensure_ascii=False)

    print("\nArquivos salvos com sucesso!")
    print(f" - Comparação de frases: {arquivo_comparacao}")
    print(f" - TOP 3 busca manual: {arquivo_top3}")
    print(f" - Scores >= 0.6: {arquivo_maiores}")
    print(f" - Scores <  0.6: {arquivo_menores}")
