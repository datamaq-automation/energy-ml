"""src/adapters/residuos/presenters/residuos_presenter.py — Respuesta → líneas de reporte."""

from __future__ import annotations

from src.application.residuos.dtos.pronosticar_residuos_response import (
    PronosticarResiduosResponse,
)
from src.domain.residuos.value_objects import HORIZONTE_COMPLETO, MODELOS


class ResiduosPresenter:
    """Formatea la validación y los pronósticos como texto para consola o log."""

    def presentar(self, respuesta: PronosticarResiduosResponse) -> list[str]:
        """Serie, métricas del bloque completo y una línea por mes pronosticado."""
        lineas = [
            f"Serie: {respuesta.meses} meses, de {respuesta.primer_mes} a {respuesta.ultimo_mes}.",
            "Validación temporal (últimos 12 meses):",
        ]
        lineas += [
            f"  {m.modelo:<17} MAE={m.mae_toneladas:.2f}  RMSE={m.rmse_toneladas:.2f}  "
            f"n={m.predicciones_evaluadas}"
            for m in respuesta.metricas
            if m.horizonte == HORIZONTE_COMPLETO
        ]
        lineas.append("Pronósticos posteriores al último mes disponible:")
        por_mes: dict[str, dict[str, float]] = {}
        for p in respuesta.pronosticos:
            por_mes.setdefault(p.mes, {})[p.modelo] = p.toneladas
        for mes in sorted(por_mes):
            valores = "  ".join(f"{modelo}={por_mes[mes][modelo]:.2f}" for modelo in MODELOS)
            lineas.append(f"  {mes}  {valores}")
        lineas += respuesta.eventos
        if respuesta.archivos:
            lineas.append(f"Resultados guardados en: {', '.join(respuesta.archivos)}")
        return lineas
