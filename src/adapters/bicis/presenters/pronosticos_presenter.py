"""src/adapters/bicis/presenters/pronosticos_presenter.py — Respuesta → líneas de reporte."""

from src.application.bicis.dtos.evaluar_pronosticos_response import EvaluarPronosticosResponse


class PronosticosPresenter:
    """Formatea métricas y cobertura para la salida de consola."""

    def presentar(self, respuesta: EvaluarPronosticosResponse) -> list[str]:
        """Devuelve el tamaño de las particiones, las métricas y los eventos."""
        lineas = [
            "Muestras: "
            f"{respuesta.dias_entrenamiento} días de entrenamiento (2024), "
            f"{respuesta.dias_prueba} de prueba (2025)",
            f"{'Método':<34s} {'MAE (viajes)':>12s} {'RMSE (viajes)':>12s}",
        ]
        for metrica in (respuesta.linea_base, respuesta.bosque_aleatorio):
            lineas.append(f"{metrica.nombre:<34s} {metrica.mae:12.2f} {metrica.rmse:12.2f}")
        for anio in (2024, 2025):
            faltantes = sum(fecha.year == anio for fecha in respuesta.dias_faltantes)
            sin_rezagos = sum(fecha.year == anio for fecha in respuesta.dias_sin_rezagos)
            lineas.append(
                f"{anio}: {faltantes} días sin registros, "
                f"{sin_rezagos} días observados sin rezagos completos"
            )
        lineas.extend(respuesta.eventos)
        return lineas
