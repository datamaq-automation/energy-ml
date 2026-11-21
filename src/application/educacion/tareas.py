"""src/application/educacion/tareas.py — Tareas A, B, C y conclusión del Issue #5.

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
  - Privacidad: solo se registran agregados, nunca filas individuales.

Las dependencias (fuente, agrupador, entrenador, graficador y bitácora)
llegan por inyección: este módulo no importa infraestructura.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.application.educacion.evaluacion import (
    analyze_fairness,
    baseline_predictions,
    evaluate_predictions,
    pick_best_model,
    subgroup_metrics,
)
from src.application.educacion.preparacion import select_cluster_features, split_train_test
from src.domain.educacion.modelos import (
    CLUSTER_FEATURES,
    CONCLUSION,
    FAIL_THRESHOLD,
    FAIRNESS_GAP_THRESHOLD,
    MODEL_FEATURES,
    MODEL_LABELS,
    RECOMMENDATION,
    SEED,
    SUBGROUP_COLUMNS,
)
from src.domain.educacion.puertos import (
    AgrupadorEstudiantes,
    Bitacora,
    EntrenadorRiesgo,
    FuenteEstudiantes,
    GraficadorGrupos,
)
from src.domain.educacion.reglas import choose_k


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


def run_task_a(
    fuente: FuenteEstudiantes,
    agrupador: AgrupadorEstudiantes,
    graficador: GraficadorGrupos,
    bitacora: Bitacora,
) -> dict[str, object]:
    """Ejecuta la Tarea A completa y registra los resultados en la bitácora."""
    bitacora.info("=== Tarea A — K-means (Issue #5) ===")
    bitacora.info(f"Variables de agrupamiento: {', '.join(CLUSTER_FEATURES)}")
    bitacora.info("(G2 no disponible en el momento de predicción; G3 es solo la etiqueta)")

    df = fuente.leer()
    features = select_cluster_features(df)
    k_values, inertias, silhouettes = agrupador.diagnosticos(features)
    best_k = choose_k(k_values, silhouettes)

    bitacora.info(f"\n{'k':>3} | {'inercia':>12} | {'silueta':>8}")
    for k, inertia, score in zip(k_values, inertias, silhouettes, strict=True):
        bitacora.info(f"{k:>3} | {inertia:>12.1f} | {score:>8.4f}")
    bitacora.info(f"k elegido (codo + mayor silueta): {best_k}")

    labels = agrupador.agrupar(features, best_k)
    bitacora.info("\nGrupos descritos en lenguaje educativo (agregados, sin datos individuales):")
    descriptions = describe_groups(features, labels)
    for group, text in descriptions.items():
        bitacora.info(f"  Grupo {group}: {text}")

    bitacora.info(
        "\nProporción de desaprobados por grupo (solo interpretación, calculada tras agrupar):"
    )
    rates = failing_rates_by_group(df, labels)
    for group, rate in rates.items():
        bitacora.info(f"  Grupo {group}: {rate:.1%}")

    graficador.mostrar_codo_silueta(k_values, inertias, silhouettes)

    return {
        "k_values": k_values,
        "inertias": inertias,
        "silhouettes": silhouettes,
        "best_k": best_k,
        "labels": labels,
        "descriptions": descriptions,
        "failing_rates": rates,
    }


def run_task_b(
    fuente: FuenteEstudiantes,
    entrenador: EntrenadorRiesgo,
    bitacora: Bitacora,
) -> dict[str, object]:
    """Ejecuta la Tarea B completa y registra la tabla comparativa en la bitácora."""
    bitacora.info("=== Tarea B — Clasificación supervisada (Issue #5) ===")
    bitacora.info("Momento de predicción: inicio del curso (G1 + contexto); G2 y G3 excluidas.")
    bitacora.info(f"Variables ({len(MODEL_FEATURES)}): {', '.join(MODEL_FEATURES)}")

    df = fuente.leer()
    x_train, x_test, y_train, y_test = split_train_test(df)
    bitacora.info(
        f"\nSplit 80/20 estratificado ANTES de transformar (random_state={SEED}): "
        f"train={len(x_train)}, test={len(x_test)}"
    )
    bitacora.info(
        f"Desaprobados: train {int(y_train.sum())} ({y_train.mean():.1%}), "
        f"test {int(y_test.sum())} ({y_test.mean():.1%})"
    )

    metrics: dict[str, dict[str, object]] = {
        "baseline": evaluate_predictions(y_test, baseline_predictions(y_train, len(x_test))),
    }

    models = entrenador.entrenar(x_train, y_train)
    for name, model in models.items():
        metrics[name] = evaluate_predictions(y_test, model.predict(x_test))

    registrar_tabla_modelos(bitacora, metrics)

    best = pick_best_model(metrics)
    beats_baseline = float(metrics[best]["recall"]) > float(metrics["baseline"]["recall"])
    bitacora.info(f"\nMejor modelo (mayor F1 de desaprobado): {best}")
    bitacora.info(
        f"Checklist: ¿supera a la línea base en recall de desaprobados? "
        f"{'Sí' if beats_baseline else 'NO'} "
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
        "models": models,
        "split": {"x_train": x_train, "x_test": x_test, "y_train": y_train, "y_test": y_test},
    }


def registrar_tabla_modelos(bitacora: Bitacora, metrics: dict[str, dict[str, object]]) -> None:
    """Registra la tabla comparativa y la matriz de confusión de cada modelo."""
    bitacora.info(
        f"\n{'Modelo':<22} | {'Accuracy':>8} | {'Precisión':>9} | {'Recall':>6} | {'F1':>6}"
    )
    for key, label in MODEL_LABELS:
        model_metrics = metrics[key]
        bitacora.info(
            f"{label:<22} | {float(model_metrics['accuracy']):>8.3f} |"
            f" {float(model_metrics['precision']):>9.3f} |"
            f" {float(model_metrics['recall']):>6.3f} | {float(model_metrics['f1']):>6.3f}"
        )

    bitacora.info("\nMatriz de confusión por modelo (0 = aprobado, 1 = desaprobado):")
    for key, label in MODEL_LABELS:
        (tn, fp), (fn, tp) = metrics[key]["confusion_matrix"]
        bitacora.info(f"  {label:<22}: TN={tn} FP={fp} FN={fn} TP={tp}")


def run_task_c(
    fuente: FuenteEstudiantes,
    entrenador: EntrenadorRiesgo,
    bitacora: Bitacora,
) -> dict[str, object]:
    """Ejecuta la Tarea C: equidad por subgrupo, causas y recomendación de uso."""
    bitacora.info("=== Tarea C — Equidad y análisis de errores (Issue #5) ===")

    df = fuente.leer()
    x_train, x_test, y_train, y_test = split_train_test(df)
    models = entrenador.entrenar(x_train, y_train)
    metrics = {
        name: evaluate_predictions(y_test, model.predict(x_test)) for name, model in models.items()
    }
    best = pick_best_model(metrics)
    bitacora.info(f"Modelo evaluado: {best} (mejor F1 de desaprobado en la Tarea B)")
    bitacora.info(f"Subgrupos exigidos por el issue: {', '.join(SUBGROUP_COLUMNS)}")

    predictions = models[best].predict(x_test)
    fairness = {
        column: subgroup_metrics(y_test, predictions, x_test[column]) for column in SUBGROUP_COLUMNS
    }
    for column, table in fairness.items():
        bitacora.info(f"\nRecall y precisión por '{column}' (clase positiva = desaprobado):")
        bitacora.info(table.to_string(index=False))

    analysis = analyze_fairness(fairness)
    bitacora.info(f"\nBrechas (diferencia relevante desde {FAIRNESS_GAP_THRESHOLD:.0%}):")
    for column, info in analysis.items():
        state = "RELEVANTE" if info["relevant"] else "sin diferencia relevante"
        bitacora.info(
            f"  {column}: recall {float(info['recall_gap']):.3f}, "
            f"precisión {float(info['precision_gap']):.3f} -> {state}"
        )
        if info["relevant"]:
            for cause in info["causes"]:
                bitacora.info(f"    causa posible: {cause}")

    bitacora.info(
        "\nRecomendación de uso (Tarea C.3) — el modelo sirve para acompañar, no para sancionar:"
    )
    for line in RECOMMENDATION:
        bitacora.info(f"  {line}")

    return {
        "best_model": best,
        "fairness": fairness,
        "analysis": analysis,
        "recommendation": RECOMMENDATION,
    }


def run_conclusion(bitacora: Bitacora) -> tuple[str, ...]:
    """Registra la conclusión de una página al final del módulo (entregable final)."""
    bitacora.info("\n=== Conclusión — Issue #5 ===")
    for paragraph in CONCLUSION:
        bitacora.info(paragraph)
        bitacora.info("")
    return CONCLUSION
