# herramienta para grafico
import matplotlib.pyplot as plt
import pandas as pd

# herramienta para armar grupos
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

datos = pd.read_csv("datos/ventas/demanda.csv")
print(len(datos))

fichas = datos.groupby(["store", "item"])["sales"].agg(["mean", "std"])
print(fichas.head())

datos["sin_venta"] = datos["sales"] == 0
fichas["sin_venta"] = datos.groupby(["store", "item"])["sin_venta"].mean()

print(fichas.head())

datos["dia"] = pd.to_datetime(datos["date"]).dt.day_of_week
print(datos.groupby("dia")["sales"].mean())

semana = datos.groupby(["store", "item", "dia"])["sales"].mean().unstack()
fichas = fichas.join(semana)
print(fichas.head())

fichas = fichas.rename(
    columns={0: "lun", 1: "mar", 2: "mie", 3: "jue", 4: "vie", 5: "sab", 6: "dom"}
)
print(fichas.head().round().astype(int))

columnas = fichas.drop(columns="sin_venta")
escaladas = StandardScaler().fit_transform(columnas)
print(escaladas[:5].round(1))

inercias = []
siluetas = []
for k in range(2, 7):
    modelo = KMeans(n_clusters=k, random_state=42, n_init=10).fit(escaladas)
    inercias.append(modelo.inertia_)
    siluetas.append(silhouette_score(escaladas, modelo.labels_))

fig, (izq, der) = plt.subplots(1, 2, figsize=(10, 4))
izq.plot(range(2, 7), inercias, marker="o")
izq.set_title("Codo (inercia)")
izq.set_xlabel("Cantidad de grupos")
der.plot(range(2, 7), siluetas, marker="o")
der.set_title("Silueta")
der.set_xlabel("Cantidad de grupos")
fig.savefig("ventas/codo_silueta.png")

modelo = KMeans(n_clusters=3, random_state=42, n_init=10).fit(escaladas)
fichas["grupo"] = modelo.labels_
print(fichas.groupby("grupo").mean().round().astype(int))
print(fichas["grupo"].value_counts())

fichas["grupo"].to_csv("ventas/grupos.csv")
