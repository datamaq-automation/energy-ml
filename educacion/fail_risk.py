"""educacion/fail_risk.py — Tareas A (agrupamiento) y B (clasificación) — Issue #5.

Caso de estudio: "Riesgo de desaprobar una materia: agrupamiento, predicción y equidad".

Momento de predicción declarado en educacion/README.md: inicio del curso,
solo G1 + variables de contexto. Por eso G2 NO entra en ninguna tarea y G3
se usa exclusivamente como etiqueta (nunca como variable de entrada).

Reglas de la sección 4 del issue aplicadas aquí:
  - Cero fuga de datos: G3 solo construye la etiqueta; G2 no existe aquí.
  - Split 80/20 estratificado con random_state=42 ANTES de transformar:
    escaladores y codificadores viven dentro del Pipeline y solo se ajustan
    con los datos de train.
  - Métricas adecuadas: precisión, recall, F1 y matriz de confusión sobre
    "desaprobado" (clase positiva = 1); accuracy no alcanza por sí solo.
  - Semilla fija: random_state = SEED (42).
  - Privacidad: en pantalla solo se imprimen agregados, nunca filas individuales.
  - Sin rutas absolutas: DATA_PATH se deriva de __file__.

Ejecución:  python educacion/fail_risk.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
    silhouette_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

#: Semilla fija para todos los estimadores (regla 7 de la sección 4).
SEED = 42

#: Dataset local UCI 320 (separador ';'), relativo a la raíz del repositorio.
DATA_PATH = Path(__file__).resolve().parents[1] / "datos" / "educacion" / "student-mat.csv"

#: Variables de desempeño y hábitos permitidas para la Tarea A (sección 2 del issue).
#: G2 queda fuera por el momento de predicción; G3 es la etiqueta y jamás entra.
CLUSTER_FEATURES: tuple[str, ...] = ("G1", "studytime", "failures", "absences")

#: Rango de k evaluado en la Tarea A (sección 3, tarea A.3).
K_MIN = 2
K_MAX = 6

#: Umbral de la etiqueta: desaprobado = G3 < 10 (sección 2 del issue).
FAIL_THRESHOLD = 10

#: Variables permitidas para la Tarea B (sección 2 del issue): las 18 coherentes
#: con el momento de predicción declarado — sin G2 (desconocida) ni G3 (etiqueta).
MODEL_FEATURES: tuple[str, ...] = (
    "G1",
    "studytime",
    "failures",
    "absences",
    "higher",
    "Medu",
    "Fedu",
    "school",
    "sex",
    "age",
    "address",
    "famsup",
    "schoolsup",
    "internet",
    "goout",
    "Dalc",
    "Walc",
    "health",
)

#: Categóricas → OneHotEncoder; el resto → StandardScaler (ambos solo sobre train).
CATEGORICAL_FEATURES: tuple[str, ...] = (
    "school",
    "sex",
    "address",
    "higher",
    "famsup",
    "schoolsup",
    "internet",
)
NUMERIC_FEATURES: tuple[str, ...] = tuple(
    column for column in MODEL_FEATURES if column not in CATEGORICAL_FEATURES
)

#: Split 80/20 estratificado (reglas 2 y 3), siempre antes de transformar.
TEST_SIZE = 0.2

#: Clases de la etiqueta; DESAPROBADO es la clase positiva de las métricas.
APROBADO = 0
DESAPROBADO = 1

#: Orden de impresión de la tabla comparativa de la Tarea B.
MODEL_LABELS: tuple[tuple[str, str], ...] = (
    ("baseline", "línea base"),
    ("logistic_regression", "regresión logística"),
    ("random_forest", "bosque aleatorio"),
)


def load_students(path: Path = DATA_PATH) -> pd.DataFrame:
    """Carga el dataset de estudiantes (separador ';') y valida columnas y tipos."""
    df = pd.read_csv(path, sep=";")
    required = (*CLUSTER_FEATURES, "G3")
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas requeridas en el dataset: {missing}")
    if not pd.api.types.is_numeric_dtype(df["G3"]):
        raise ValueError("G3 debe ser numérica para construir la etiqueta de desaprobado.")
    return df


def select_cluster_features(df: pd.DataFrame) -> pd.DataFrame:
    """Extrae solo las variables permitidas para el agrupamiento (sin G2 ni G3)."""
    missing = [column for column in CLUSTER_FEATURES if column not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas requeridas: {missing}")
    return df.loc[:, list(CLUSTER_FEATURES)].copy()


def scale_features(features: pd.DataFrame) -> np.ndarray:
    """Estandariza las variables con StandardScaler (media 0, desvío 1)."""
    return StandardScaler().fit_transform(features)


def compute_k_metrics(
    scaled: np.ndarray,
    k_values: range = range(K_MIN, K_MAX + 1),
) -> tuple[list[int], list[float], list[float]]:
    """Ejecuta K-means para cada k y devuelve (ks, inercias, siluetas).

    La inercia alimenta la lectura del codo y la silueta la del score;
    ambos se calculan sobre los mismos datos escalados.
    """
    ks = list(k_values)
    if not ks:
        raise ValueError("k_values no puede estar vacío.")
    inertias: list[float] = []
    silhouettes: list[float] = []
    for k in ks:
        model = KMeans(n_clusters=k, random_state=SEED, n_init=10)
        labels = model.fit_predict(scaled)
        inertias.append(float(model.inertia_))
        silhouettes.append(float(silhouette_score(scaled, labels)))
    return ks, inertias, silhouettes


def choose_k(k_values: list[int], silhouettes: list[float]) -> int:
    """Elige k por mayor score de silueta, en complemento a la lectura del codo."""
    if not k_values or len(k_values) != len(silhouettes):
        raise ValueError("k_values y silhouettes deben ser listas no vacías de igual longitud.")
    return k_values[int(np.argmax(silhouettes))]


def fit_kmeans(scaled: np.ndarray, k: int) -> np.ndarray:
    """Ajusta K-means con semilla fija y devuelve una etiqueta de grupo por estudiante."""
    model = KMeans(n_clusters=k, random_state=SEED, n_init=10)
    return model.fit_predict(scaled)


def describe_groups(features: pd.DataFrame, labels: np.ndarray) -> pd.Series:
    """Describe cada grupo en lenguaje educativo a partir de medias agregadas.

    Solo usa promedios por grupo: nunca expone datos individuales (privacidad).
    """
    work = features.copy()
    work["group"] = labels
    grouped = work.groupby("group")[list(CLUSTER_FEATURES)].mean()
    any_failure = (
        (work["failures"] > 0).astype(float).groupby(work["group"]).mean().rename("recursada")
    )
    global_means = work[list(CLUSTER_FEATURES)].mean()
    global_failure_rate = float((work["failures"] > 0).mean())

    descriptions: dict[int, str] = {}
    for group, row in grouped.iterrows():
        performance = "Buen desempeño" if row["G1"] >= global_means["G1"] else "Desempeño bajo"
        attendance = (
            "ausencias frecuentes"
            if row["absences"] >= global_means["absences"]
            else "buena asistencia"
        )
        study = (
            "buen hábito de estudio"
            if row["studytime"] >= global_means["studytime"]
            else "poco tiempo de estudio"
        )
        history = (
            "con alta proporción de materias recursadas"
            if any_failure.loc[group] >= global_failure_rate
            else "con baja proporción de materias recursadas"
        )
        descriptions[int(group)] = (
            f"{performance} (G1 {row['G1']:.1f}) con {attendance}, {study} y {history}"
        )
    return pd.Series(descriptions, name="description", dtype=object).rename_axis("group")


def failing_rates_by_group(df: pd.DataFrame, labels: np.ndarray) -> pd.Series:
    """Proporción de desaprobados (G3 < 10) por grupo.

    Se calcula SOLO después de agrupar y únicamente para interpretar
    (sección 3, tarea A.5): la etiqueta nunca participa del agrupamiento.
    """
    failed = (df["G3"] < FAIL_THRESHOLD).astype(float)
    return failed.groupby(labels).mean().rename_axis("group").rename("failing_rate")


def plot_elbow_silhouette(
    k_values: list[int],
    inertias: list[float],
    silhouettes: list[float],
) -> None:
    """Muestra los gráficos de codo y silueta en pantalla (sin guardar archivos)."""
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].plot(k_values, inertias, marker="o")
    axes[0].set_title("Codo (inercia)")
    axes[0].set_xlabel("k")
    axes[0].set_ylabel("Inercia")
    axes[1].plot(k_values, silhouettes, marker="o")
    axes[1].set_title("Silueta")
    axes[1].set_xlabel("k")
    axes[1].set_ylabel("Score de silueta")
    fig.tight_layout()
    plt.show()
    plt.close(fig)


def run_task_a() -> dict[str, object]:
    """Ejecuta la Tarea A completa e imprime los resultados en pantalla."""
    print("=== Tarea A — K-means (Issue #5) ===")
    print(f"Variables de agrupamiento: {', '.join(CLUSTER_FEATURES)}")
    print("(G2 no disponible en el momento de predicción; G3 es solo la etiqueta)")

    df = load_students()
    features = select_cluster_features(df)
    scaled = scale_features(features)

    k_values, inertias, silhouettes = compute_k_metrics(scaled)
    best_k = choose_k(k_values, silhouettes)

    print(f"\n{'k':>3} | {'inercia':>12} | {'silueta':>8}")
    for k, inertia, score in zip(k_values, inertias, silhouettes, strict=True):
        print(f"{k:>3} | {inertia:>12.1f} | {score:>8.4f}")
    print(f"k elegido (codo + mayor silueta): {best_k}")

    labels = fit_kmeans(scaled, best_k)
    print("\nGrupos descritos en lenguaje educativo (agregados, sin datos individuales):")
    descriptions = describe_groups(features, labels)
    for group, text in descriptions.items():
        print(f"  Grupo {group}: {text}")

    print("\nProporción de desaprobados por grupo (solo interpretación, calculada tras agrupar):")
    rates = failing_rates_by_group(df, labels)
    for group, rate in rates.items():
        print(f"  Grupo {group}: {rate:.1%}")

    plot_elbow_silhouette(k_values, inertias, silhouettes)

    return {
        "k_values": k_values,
        "inertias": inertias,
        "silhouettes": silhouettes,
        "best_k": best_k,
        "labels": labels,
        "descriptions": descriptions,
        "failing_rates": rates,
    }


# ------------------------------------------------------------------------------
# Tarea B — Aprendizaje supervisado (clasificación)
# ------------------------------------------------------------------------------


def build_target(df: pd.DataFrame) -> pd.Series:
    """Construye la etiqueta 'desaprobado = G3 < 10', usando solo G3."""
    if "G3" not in df.columns:
        raise ValueError("G3 es obligatoria para construir la etiqueta.")
    return (df["G3"] < FAIL_THRESHOLD).astype(int).rename("desaprobado")


def select_model_features(df: pd.DataFrame) -> pd.DataFrame:
    """Extrae las variables permitidas para la Tarea B, sin G2 ni G3 (cero fuga)."""
    missing = [column for column in MODEL_FEATURES if column not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas requeridas: {missing}")
    return df.loc[:, list(MODEL_FEATURES)].copy()


def split_train_test(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Split 80/20 estratificado con semilla 42, ANTES de cualquier transform.

    Ningún escalador ni codificador se ajusta aquí: viven dentro del Pipeline
    y solo ven los datos de train (reglas 2 y 3 de la sección 4).
    """
    features = select_model_features(df)
    target = build_target(df)
    return train_test_split(
        features,
        target,
        test_size=TEST_SIZE,
        stratify=target,
        random_state=SEED,
    )


