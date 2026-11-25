"""src/adapters/medioambiente/presenters/episodios_co_presenter.py — Respuesta → líneas de reporte."""

from __future__ import annotations

from src.application.medioambiente.dtos.analizar_episodios_response import (
    AnalizarEpisodiosResponse,
)

SEPARADOR = "=" * 72


class EpisodiosCOPresenter:
    """Formatea los resultados de las Tareas A, B y C como texto para consola o log."""

    def presentar(self, respuesta: AnalizarEpisodiosResponse) -> list[str]:
        """Devuelve una línea por dato relevante, en el orden A → B → C."""
        lineas = [SEPARADOR, f"Informe {respuesta.id_informe}: {respuesta.filas_cargadas} filas"]
        lineas.append("TAREA A — K-means sobre meteorología (sin etiqueta)")
        lineas += [
            f"  k={d.k}  inercia={d.inercia:.3f}  silueta={d.silueta:.3f}"
            for d in respuesta.diagnosticos
        ]
        lineas.append(f"Mejor k por silueta: {respuesta.mejor_k}")
        lineas += [
            f"  grupo {g.grupo}: {g.horas} h, T={g.temperatura_media:.2f}, "
            f"RH={g.humedad_relativa_media:.2f}, AH={g.humedad_absoluta_media:.2f}, "
            f"episodios={g.proporcion_episodio:.3f}"
            for g in respuesta.grupos
        ]
        lineas.append("TAREAS B y C — Métricas por split (clase 'episodio')")
        lineas += [
            f"  {m.split:<9} {m.modelo:<20} acc={m.accuracy:.3f} prec={m.precision:.3f} "
            f"rec={m.recall:.3f} f1={m.f1:.3f}"
            for m in respuesta.metricas
        ]
        lineas.append(
            f"Matriz de confusión de {respuesta.mejor_modelo} sobre test temporal "
            f"[[TN, FP], [FN, TP]]: {respuesta.matriz_confusion}"
        )
        lineas.append(f"Features con cambio de distribución: {respuesta.features_con_cambio}")
        lineas += respuesta.eventos
        lineas.append(f"Gráficos: {', '.join(respuesta.graficos)}")
        return lineas
