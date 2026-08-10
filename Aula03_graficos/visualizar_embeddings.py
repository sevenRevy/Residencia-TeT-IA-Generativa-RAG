import json
from pathlib import Path

import matplotlib.pyplot as plt
import plotly.express as px

from sklearn.decomposition import PCA


# ==========================
# Configurações
# ==========================

embedding_folder = Path("Aula03_embedding_output")
output_folder = Path("Aula03_graficos")

output_folder.mkdir(exist_ok=True)


# ==========================
# Carregar embeddings
# ==========================

termos = []
vetores = []


for arquivo in embedding_folder.glob("*.json"):

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


print(f"Embeddings carregados: {len(vetores)}")
print(f"Dimensão original: {len(vetores[0])}")


# ==========================
# PCA 2D
# ==========================

pca_2d = PCA(n_components=2)

embeddings_2d = pca_2d.fit_transform(vetores)


plt.figure(figsize=(8, 6))

plt.scatter(
    embeddings_2d[:, 0],
    embeddings_2d[:, 1]
)


for i, termo in enumerate(termos):

    plt.annotate(
        termo,
        (
            embeddings_2d[i, 0],
            embeddings_2d[i, 1]
        )
    )


plt.title("Embeddings - PCA 2D")
plt.xlabel("Componente Principal 1")
plt.ylabel("Componente Principal 2")


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
    text=termos,
    title="Embeddings - PCA 3D"
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