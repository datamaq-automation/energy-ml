"""tests/educacion/test_ablacion_sex_school.py — Ablación de sex/school (decisión del PR)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.adapters.educacion.gateways.estudiantes_csv import load_students
from src.application.educacion.evaluacion import evaluate_predictions, subgroup_metrics
from src.application.educacion.preparacion import split_train_test
from src.domain.educacion.modelos import CATEGORICAL_FEATURES, MODEL_FEATURES, SEED
from src.infrastructure.sklearn.educacion_modelos import build_logistic_regression

#: Variante "con": las 18 variables originales (school y sex entre Fedu y age).
FEATURES_CON: tuple[str, ...] = (*MODEL_FEATURES[:7], "school", "sex", *MODEL_FEATURES[7:])
#: Categóricas originales: school y sex iban delante de las del modelo actual.
CATS_CON: tuple[str, ...] = ("school", "sex", *CATEGORICAL_FEATURES)

#: Los mismos dos clasificadores de la Tarea B (semilla 42).
CLASSIFIERS = {
    "logistic_regression": lambda: LogisticRegression(max_iter=1000, random_state=SEED),
    "random_forest": lambda: RandomForestClassifier(
        n_estimators=200, class_weight="balanced", random_state=SEED
    ),
}


def pipeline_con(features: tuple[str, ...], classifier: object) -> Pipeline:
    """Mismo preprocesado que producción, pero con las variables indicadas."""
    cats = [column for column in CATS_CON if column in features]
    nums = [column for column in features if column not in cats]
    pre = ColumnTransformer(
        transformers=[
            ("num", Pipeline([("scaler", StandardScaler())]), nums),
            (
                "cat",
                Pipeline([("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))]),
                cats,
            ),
        ],
        remainder="drop",
    )
    return Pipeline([("pre", pre), ("clf", classifier)])


def brecha_sexo(y_true: pd.Series, predictions: np.ndarray, sex: pd.Series) -> float:
    """Diferencia de recall de 'desaprobado' entre mujeres y varones."""
    table = subgroup_metrics(y_true, predictions, sex)
    return float(table["recall"].max() - table["recall"].min())


@pytest.fixture(scope="module")
def students() -> pd.DataFrame:
    """Dataset real una sola vez para toda la ablativa."""
    return load_students()


@pytest.fixture(scope="module")
def ablacion(students: pd.DataFrame) -> dict[str, dict[str, dict[str, float]]]:
    """Corre las dos variantes (con y sin sex/school) × los dos modelos."""
    x_train, x_test, y_train, y_test = split_train_test(students)
    full_train = students.loc[x_train.index]
    full_test = students.loc[x_test.index]

    results: dict[str, dict[str, dict[str, float]]] = {"con": {}, "sin": {}}
    for variant, features in (("con", FEATURES_CON), ("sin", MODEL_FEATURES)):
        for name, make_classifier in CLASSIFIERS.items():
            pipeline = pipeline_con(features, make_classifier())
            pipeline.fit(full_train.loc[:, list(features)], y_train)
            predictions = pipeline.predict(full_test.loc[:, list(features)])
            results[variant][name] = {
                "recall": float(evaluate_predictions(y_test, predictions)["recall"]),
                "f1": float(evaluate_predictions(y_test, predictions)["f1"]),
                "brecha_sexo": brecha_sexo(y_test, predictions, full_test["sex"]),
            }
    return results


def test_quitar_sex_school_cuesta_unos_cuatro_puntos_de_recall(
    ablacion: dict[str, dict[str, dict[str, float]]],
) -> None:
    """Costo aceptado de la decisión: hasta 6 puntos de recall en cada modelo."""
    for model in CLASSIFIERS:
        costo = ablacion["con"][model]["recall"] - ablacion["sin"][model]["recall"]
        assert 0.0 <= costo <= 0.06, f"{model}: costo de recall inesperado ({costo:.3f})"


def test_brecha_por_sexo_baja_en_el_mejor_modelo(
    ablacion: dict[str, dict[str, dict[str, float]]],
) -> None:
    """Con sex/school la brecha del mejor modelo pasa de ≥0,20 a al menos 5 puntos menos."""
    con = ablacion["con"]["logistic_regression"]["brecha_sexo"]
    sin = ablacion["sin"]["logistic_regression"]["brecha_sexo"]
    assert con >= 0.20
    assert sin <= con - 0.05


def test_ambos_modelos_arrancaban_con_brecha_relevante(
    ablacion: dict[str, dict[str, dict[str, float]]],
) -> None:
    """Premisa de la decisión: la brecha existía en las dos variantes con sex/school.

    Ojo: sin sex/school la brecha de random_forest NO baja (0,29 → 0,35): el árbol
    es inestable en subgrupos chicos. Por eso la conclusión cita al mejor modelo
    (regresión logística), que es el que reporta la Tarea C.
    """
    assert ablacion["con"]["logistic_regression"]["brecha_sexo"] >= 0.20
    assert ablacion["con"]["random_forest"]["brecha_sexo"] >= 0.20


def test_mejor_modelo_por_f1_no_cambia_con_la_decision(
    ablacion: dict[str, dict[str, dict[str, float]]],
) -> None:
    """La regresión logística sigue siendo la mejor por F1 con las 18 y con las 16."""
    for variant in ("con", "sin"):
        f1_by_model = {name: data["f1"] for name, data in ablacion[variant].items()}
        assert max(f1_by_model, key=f1_by_model.get) == "logistic_regression"


def test_variante_sin_es_identica_al_pipeline_de_produccion(
    students: pd.DataFrame,
) -> None:
    """La ablativa 'sin' debe reproducir exactamente lo que corre la Tarea B hoy."""
    x_train, x_test, y_train, _ = split_train_test(students)

    produccion = build_logistic_regression()
    ablativa = pipeline_con(MODEL_FEATURES, LogisticRegression(max_iter=1000, random_state=SEED))
    for pipeline in (produccion, ablativa):
        pipeline.fit(x_train, y_train)

    assert np.array_equal(
        produccion.predict(x_test),
        ablativa.predict(x_test),
    ), "el pipeline ablativo 'sin' debe ser idéntico al de producción"
