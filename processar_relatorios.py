import json
import os
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent
pasta_relatorios = REPO_DIR / "corpus" / "reports" / "aula04"
arquivo_maiores_fixo = pasta_relatorios / "relatorio_maiores_ou_igual_06.json"
arquivo_menores_fixo = pasta_relatorios / "relatorio_menores_06.json"
arquivo_maiores_top20 = pasta_relatorios / "relatorio_maiores_top20.json"
arquivo_menores_top20 = pasta_relatorios / "relatorio_menores_top20.json"

PERCENTIL_CORTE = 0.80  # Mantém os 20% melhores scores de cada grupo
LIMIAR_FIXO = 0.06  # Corte fixo compatível com a escala real dos scores do dataset


def analisar_distribuicao(arquivos_json):
    """Exibe a média e o score máximo de cada estratégia para identificar distorções de escala."""
    print("--- ANÁLISE DE ESCALA DOS SCORES POR ESTRATÉGIA ---")
    estatisticas = {}

    for caminho_arquivo in arquivos_json:
        with caminho_arquivo.open("r", encoding="utf-8") as f:
            conteudo = json.load(f)

        for item in conteudo:
            estrategia = item.get("estrategia", "desconhecida")
            scores = [
                c.get("score_similaridade", 0)
                for c in item.get("resultados_completos", [])
            ]

            if scores:
                if estrategia not in estatisticas:
                    estatisticas[estrategia] = []
                estatisticas[estrategia].extend(scores)

    for est, scores in estatisticas.items():
        max_score = max(scores)
        min_score = min(scores)
        avg_score = sum(scores) / len(scores)
        print(
            f"Estratégia: {est:<22} | Min: {min_score:.4f} | Max: {max_score:.4f} | Média: {avg_score:.4f}"
        )
    print("-" * 55 + "\n")


def calcular_limiar_efetivo(resultados, usar_corte_adaptativo):
    # Mantém a lógica de corte separada para reutilizar com saída fixa e top 20%
    if usar_corte_adaptativo:
        scores_ordenados = sorted(
            [c.get("score_similaridade", 0) for c in resultados]
        )
        idx_corte = int(len(scores_ordenados) * PERCENTIL_CORTE)
        return scores_ordenados[min(idx_corte, len(scores_ordenados) - 1)]

    return LIMIAR_FIXO


def processar_arquivos_relatorios(arquivo_maiores, arquivo_menores, usar_corte_adaptativo):
    if not pasta_relatorios.exists():
        raise FileNotFoundError(
            f"A pasta '{pasta_relatorios}' não foi encontrada!"
        )

    arquivos_json = sorted(pasta_relatorios.glob("*.json"))

    if not arquivos_json:
        print(f"Nenhum arquivo JSON encontrado em '{pasta_relatorios}'.")
        return

    # Executa análise preventiva de distribuição de scores
    analisar_distribuicao(arquivos_json)

    dados_maiores = []
    dados_menores = []

    for caminho_arquivo in arquivos_json:
        with caminho_arquivo.open("r", encoding="utf-8") as f:
            conteudo = json.load(f)

        for item in conteudo:
            query = item.get("query", "")
            estrategia = item.get("estrategia", "")
            resultados = item.get("resultados_completos", [])

            if not resultados:
                continue

            # Define o limiar de corte para este conjunto de dados
            limiar_efetivo = calcular_limiar_efetivo(
                resultados, usar_corte_adaptativo
            )

            chunks_maiores = [
                chunk
                for chunk in resultados
                if chunk.get("score_similaridade", 0) >= limiar_efetivo
            ]
            chunks_menores = [
                chunk
                for chunk in resultados
                if chunk.get("score_similaridade", 0) < limiar_efetivo
            ]

            dados_maiores.append({
                "query": query,
                "estrategia": estrategia,
                "fator_filtro": f"score_similaridade >= {limiar_efetivo:.4f}",
                "total_chunks": len(chunks_maiores),
                "resultados_completos": chunks_maiores,
            })

            dados_menores.append({
                "query": query,
                "estrategia": estrategia,
                "fator_filtro": f"score_similaridade < {limiar_efetivo:.4f}",
                "total_chunks": len(chunks_menores),
                "resultados_completos": chunks_menores,
            })

    with open(arquivo_maiores, "w", encoding="utf-8") as f:
        json.dump(dados_maiores, f, indent=2, ensure_ascii=False)

    with open(arquivo_menores, "w", encoding="utf-8") as f:
        json.dump(dados_menores, f, indent=2, ensure_ascii=False)

    modo = "top 20%" if usar_corte_adaptativo else f"corte fixo {LIMIAR_FIXO:.2f}"
    print(f"Processamento concluído com sucesso! ({modo})")


if __name__ == "__main__":
    processar_arquivos_relatorios(
        arquivo_maiores_fixo,
        arquivo_menores_fixo,
        usar_corte_adaptativo=False,
    )
    processar_arquivos_relatorios(
        arquivo_maiores_top20,
        arquivo_menores_top20,
        usar_corte_adaptativo=True,
    )
