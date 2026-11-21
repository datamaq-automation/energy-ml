"""educacion/fail_risk.py — Tareas A, B y C del Issue #5: agrupamiento, predicción y equidad.

Caso de estudio: "Riesgo de desaprobar una materia: agrupamiento, predicción y equidad".

Momento de predicción declarado en educacion/README.md: inicio del curso,
solo G1 + variables de contexto. Por eso G2 NO entra en ninguna tarea y G3
se usa exclusivamente como etiqueta (nunca como variable de entrada).

El código vive en las cuatro capas de src/ (domain, application, adapters e
infrastructure); este módulo es solo el punto de entrada que arma las piezas
y corre las cuatro partes en orden.

Ejecución (desde la raíz del repositorio):  python -m educacion.fail_risk
"""

from __future__ import annotations

from src.adapters.educacion.controllers.tareas import ejecutar_tareas
from src.adapters.educacion.gateways.estudiantes_csv import EstudiantesCsv
from src.infrastructure.graficos.educacion import MatplotlibGraficador
from src.infrastructure.settings.logger import logger
from src.infrastructure.sklearn.educacion_agrupador import KMeansAgrupadorEstudiantes
from src.infrastructure.sklearn.educacion_modelos import SklearnEntrenadorRiesgo


def main() -> None:
    """Arma las piezas y ejecuta la Tarea A, la Tarea B, la Tarea C y la conclusión."""
    ejecutar_tareas(
        fuente=EstudiantesCsv(),
        agrupador=KMeansAgrupadorEstudiantes(),
        entrenador=SklearnEntrenadorRiesgo(),
        graficador=MatplotlibGraficador(),
        bitacora=logger,
    )


if __name__ == "__main__":
    main()
