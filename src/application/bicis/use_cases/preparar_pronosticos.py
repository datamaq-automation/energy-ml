"""src/application/bicis/use_cases/preparar_pronosticos.py — Prepara muestras cronológicas."""

from datetime import date, timedelta
from typing import overload

from src.application.bicis.dtos.preparar_pronosticos_request import (
    PrepararPronosticosRequest,
)
from src.application.bicis.dtos.preparar_pronosticos_response import (
    PrepararPronosticosResponse,
)
from src.application.bicis.mappers.preparacion_pronosticos_mapper import (
    PreparacionPronosticosMapper,
)
from src.domain.bicis.repositories import RepositorioSerieDiaria
from src.domain.bicis.services import construir_variables_pronostico, validar_periodo
from src.domain.bicis.value_objects import (
    MuestraPronostico,
    ResultadoPreparacionPronosticos,
    SerieDiariaViajes,
)


class PrepararPronosticosUseCase:
    """Prepara filas de evaluación sin usar datos del objetivo como variables de entrada."""

    def __init__(self, repositorio: RepositorioSerieDiaria) -> None:
        self._repositorio = repositorio

    @overload
    def execute(self, request: PrepararPronosticosRequest) -> PrepararPronosticosResponse: ...

    @overload
    def execute(self, request: date, hasta: date) -> PrepararPronosticosResponse: ...

    def execute(
        self, request: PrepararPronosticosRequest | date, hasta: date | None = None
    ) -> PrepararPronosticosResponse:
        """Obtiene el período más siete días previos y prepara sus muestras disponibles."""
        if isinstance(request, date):
            if hasta is None:
                raise TypeError("El intervalo requiere fecha inicial y final.")
            request = PrepararPronosticosRequest(desde=request, hasta=hasta)
        elif hasta is not None:
            raise TypeError("No se pasa una fecha final separada junto con el request.")

        validar_periodo(request.desde, request.hasta)
        serie = self._repositorio.obtener(request.desde - timedelta(days=7), request.hasta)
        resultado = self._preparar(serie, request.desde, request.hasta)
        return PreparacionPronosticosMapper.a_response(resultado)

    @staticmethod
    def _preparar(
        serie: SerieDiariaViajes, desde: date, hasta: date
    ) -> ResultadoPreparacionPronosticos:
        muestras: list[MuestraPronostico] = []
        dias_sin_rezagos: list[date] = []

        for dia in serie.dias:
            if not desde <= dia.fecha <= hasta:
                continue
            variables = construir_variables_pronostico(serie, dia.fecha)
            if variables is None:
                dias_sin_rezagos.append(dia.fecha)
                continue
            muestras.append(
                MuestraPronostico(
                    fecha_objetivo=dia.fecha,
                    variables=variables,
                    viajes_reales=dia.viajes,
                )
            )

        return ResultadoPreparacionPronosticos(
            muestras=tuple(muestras),
            dias_faltantes=serie.dias_faltantes(desde, hasta),
            dias_sin_rezagos=tuple(dias_sin_rezagos),
        )