def build_preprocessor() -> ColumnTransformer:
    """Preprocesador: StandardScaler para numéricas y OneHotEncoder para categóricas."""
    numeric_pipe = Pipeline([("scaler", StandardScaler())])
    categorical_pipe = Pipeline(
        [("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))]
    )
    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipe, list(NUMERIC_FEATURES)),
            ("cat", categorical_pipe, list(CATEGORICAL_FEATURES)),
        ],
        remainder="drop",
    )


def build_logistic_regression() -> Pipeline:
    """Regresión logística con one-hot para categóricas (Tarea B.4)."""
    return Pipeline(
        steps=[
            ("pre", build_preprocessor()),
            ("clf", LogisticRegression(max_iter=1000, random_state=SEED)),
        ]
    )


def build_random_forest() -> Pipeline:
    """Bosque aleatorio con 200 árboles y pesos balanceados (Tarea B.5)."""
    return Pipeline(
        steps=[
            ("pre", build_preprocessor()),
            (
                "clf",
                RandomForestClassifier(
                    n_estimators=200,
                    class_weight="balanced",
                    random_state=SEED,
                ),
            ),
        ]
    )


def baseline_predictions(y_train: pd.Series, n: int) -> np.ndarray:
    """Línea base: predice siempre la clase mayoritaria de train (Tarea B.3)."""
    majority = int(y_train.value_counts().idxmax())
    return np.full(n, majority, dtype=int)


