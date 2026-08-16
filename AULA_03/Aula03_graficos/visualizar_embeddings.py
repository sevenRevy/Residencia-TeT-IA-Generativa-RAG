import json
from pathlib import Path

import matplotlib.pyplot as plt
import plotly.express as px

from sklearn.decomposition import PCA


# ==========================
# Configurações
# ==========================

REPO_DIR = Path(__file__).resolve().parents[2]
embedding_folder = REPO_DIR / "corpus" / "embeddings" / "aula03"
output_folder = Path(__file__).resolve().parent

output_folder.mkdir(exist_ok=True)

TERMOS = [
    "gato",
    "felino",
    "cachorro",
    "carro",
    "caminhão",
    "moto",
    "banana",
    "maçã",
    "goiaba",
]

CATEGORIAS = {
    "gato": "animais",
    "felino": "animais",
    "cachorro": "animais",
    "carro": "veículos",
    "caminhão": "veículos",
    "moto": "veículos",
    "banana": "frutas",
    "maçã": "frutas",
    "goiaba": "frutas",
}


# ==========================
# Carregar embeddings
# ==========================

termos = []
vetores = []
categorias = []


for termo_esperado in TERMOS:
    arquivo = embedding_folder / f"{termo_esperado}.json"

    with arquivo.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Formato:
    # {
    #   "texto": "gato",
    #   "embedding": [...]
    # }
    if "embedding" in data:
        embedding = data["embedding"]
        termo = data.get("texto", arquivo.stem)

    # Formato response.model_dump()
    elif "data" in data:
        embedding = data["data"][0]["embedding"]
        termo = arquivo.stem

    else:
        print(f"Ignorado: {arquivo.name}")
        continue


    termos.append(termo)
    vetores.append(embedding)
    categorias.append(CATEGORIAS[termo_esperado])


print(f"Embeddings carregados: {len(vetores)}")
print(f"Dimensão original: {len(vetores[0])}")


# ==========================
# PCA 2D
# ==========================

pca_2d = PCA(n_components=2)

embeddings_2d = pca_2d.fit_transform(vetores)


plt.figure(figsize=(9, 6))

cores = {
    "animais": "#1f77b4",
    "veículos": "#2ca02c",
    "frutas": "#ff7f0e",
}

for categoria, cor in cores.items():
    indices = [i for i, valor in enumerate(categorias) if valor == categoria]
    plt.scatter(
        embeddings_2d[indices, 0],
        embeddings_2d[indices, 1],
        label=categoria,
        color=cor,
        s=70,
    )

ajustes_rotulos = {
    "gato": (10, 0),
    "cachorro": (-46, 2),
}

for i, termo in enumerate(termos):

    plt.annotate(
        termo,
        (
            embeddings_2d[i, 0],
            embeddings_2d[i, 1]
        ),
        textcoords="offset points",
        xytext=ajustes_rotulos.get(termo, (0, 0)),
    )


variancia_2d = pca_2d.explained_variance_ratio_ * 100
plt.title("Embeddings Qwen - PCA 2D")
plt.xlabel("Componente Principal 1")
plt.ylabel("Componente Principal 2")
plt.figtext(
    0.5,
    -0.02,
    f"Variância explicada: PC1 {variancia_2d[0]:.1f}% | PC2 {variancia_2d[1]:.1f}%",
    ha="center",
)
plt.legend(title="Grupo")
plt.grid(alpha=0.2)
plt.margins(x=0.1, y=0.1)


plt.savefig(
    output_folder / "embeddings_pca_2d.png",
    dpi=300,
    bbox_inches="tight"
)


plt.close()


# ==========================
# PCA 3D
# ==========================

pca_3d = PCA(n_components=3)

embeddings_3d = pca_3d.fit_transform(vetores)


fig = px.scatter_3d(
    x=embeddings_3d[:, 0],
    y=embeddings_3d[:, 1],
    z=embeddings_3d[:, 2],
    color=categorias,
    text=termos,
    hover_name=termos,
    labels={"color": "Grupo"},
    title="Embeddings Qwen - PCA 3D"
)

fig.update_layout(
    scene=dict(
        xaxis=dict(range=[
            embeddings_3d[:,0].min() - 0.5,
            embeddings_3d[:,0].max() + 0.5
        ]),
        yaxis=dict(range=[
            embeddings_3d[:,1].min() - 0.5,
            embeddings_3d[:,1].max() + 0.5
        ]),
        zaxis=dict(range=[
            embeddings_3d[:,2].min() - 0.5,
            embeddings_3d[:,2].max() + 0.5
        ])
    )
)


fig.update_traces(
    marker_size=8
)


fig.write_html(
    output_folder / "embeddings_pca_3d.html"
)


print("Gráficos gerados:")
print(output_folder / "embeddings_pca_2d.png")
print(output_folder / "embeddings_pca_3d.html")
