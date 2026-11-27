# PARA DIBUJA LOS 2 DIAGRAMAS
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression

datos = pd.read_csv("datos/ventas/demanda.csv")
datos["date"] = pd.to_datetime(datos["date"])
datos = datos.sort_values(["store", "item", "date"])
datos["ayer"] = datos.groupby(["store", "item"])["sales"].shift(1)
datos["semana_pasada"] = datos.groupby(["store", "item"])["sales"].shift(7)
datos["dia"] = datos["date"].dt.day_of_week
datos["mes"] = datos["date"].dt.month


aprender = datos[datos["date"] < "2017-01-01"]
examen = datos[datos["date"] >= "2017-01-01"]
print("aprender:", len(aprender), "examen:", len(examen))

error = (examen["sales"] - examen["ayer"]).abs().mean()
print("Igual que ayer → se equivoca en promedio:", round(error, 1), "unidades")

pistas = ["ayer", "semana_pasada", "dia", "mes"]
aprender = aprender.dropna()

lineal = LinearRegression().fit(aprender[pistas], aprender["sales"])
examen["lineal"] = lineal.predict(examen[pistas])
error_lineal = (examen["sales"] - examen["lineal"]).abs().mean()
print("Regresión lineal → se equivoca en promedio:", round(error_lineal, 1), "unidades")

bosque = RandomForestRegressor(n_estimators=200, random_state=42, min_samples_leaf=50, n_jobs=-1)
bosque.fit(aprender[pistas], aprender["sales"])
examen["bosque"] = bosque.predict(examen[pistas])
error_bosque = (examen["sales"] - examen["bosque"]).abs().mean()
print("Bosque aleatorio → se equivoca en promedio:", round(error_bosque, 1), "unidades")

for metodo in ["ayer", "lineal", "bosque"]:
    diferencia = examen["sales"] - examen[metodo]
    mae = diferencia.abs().mean()
    rmse = (diferencia**2).mean() ** 0.5
    print(metodo, "→ MAE:", round(mae, 1), "RMSE:", round(rmse, 1))

una = examen[(examen["store"] == 1) & (examen["item"] == 1)].head(90)
fig, ax = plt.subplots(figsize=(12, 4))
ax.plot(una["date"], una["sales"], label="Ventas reales")
ax.plot(una["date"], una["bosque"], label="Pronóstico (bosque)")
ax.set_title("Tienda 1, producto 1: enero a marzo de 2017")
ax.legend()
fig.savefig("ventas/real_vs_pronostico.png")
grupos = pd.read_csv("ventas/grupos.csv")
examen = examen.merge(grupos, on=["store", "item"])
for metodo in ["ayer", "lineal", "bosque"]:
    examen["error_" + metodo] = (examen["sales"] - examen[metodo]).abs()
print(examen.groupby("grupo")[["error_ayer", "error_lineal", "error_bosque"]].mean().round(1))
