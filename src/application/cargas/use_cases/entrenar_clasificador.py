"""src/application/cargas/use_cases/entrenar_clasificador.py — Caso de uso: aprender las cargas a partir de la verdad."""

from datetime import datetime

from src.domain.cargas.entities import MatrizConfusion
from src.domain.cargas.repositories import (
    Bitacora,
    ClasificadorSaltos,
    MedicionRepository,
    VerdadRepository,
)
from src.domain.cargas.supervisado import NINGUNA, armar_saltos, etiquetar, matriz_confusion

TODO_EL_RANGO = (datetime(2000, 1, 1), datetime(2100, 1, 1))


class EntrenarClasificadorUseCase:
    """Entrena con los primeros días de un medidor simulado y evalúa con los últimos.

    El corte es en el tiempo, no al azar: así se simula lo que pasaría en una planta, donde
    se etiqueta un período y el modelo se usa después, con días que nunca vio.
    """

    def __init__(
        self,
        mediciones: MedicionRepository,
        verdad: VerdadRepository,
        clasificador: ClasificadorSaltos,
        logger: Bitacora,
    ) -> None:
        self._mediciones = mediciones
        self._verdad = verdad
        self._clasificador = clasificador
        self._logger = logger

    def execute(self, medidor: str, fraccion_entrenamiento: float = 0.7) -> MatrizConfusion:
        if not 0 < fraccion_entrenamiento < 1:
            raise ValueError("La fracción de entrenamiento tiene que estar entre 0 y 1.")
        saltos = armar_saltos(self._mediciones.listar(medidor, *TODO_EL_RANGO))
        etiquetas = etiquetar(saltos, self._verdad.listar(medidor))
        corte = round(len(saltos) * fraccion_entrenamiento)
        if corte == 0 or corte == len(saltos):
            raise ValueError(
                f"Hay muy pocos datos en {medidor} para separar entrenamiento y prueba."
            )
        self._logger.info(
            "%s: %d saltos (%d con carga). Entrena hasta %s (%d) y prueba desde ahí (%d)",
            medidor, len(saltos), sum(e != NINGUNA for e in etiquetas),
            saltos[corte].instante, corte, len(saltos) - corte,
        )  # fmt: skip
        self._clasificador.entrenar(saltos[:corte], etiquetas[:corte])
        self._logger.info("Reglas que aprendió:\n%s", self._clasificador.explicar())
        matriz = matriz_confusion(etiquetas[corte:], self._clasificador.predecir(saltos[corte:]))
        self._informar(matriz)
        return matriz

    def _informar(self, matriz: MatrizConfusion) -> None:
        titulo = "real \\ predicha"
        ancho, primera = max(len(c) for c in matriz.clases) + 2, len(titulo) + 2
        filas = [titulo.ljust(primera) + "".join(c.rjust(ancho) for c in matriz.clases)]
        filas += [
            r.ljust(primera) + "".join(str(matriz.celdas[r][p]).rjust(ancho) for p in matriz.clases)
            for r in matriz.clases
        ]
        self._logger.info("Matriz de confusión en los días de prueba:\n%s", "\n".join(filas))
        for clase in matriz.clases:
            self._logger.info(
                "%s: sensibilidad %.0f %%, precisión %.0f %%",
                clase, 100 * matriz.sensibilidad(clase), 100 * matriz.precision(clase),
            )  # fmt: skip
        self._logger.info("Exactitud: %.1f %% de %d saltos", 100 * matriz.exactitud, matriz.total)
