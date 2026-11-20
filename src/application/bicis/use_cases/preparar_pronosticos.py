"""src/application/bicis/use_cases/preparar_pronosticos.py — Prepara muestras cronológicas."""

from datetime import date, timedelta

from src.application.bicis.dtos.pronostico import (
    MuestraPronostico,
    ResultadoPreparacionPronosticos,
)
from src.domain.bicis.modelos import SerieDiariaViajes
from src.domain.bicis.reglas import construir_variables_pronostico
from src.domain.bicis.repositorios import RepositorioSerieDiaria


class PrepararPronosticosUseCase:
    """Prepara filas de evaluación sin usar datos del objetivo como variables de entrada."""

    def __init__(self, repositorio: RepositorioSerieDiaria) -> None:
        self._repositorio = repositorio

    def execute(
        self, desde: date, hasta: date
    ) -> ResultadoPreparacionPronosticos:
        """Obtiene el período más siete días previos y prepara sus muestras disponibles."""
        if desde > hasta:
            raise ValueError("La fecha inicial no puede ser posterior a la fecha final.")

        serie = self._repositorio.obtener(desde - timedelta(days=7), hasta)
        return self._preparar(serie, desde, hasta)

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
