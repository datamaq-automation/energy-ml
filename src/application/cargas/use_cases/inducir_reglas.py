"""src/application/cargas/use_cases/inducir_reglas.py — Caso de uso para inducción de reglas."""

from src.application.cargas.dtos.reglas import (
    CondicionDTO,
    InducirReglasResponse,
    ObtenerReglaResponse,
    ReglaDTO,
)
from src.domain.cargas.repositories import ClasificadorSaltos


class InducirReglasUseCase:
    """Induce reglas a partir del árbol CART entrenado."""

    def __init__(self, clasificador: ClasificadorSaltos) -> None:
        self._clasificador = clasificador

    def execute(self) -> InducirReglasResponse:
        """Extrae todas las reglas del árbol y retorna el conjunto."""
        reglas_dict = self._clasificador.obtener_reglas_dict()

        reglas_dto = [
            ReglaDTO(
                id_regla=r["id_regla"],
                condiciones=[
                    CondicionDTO(
                        rasgo=c["rasgo"],
                        operador=c["operador"],
                        valor=c["valor"],
                    )
                    for c in r["condiciones"]
                ],
                clase_predicha=r["clase_predicha"],
                soporte=r["soporte"],
                confianza=r["confianza"],
                texto=r["texto"],
            )
            for r in reglas_dict["reglas"]
        ]

        return InducirReglasResponse(
            reglas=reglas_dto,
            numero_reglas=reglas_dict["numero_reglas"],
            numero_ejemplos=0,
            cobertura_total=reglas_dict["cobertura_total"],
        )


class ObtenerReglaUseCase:
    """Obtiene el detalle de una regla específica."""

    def __init__(self, clasificador: ClasificadorSaltos) -> None:
        self._clasificador = clasificador
        self._reglas_dict_cache: dict | None = None

    def execute(self, id_regla: str) -> ObtenerReglaResponse:
        """Retorna el detalle de una regla específica."""
        if self._reglas_dict_cache is None:
            self._reglas_dict_cache = self._clasificador.obtener_reglas_dict()

        reglas_dict = self._reglas_dict_cache
        regla_dict = next((r for r in reglas_dict["reglas"] if r["id_regla"] == id_regla), None)

        if not regla_dict:
            raise ValueError(f"Regla no encontrada: {id_regla}")

        condiciones_dto = [
            CondicionDTO(
                rasgo=c["rasgo"],
                operador=c["operador"],
                valor=c["valor"],
            )
            for c in regla_dict["condiciones"]
        ]

        regla_dto = ReglaDTO(
            id_regla=regla_dict["id_regla"],
            condiciones=condiciones_dto,
            clase_predicha=regla_dict["clase_predicha"],
            soporte=regla_dict["soporte"],
            confianza=regla_dict["confianza"],
            texto=regla_dict["texto"],
        )

        ejemplos_positivos = int(regla_dict["soporte"] * regla_dict["confianza"])

        return ObtenerReglaResponse(
            regla=regla_dto,
            ejemplos_cubiertos=regla_dict["soporte"],
            ejemplos_positivos=ejemplos_positivos,
            tasa_exito=regla_dict["confianza"],
        )
