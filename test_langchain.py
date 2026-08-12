import glob
import json
import os
import re
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
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENAI_API_KEY"),
)

embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "nvidia/nemotron-3-embed-1b:free")

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


def ler_documentos_markdown(diretorio: str = "aula04/aula04_arquivos_output") -> List[Dict[str, str]]:
    """Lê todos os arquivos .md presentes na pasta informada."""
    documentos = []
    padrao = os.path.join(diretorio, "*.md")
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
    """Gera embeddings em lote utilizando a API do OpenRouter."""
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


def buscar_por_similaridade(
    query: str,
    trechos: List[Dict[str, Any]],
    embeddings: Dict[str, List[float]]
) -> List[Dict[str, Any]]:
    """Calcula a similaridade de todos os trechos com a query e ordena do maior para o menor (sem limitar Top-K)."""
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
    return resultados


def gerar_relatorio_busca_semantica(
    queries: List[str]
) -> List[Dict[str, Any]]:
    """Gera o relatório executando os 10 experimentos para todas as queries sem limitação de Top-K."""
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

            resultado_query["resultados"][nome_estrategia] = buscar_por_similaridade(
                query,
                trechos,
                embeddings
            )

    return relatorio


if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("Defina OPENAI_API_KEY no .env ou no ambiente antes de executar este script.")

    queries_teste = [
        "O que é autonomia e opacidade algorítmica?",
        "Quais são os principais problemas éticos em modelos de linguagem?"
    ]

    print("Gerando embeddings reais via API (avaliando todos os trechos sem limitação de Top-K)...")
    relatorio_completo = gerar_relatorio_busca_semantica(queries_teste)

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

    arquivo_maiores = "relatorio_maiores_ou_igual_06.json"
    arquivo_menores = "relatorio_menores_06.json"

    with open(arquivo_maiores, "w", encoding="utf-8") as f:
        json.dump(relatorio_maiores, f, indent=2, ensure_ascii=False)

    with open(arquivo_menores, "w", encoding="utf-8") as f:
        json.dump(relatorio_menores, f, indent=2, ensure_ascii=False)

    print("\nArquivos salvos com sucesso!")
    print(f" - Scores >= 0.6: {arquivo_maiores}")
    print(f" - Scores <  0.6: {arquivo_menores}")