import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENAI_API_KEY"),
)

output_folder = Path("Aula03_embedding_output")
output_folder.mkdir(exist_ok=True)

documents_folder = Path("Aula02_arquivos_output")
embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "nvidia/nemotron-3-embed-1b:free")


def gerar_embedding(texto):
    response = client.embeddings.create(
        model=embedding_model,
        input=texto,
        encoding_format="float",
    )
    return response.data[0].embedding


def gerar_embeddings_em_lote(textos, lote_tamanho=64):
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


def similaridade_cosseno(embedding_a, embedding_b):
    if len(embedding_a) != len(embedding_b):
        raise ValueError("Embeddings precisam ter a mesma dimensão")

    produto_escalar = 0
    norma_a = 0
    norma_b = 0

    for a, b in zip(embedding_a, embedding_b):
        produto_escalar += a * b
        norma_a += a ** 2
        norma_b += b ** 2

    return produto_escalar / ((norma_a ** 0.5) * (norma_b ** 0.5))


def salvar_json(nome_arquivo, dados):
    arquivo = output_folder / nome_arquivo
    with arquivo.open("w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
    print(f"Salvo: {arquivo}")


def ler_documentos_markdown():
    documentos = []
    for arquivo in sorted(documents_folder.glob("*.md")):
        documentos.append(
            {
                "arquivo": arquivo.name,
                "texto": arquivo.read_text(encoding="utf-8"),
            }
        )
    return documentos


def quebrar_em_linhas(texto):
    return [linha.strip() for linha in texto.splitlines() if linha.strip()]


def quebrar_em_paragrafos(texto):
    return [paragrafo.strip() for paragrafo in re.split(r"\n\s*\n", texto) if paragrafo.strip()]


def quebrar_em_capitulos(texto):
    linhas = texto.splitlines()
    capitulos = []
    bloco_atual = []

    for linha in linhas:
        if linha.lstrip().startswith("#") and bloco_atual:
            capitulos.append("\n".join(bloco_atual).strip())
            bloco_atual = [linha]
            continue

        if linha.lstrip().startswith("#") and not bloco_atual:
            bloco_atual.append(linha)
            continue

        bloco_atual.append(linha)

    if bloco_atual:
        capitulos.append("\n".join(bloco_atual).strip())

    if not capitulos:
        return [texto.strip()]

    return [capitulo for capitulo in capitulos if capitulo]


def montar_trechos(documentos, granularidade):
    trechos = []

    for documento in documentos:
        if granularidade == "linha":
            partes = quebrar_em_linhas(documento["texto"])
        elif granularidade == "paragrafo":
            partes = quebrar_em_paragrafos(documento["texto"])
        elif granularidade == "capitulo":
            partes = quebrar_em_capitulos(documento["texto"])
        else:
            raise ValueError(f"Granularidade inválida: {granularidade}")

        for indice, parte in enumerate(partes, start=1):
            trechos.append(
                {
                    "arquivo": documento["arquivo"],
                    "indice": indice,
                    "granularidade": granularidade,
                    "texto": parte,
                }
            )

    return trechos


def buscar_top_k(query, trechos, embeddings, k=3):
    query_embedding = embeddings[query]
    resultados = []

    for trecho in trechos:
        resultados.append(
            {
                **trecho,
                "similaridade_cosseno": similaridade_cosseno(query_embedding, embeddings[trecho["texto"]]),
            }
        )

    resultados.sort(key=lambda item: item["similaridade_cosseno"], reverse=True)
    return resultados[:k]


def gerar_relatorio_busca_semantica(queries):
    documentos = ler_documentos_markdown()
    relatorio = []

    for granularidade in ("linha", "paragrafo", "capitulo"):
        trechos = montar_trechos(documentos, granularidade)
        textos_para_embeding = list(queries) + [trecho["texto"] for trecho in trechos]
        embeddings = gerar_embeddings_em_lote(textos_para_embeding)

        for query in queries:
            resultado_query = next((item for item in relatorio if item["query"] == query), None)
            if resultado_query is None:
                resultado_query = {"query": query, "resultados": {}}
                relatorio.append(resultado_query)

            resultado_query["resultados"][granularidade] = buscar_top_k(query, trechos, embeddings, k=3)

    return relatorio


def gerar_relatorio_comparacao_frases():
    frase_ancora = "O cachorro correu no parque e brincou com a bola."
    frases_comparacao = [
        ("Similar (mesmo sentido, palavras diferentes)", "Um cão estava correndo no jardim e brincando com seu brinquedo."),
        ("Relacionado (mesmo contexto de animais)", "O gato dormiu na almofada da sala durante toda a tarde."),
        ("Diferente (outro domínio - economia)", "A taxa de juros do banco central subiu dois pontos percentuais."),
        ("Oposto/Negação", "Nenhum animal esteve no parque e o cão permaneceu preso em casa."),
    ]

    textos_para_embedding = [frase_ancora] + [frase for _, frase in frases_comparacao]
    embeddings = gerar_embeddings_em_lote(textos_para_embedding)
    embedding_ancora = embeddings[frase_ancora]
    comparacoes = []

    for rotulo, frase in frases_comparacao:
        comparacoes.append(
            {
                "rotulo": rotulo,
                "frase": frase,
                "similaridade_cosseno": similaridade_cosseno(embedding_ancora, embeddings[frase]),
            }
        )

    comparacoes.sort(key=lambda item: item["similaridade_cosseno"], reverse=True)

    return {
        "frase_ancora": frase_ancora,
        "comparacoes": comparacoes,
    }


if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("Defina OPENAI_API_KEY no .env ou no ambiente antes de executar este script.")

    relatorio_comparacao = gerar_relatorio_comparacao_frases()
    salvar_json("Aula03_comparacao_frases.json", relatorio_comparacao)

    queries = [
        "O que é autonomia e opacidade algorítmica?",
        "O que é o diário de bordo da IA?",
        "Como a IA afeta a escrita acadêmica?",
    ]
    relatorio_busca = gerar_relatorio_busca_semantica(queries)
    salvar_json("Aula03_busca_semantica_manual.json", relatorio_busca)
