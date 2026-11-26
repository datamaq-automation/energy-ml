"""src/infrastructure/sklearn/medioambiente_modelador.py — Implementa ModeladorEpisodios con pandas + sklearn.

Traduce las tablas de pandas a los value objects del dominio; el caso de uso
nunca ve un DataFrame.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.domain.medioambiente.value_objects import (
    CambioDistribucion,
    DiagnosticoK,
    MatrizConfusion,
    MetricasModelo,
    Particion,
    PerfilGrupo,
)
from src.infrastructure.graficos.medioambiente import graficar_diagnosticos
from src.infrastructure.sklearn.medioambiente_agrupamiento import (
    agrupar_meteo,
    calcular_diagnosticos_k,
    proporcion_episodios,
    resumen_grupos,
)
from src.infrastructure.sklearn.medioambiente_preparacion import (
    construir_etiqueta,
    construir_features,
)
from src.infrastructure.sklearn.medioambiente_split import split_aleatorio
from src.infrastructure.sklearn.medioambiente_supervisado import (
    matriz_confusion,
    predecir_particion,
    separar_xy,
)
from src.infrastructure.sklearn.medioambiente_temporal import (
    detectar_cambio_distribucion,
    split_temporal,
)


class ModeladorEpisodiosSklearn:
    """Motor de las Tareas A, B y C sobre la tabla horaria de Air Quality."""

    def contar_filas(self, crudo: pd.DataFrame) -> int:
        """Cantidad de mediciones horarias cargadas."""
        return len(crudo)

    def diagnosticar_k(self, crudo: pd.DataFrame) -> list[DiagnosticoK]:
        """Inercia y silueta de K-means para k en [K_MIN, K_MAX]."""
        tabla = calcular_diagnosticos_k(crudo)
        return [
            DiagnosticoK(
                k=int(fila["k"]), inercia=float(fila["inercia"]), silueta=float(fila["silueta"])
            )
            for fila in tabla.to_dict("records")
        ]

    def perfilar_grupos(self, crudo: pd.DataFrame, k: int) -> list[PerfilGrupo]:
        """Agrupa con k clusters y combina medias meteorológicas con proporción de episodios."""
        agrupado = construir_etiqueta(agrupar_meteo(crudo, k=k))
        medias = resumen_grupos(agrupado)
        episodios = proporcion_episodios(agrupado)
        return [
            PerfilGrupo(
                grupo=int(grupo),
                horas=int(episodios.loc[grupo, "n_horas"]),
                temperatura_media=float(medias.loc[grupo, "T_mean"]),
                humedad_relativa_media=float(medias.loc[grupo, "RH_mean"]),
                humedad_absoluta_media=float(medias.loc[grupo, "AH_mean"]),
                proporcion_episodio=float(episodios.loc[grupo, "proporcion_episodio"]),
            )
            for grupo in medias.index
        ]

    def preparar(self, crudo: pd.DataFrame) -> pd.DataFrame:
        """Features anticipables (lags + calendario) y etiqueta `episodio`."""
        return construir_etiqueta(construir_features(crudo))

    def evaluar(self, datos: pd.DataFrame, particion: Particion) -> list[MetricasModelo]:
        """Entrena con train y mide sobre test, con matriz de confusión por modelo."""
        separar = split_temporal if particion is Particion.TEMPORAL else split_aleatorio
        train, test = separar(datos)
        tabla, predicciones = predecir_particion(train, test)
        _, y_test = separar_xy(test)
        metricas: list[MetricasModelo] = []
        for fila in tabla.to_dict("records"):
            matriz = matriz_confusion(y_test, predicciones[str(fila["modelo"])])
            metricas.append(
                MetricasModelo(
                    modelo=str(fila["modelo"]),
                    particion=particion,
                    accuracy=float(fila["accuracy"]),
                    precision=float(fila["precision"]),
                    recall=float(fila["recall"]),
                    f1=float(fila["f1"]),
                    matriz=MatrizConfusion(
                        verdaderos_negativos=int(matriz[0, 0]),
                        falsos_positivos=int(matriz[0, 1]),
                        falsos_negativos=int(matriz[1, 0]),
                        verdaderos_positivos=int(matriz[1, 1]),
                    ),
                )
            )
        return metricas

    def detectar_cambios(self, datos: pd.DataFrame) -> list[CambioDistribucion]:
        """Compara cada feature entre el train y el test temporales."""
        train, test = split_temporal(datos)
        tabla = detectar_cambio_distribucion(train, test)
        return [
            CambioDistribucion(
                feature=str(fila["feature"]),
                media_train=float(fila["media_train"]),
                media_test=float(fila["media_test"]),
                desvio_estandarizado=float(fila["desvio_estandarizado"]),
                cambio=bool(fila["cambio"]),
            )
            for fila in tabla.to_dict("records")
        ]

    def graficar_diagnosticos(self, diagnosticos: list[DiagnosticoK], destino: str) -> list[str]:
        """Gráficos de codo y silueta en `destino`; devuelve las rutas."""
        tabla = pd.DataFrame([vars(d) for d in diagnosticos])
        return [str(ruta) for ruta in graficar_diagnosticos(tabla, Path(destino))]
