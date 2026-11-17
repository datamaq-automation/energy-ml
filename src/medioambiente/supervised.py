"""src/medioambiente/supervised.py — Tarea B: modelos supervisados con split aleatorio."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.tree import DecisionTreeClassifier

from src.infrastructure.settings.logger import logger
from src.medioambiente.preprocess import (
    COLUMNA_ETIQUETA,
    COLUMNAS_FEATURES,
    crear_transformador,
)

SEMILLA = 42
PROFUNDIDADES_ARBOL = [3, 4, 5, 6]


def separar_xy(particion: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Features (COLUMNAS_FEATURES) y etiqueta (`episodio`) de una partición."""
    requeridas = [*COLUMNAS_FEATURES, COLUMNA_ETIQUETA]
    ausentes = [c for c in requeridas if c not in particion.columns]
    if ausentes:
        raise ValueError(f"Faltan columnas en la partición: {ausentes}")
    return particion[COLUMNAS_FEATURES].copy(), particion[COLUMNA_ETIQUETA].copy()


def ajustar_transformacion(
    train: pd.DataFrame, test: pd.DataFrame
) -> tuple[np.ndarray, np.ndarray]:
    """Ajusta imputador + escalador SOLO con train y transforma ambas particiones.

    El test nunca entra en el `fit`: su distribución no puede contaminar
    la imputación ni la escala (regla: split antes de transformar).
    """
    x_train, _ = separar_xy(train)
    x_test, _ = separar_xy(test)
    transformador = crear_transformador().fit(x_train)
    return transformador.transform(x_train), transformador.transform(x_test)


def metricas_episodio(y_verdadero: pd.Series, y_predicho: np.ndarray) -> dict[str, float]:
    """Accuracy global + precisión, recall y F1 de la clase 'episodio' (positivo = 1)."""
    return {
        "accuracy": float(accuracy_score(y_verdadero, y_predicho)),
        "precision": float(precision_score(y_verdadero, y_predicho, pos_label=1, zero_division=0)),
        "recall": float(recall_score(y_verdadero, y_predicho, pos_label=1, zero_division=0)),
        "f1": float(f1_score(y_verdadero, y_predicho, pos_label=1, zero_division=0)),
    }


def linea_base(y_verdadero: pd.Series) -> dict[str, float]:
    """Clasificador tonto que siempre predice 'sin episodio' (0)."""
    siempre_cero = np.zeros(len(y_verdadero), dtype="int8")
    return metricas_episodio(y_verdadero, siempre_cero)


def matriz_confusion(y_verdadero: pd.Series, y_predicho: np.ndarray) -> np.ndarray:
    """Matriz 2x2 [[TN, FP], [FN, TP]] sobre las clases 0 y 1."""
    return confusion_matrix(y_verdadero, y_predicho, labels=[0, 1])


def entrenar_modelos(x_train: np.ndarray, y_train: pd.Series) -> dict[str, BaseEstimator]:
    """Regresión logística balanceada + árbol con CV (max_depth 3..6, F1).

    La profundidad del árbol se elige con GridSearchCV estratificado SOLO
    sobre train (semilla 42), optimizando F1 de la clase 'episodio'.
    """
    logistic = LogisticRegression(class_weight="balanced", max_iter=1000, random_state=SEMILLA)
    arbol = GridSearchCV(
        estimator=DecisionTreeClassifier(random_state=SEMILLA),
        param_grid={"max_depth": PROFUNDIDADES_ARBOL},
        scoring="f1",
        cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=SEMILLA),
    )
    logistic.fit(x_train, y_train)
    arbol.fit(x_train, y_train)
    logger.info(
        "Modelos entrenados: logística balanceada + árbol (mejor max_depth=%s, F1 CV=%.3f)",
        arbol.best_params_["max_depth"],
        arbol.best_score_,
    )
    return {"regresion_logistica": logistic, "arbol": arbol}


def predecir_particion(
    train: pd.DataFrame, test: pd.DataFrame
) -> tuple[pd.DataFrame, dict[str, np.ndarray]]:
    """Tarea B sobre cualquier partición: tabla de métricas + predicciones en test.

    Incluye la línea base (siempre 'sin episodio'), la regresión logística
    balanceada y el árbol con CV. Transformación ajustada solo en train.
    """
    x_train_t, x_test_t = ajustar_transformacion(train, test)
    _, y_train = separar_xy(train)
    _, y_test = separar_xy(test)
    modelos = entrenar_modelos(x_train_t, y_train)
    predicciones: dict[str, np.ndarray] = {
        "linea_base": np.zeros(len(y_test), dtype="int8"),
        **{nombre: modelo.predict(x_test_t) for nombre, modelo in modelos.items()},
    }
    filas = [
        {"modelo": nombre, **metricas_episodio(y_test, prediccion)}
        for nombre, prediccion in predicciones.items()
    ]
    tabla = pd.DataFrame(filas)
    logger.info(
        "Evaluación sobre test (%d filas): F1 episodio = %s",
        len(y_test),
        {f["modelo"]: round(f["f1"], 3) for f in filas},
    )
    return tabla, predicciones