def evaluate_predictions(
    y_true: pd.Series | np.ndarray,
    y_pred: np.ndarray,
) -> dict[str, object]:
    """Accuracy, precisión, recall, F1 y matriz de confusión con foco en 'desaprobado'."""
    true_array = np.asarray(y_true)
    precision, recall, f1, _ = precision_recall_fscore_support(
        true_array,
        y_pred,
        average="binary",
        pos_label=DESAPROBADO,
        zero_division=0,
    )
    matrix = confusion_matrix(true_array, y_pred, labels=[APROBADO, DESAPROBADO])
    return {
        "accuracy": float(accuracy_score(true_array, y_pred)),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "confusion_matrix": matrix.tolist(),
    }


def run_task_b() -> dict[str, object]:
    """Ejecuta la Tarea B completa e imprime la tabla comparativa en pantalla."""
    print("=== Tarea B — Clasificación supervisada (Issue #5) ===")
    print("Momento de predicción: inicio del curso (G1 + contexto); G2 y G3 excluidas.")
    print(f"Variables ({len(MODEL_FEATURES)}): {', '.join(MODEL_FEATURES)}")

    df = load_students()
    x_train, x_test, y_train, y_test = split_train_test(df)
    print(
        f"\nSplit 80/20 estratificado ANTES de transformar (random_state={SEED}): "
        f"train={len(x_train)}, test={len(x_test)}"
    )
    print(
        f"Desaprobados: train {int(y_train.sum())} ({y_train.mean():.1%}), "
        f"test {int(y_test.sum())} ({y_test.mean():.1%})"
    )

    metrics: dict[str, dict[str, object]] = {
        "baseline": evaluate_predictions(y_test, baseline_predictions(y_train, len(x_test))),
    }

    logistic = build_logistic_regression()
    logistic.fit(x_train, y_train)
    metrics["logistic_regression"] = evaluate_predictions(y_test, logistic.predict(x_test))

    forest = build_random_forest()
    forest.fit(x_train, y_train)
    metrics["random_forest"] = evaluate_predictions(y_test, forest.predict(x_test))

    print(f"\n{'Modelo':<22} | {'Accuracy':>8} | {'Precisión':>9} | {'Recall':>6} | {'F1':>6}")
    for key, label in MODEL_LABELS:
        model_metrics = metrics[key]
        print(
            f"{label:<22} | {float(model_metrics['accuracy']):>8.3f} |"
            f" {float(model_metrics['precision']):>9.3f} |"
            f" {float(model_metrics['recall']):>6.3f} | {float(model_metrics['f1']):>6.3f}"
        )

    print("\nMatriz de confusión por modelo (0 = aprobado, 1 = desaprobado):")
    for key, label in MODEL_LABELS:
        (tn, fp), (fn, tp) = metrics[key]["confusion_matrix"]
        print(f"  {label:<22}: TN={tn} FP={fp} FN={fn} TP={tp}")

    real_models = ("logistic_regression", "random_forest")
    best = max(
        real_models,
        key=lambda name: (float(metrics[name]["f1"]), float(metrics[name]["recall"])),
    )
    beats_baseline = float(metrics[best]["recall"]) > float(metrics["baseline"]["recall"])
    print(f"\nMejor modelo (mayor F1 de desaprobado): {best}")
    print(
        f"Checklist: ¿supera a la línea base en recall de desaprobados? "
        f"{'Sí' if beats_baseline else 'NO ⚠️'} "
        f"({float(metrics[best]['recall']):.3f} vs "
        f"{float(metrics['baseline']['recall']):.3f})"
    )

    return {
        "n_train": len(x_train),
        "n_test": len(x_test),
        "train_rate": float(y_train.mean()),
        "test_rate": float(y_test.mean()),
        "metrics": metrics,
        "best_model": best,
        "beats_baseline_recall": beats_baseline,
        "models": {"logistic_regression": logistic, "random_forest": forest},
        "split": {"x_train": x_train, "x_test": x_test, "y_train": y_train, "y_test": y_test},
    }


if __name__ == "__main__":
    run_task_a()
    run_task_b()
