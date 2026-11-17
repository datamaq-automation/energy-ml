"""src/infrastructure/cli/analizar_logistica.py — CLI para ejecutar las Tareas A, B y C de logística."""

from __future__ import annotations

import argparse
from pathlib import Path

from src.infrastructure.settings.logger import logger
from src.infrastructure.sklearn.logistics_pipeline import (
    load_and_prepare_orders,
    run_task_a_clustering,
    run_task_b_supervised,
    run_task_c_error_analysis,
    save_confusion_matrix_plot,
    save_elbow_and_silhouette_plot,
    split_and_preprocess,
)


def parse_args() -> argparse.Namespace:
    """Lee argumentos de línea de comandos para el análisis de logística."""
    parser = argparse.ArgumentParser(
        description="Ejecuta el análisis no supervisado (Tarea A), supervisado (Tarea B) y de errores (Tarea C)."
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("datos/logistica/pedidos.csv"),
        help="Ruta relativa al archivo CSV de pedidos.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/output"),
        help="Directorio donde se guardarán los gráficos generados.",
    )
    parser.add_argument(
        "--best-k",
        type=int,
        default=5,
        help="Número de clusters k elegido para perfilar en Tarea A.",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=5,
        help="Profundidad máxima del árbol de decisión en Tarea B.",
    )
    return parser.parse_args()


def main() -> None:
    """Punto de entrada principal del análisis de retrasos logísticos."""
    args = parse_args()
    if not args.csv.exists():
        logger.error("No se encontró el dataset en %s", args.csv)
        return

    logger.info("Cargando y validando pedidos desde %s (cero fuga de datos)...", args.csv)
    df = load_and_prepare_orders(args.csv)
    logger.info("Pedidos cargados: %d filas, %d columnas seguras.", len(df), len(df.columns))

    metrics_a, profiles_a = run_task_a_clustering(df, best_k=args.best_k)
    elbow_path = args.output_dir / "logistica_elbow_silhouette.png"
    save_elbow_and_silhouette_plot(metrics_a, best_k=args.best_k, output_path=elbow_path)
    logger.info("Gráfico de codo y silueta guardado en %s", elbow_path)

    for profile in profiles_a:
        logger.info(
            "Cluster %d (%d pedidos): %s | retraso=%.1f%%",
            profile.cluster_id,
            profile.order_count,
            profile.business_description,
            profile.late_delivery_rate * 100,
        )

    x_train, x_test, y_train, y_test, feat_names, x_test_df = split_and_preprocess(df)
    models_b, top_features, best_preds = run_task_b_supervised(
        x_train, x_test, y_train, y_test, feat_names, tree_max_depth=args.max_depth
    )

    for m in models_b:
        logger.info(
            "%s -> Acc=%.4f | Prec=%.4f | Rec=%.4f | F1=%.4f | CM=%s",
            m.model_name,
            m.accuracy,
            m.precision,
            m.recall,
            m.f1,
            m.confusion_matrix,
        )

    cm_path = args.output_dir / "logistica_confusion_matrix.png"
    save_confusion_matrix_plot(models_b[-1], output_path=cm_path)
    logger.info("Matriz de confusión guardada en %s", cm_path)

    for fname, weight in top_features[:5]:
        logger.info("Importancia variable: %s = %.4f", fname, weight)

    segments_mode = run_task_c_error_analysis(
        x_test_df, y_test, best_preds, segment_col="Shipping Mode"
    )
    for seg in segments_mode:
        logger.info(
            "Tarea C [%s=%s] (%d pedidos): retraso_real=%.2f%% | recall=%.2f%%",
            seg.segment_type,
            seg.segment_value,
            seg.order_count,
            seg.actual_late_rate * 100,
            seg.recall * 100,
        )


if __name__ == "__main__":
    main()
