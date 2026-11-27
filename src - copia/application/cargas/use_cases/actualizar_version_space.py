"""src/application/cargas/use_cases/actualizar_version_space.py — Caso de uso para Version Space Learning."""

from datetime import datetime

from src.application.cargas.dtos.version_space import (
    EstadoVersionSpaceResponse,
    HipotesisDTO,
    PasoVersionSpaceRequest,
    RestriccionDTO,
)
from src.domain.cargas.entities import Salto
from src.domain.cargas.espacio_versiones import Hipotesis
from src.domain.cargas.version_space_learner import VersionSpaceLearner


class ActualizarVersionSpaceUseCase:
    """Ejecuta un paso del algoritmo de aprendizaje por espacio de versiones."""

    def __init__(self) -> None:
        self._learner = VersionSpaceLearner(["ΔP", "ΔP_previo", "ΔP_siguiente"])

    def execute(self, request: PasoVersionSpaceRequest) -> EstadoVersionSpaceResponse:
        """Actualiza el espacio con un nuevo ejemplo y retorna el estado."""
        salto = Salto(
            instante=datetime.now(),
            delta_kw=request.delta_kw,
            delta_previo_kw=request.delta_previo_kw,
            delta_siguiente_kw=request.delta_siguiente_kw,
        )

        self._learner.actualizar(salto, request.etiqueta)
        estado = self._learner.obtener_estado()

        frontera_s = [self._hipotesis_a_dto(h) for h in estado.S]
        frontera_g = [self._hipotesis_a_dto(h) for h in estado.G]

        return EstadoVersionSpaceResponse(
            numero_ejemplos=estado.numero_ejemplos,
            frontera_s=frontera_s,
            frontera_g=frontera_g,
            es_consistente=estado.es_consistente(),
            tamano_espacio=self._estimar_tamano_espacio(estado.S, estado.G),
        )

    def _hipotesis_a_dto(self, h: Hipotesis) -> HipotesisDTO:
        """Serializa una hipótesis a DTO."""
        restricciones_dto = {
            rasgo: RestriccionDTO(
                rasgo=restriccion.rasgo,
                minimo=restriccion.minimo,
                maximo=restriccion.maximo,
            )
            for rasgo, restriccion in h.restricciones.items()
        }
        return HipotesisDTO(
            restricciones=restricciones_dto,
            es_universo=h.es_universo(),
            es_vacia=h.es_vacio(),
        )

    def _estimar_tamano_espacio(self, S: set[Hipotesis], G: set[Hipotesis]) -> int:
        """Estima la cantidad de hipótesis en el espacio (aproximación)."""
        if not S or not G:
            return len(S) + len(G)
        return max(1, len(S) * len(G))
