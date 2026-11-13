"""educacion/fail_risk.py — Tarea A: agrupamiento no supervisado (Issue #5).

Caso de estudio: "Riesgo de desaprobar una materia: agrupamiento, predicción y equidad".

Momento de predicción declarado en educacion/README.md: inicio del curso,
solo G1 + variables de contexto. Por eso G2 NO entra en ninguna tarea y G3
se usa exclusivamente como etiqueta (nunca como variable de entrada).

Reglas de la sección 4 del issue aplicadas aquí:
  - Cero fuga de datos: las variables de agrupamiento no incluyen G2 ni G3.
  - Semilla fija: random_state = SEED (42).
  - Privacidad: en pantalla solo se imprimen agregados, nunca filas individuales.
  - Sin rutas absolutas: DATA_PATH se deriva de __file__.

Ejecución:  python educacion/fail_risk.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

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


if __name__ == "__main__":
    run_task_a()
