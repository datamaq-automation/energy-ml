"""src/application/cargas/use_cases/explicar_arbol.py — Caso de uso para explicabilidad del árbol CART."""

from src.application.cargas.dtos.explicabilidad import ExplicarArbolResponse
from src.domain.cargas.repositories import ClasificadorSaltos


class ExplicarArbolUseCase:
    """Extrae explicabilidad del árbol de decisión CART entrenado."""

    def __init__(self, clasificador: ClasificadorSaltos) -> None:
        self._clasificador = clasificador

    def execute(self) -> ExplicarArbolResponse:
        """Serializa el árbol del clasificador a JSON estructurado."""
        arbol_dict = self._clasificador.obtener_arbol_dict()

        return ExplicarArbolResponse(
            tipo=arbol_dict["tipo"],
            rasgos=arbol_dict["rasgos"],
            clases=arbol_dict["clases"],
            profundidad=arbol_dict["profundidad"],
            hojas=arbol_dict["hojas"],
            raiz=arbol_dict["raiz"],
        )
