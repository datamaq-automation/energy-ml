"""src/adapters/logistica/presenters/retrasos_presenter.py — Respuesta → líneas de reporte."""

from __future__ import annotations

from src.application.logistica.dtos.analizar_retrasos_response import AnalizarRetrasosResponse


class RetrasosPresenter:
    """Formatea los resultados de las Tareas A, B y C como texto para consola o log."""

    def presentar(self, respuesta: AnalizarRetrasosResponse) -> list[str]:
        """Devuelve una línea por grupo, modelo, variable importante y segmento."""
        lineas = [f"Informe {respuesta.id_informe}: {respuesta.pedidos} pedidos"]
        lineas += [
            f"Cluster {p.cluster_id} ({p.order_count} pedidos): {p.business_description} "
            f"| retraso={p.late_delivery_rate * 100:.1f}%"
            for p in respuesta.perfiles
        ]
        lineas += [
            f"{m.model_name} -> Acc={m.accuracy:.4f} | Prec={m.precision:.4f} "
            f"| Rec={m.recall:.4f} | F1={m.f1:.4f} | CM={m.confusion_matrix}"
            for m in respuesta.modelos
        ]
        lineas += [
            f"Importancia variable: {nombre} = {peso:.4f}"
            for nombre, peso in respuesta.importancias
        ]
        lineas += [
            f"Tarea C [{s.segment_type}={s.segment_value}] ({s.order_count} pedidos): "
            f"retraso_real={s.actual_late_rate * 100:.2f}% | recall={s.recall * 100:.2f}%"
            for s in respuesta.segmentos
        ]
        lineas += respuesta.eventos
        lineas.append(f"Gráficos: {', '.join(respuesta.graficos)}")
        return lineas
