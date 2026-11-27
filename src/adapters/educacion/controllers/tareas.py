"""src/adapters/educacion/controllers/tareas.py — Punto de entrada: corre A, B, C y conclusión."""

from __future__ import annotations

from src.application.educacion.tareas import (
    run_conclusion,
    run_task_a,
    run_task_b,
    run_task_c,
)
from src.domain.educacion.puertos import (
    AgrupadorEstudiantes,
    Bitacora,
    EntrenadorRiesgo,
    FuenteEstudiantes,
    GraficadorGrupos,
)


def ejecutar_tareas(
    fuente: FuenteEstudiantes,
    agrupador: AgrupadorEstudiantes,
    entrenador: EntrenadorRiesgo,
    graficador: GraficadorGrupos,
    bitacora: Bitacora,
) -> dict[str, object]:
    """Corre las Tareas A, B y C y la conclusión en orden; devuelve cada resultado."""
    resultados: dict[str, object] = {}
    resultados["tarea_a"] = run_task_a(fuente, agrupador, graficador, bitacora)
    resultados["tarea_b"] = run_task_b(fuente, entrenador, bitacora)
    resultados["tarea_c"] = run_task_c(fuente, entrenador, bitacora)
    resultados["conclusion"] = run_conclusion(bitacora)
    return resultados
