"""src/application/cargas/use_cases/identificar_cargas.py — Caso de uso: qué cargas hay detrás del consumo total."""

from src.application.cargas.dtos.identificar_cargas import (
    CargaResponse,
    IdentificarCargasRequest,
    IdentificarCargasResponse,
)
from src.domain.cargas.repositories import AgrupadorEventos, MedicionRepository
from src.domain.cargas.services import detectar_eventos, resumir_cargas


class IdentificarCargasUseCase:
    def __init__(self, mediciones: MedicionRepository, agrupador: AgrupadorEventos, umbral_kw: float) -> None:
        self._mediciones = mediciones
        self._agrupador = agrupador
        self._umbral_kw = umbral_kw

    def execute(self, request: IdentificarCargasRequest) -> IdentificarCargasResponse:
        serie = self._mediciones.listar(request.medidor, request.desde, request.hasta)
        eventos = detectar_eventos(serie, self._umbral_kw)
        etiquetas = self._agrupador.agrupar(eventos) if eventos else []
        cargas = resumir_cargas(eventos, etiquetas)
        media = sum(m.potencia_kw for m in serie) / len(serie) if serie else 0.0
        return IdentificarCargasResponse(
            medidor=request.medidor,
            mediciones=len(serie),
            eventos=len(eventos),
            potencia_media_kw=round(media, 1),
            cargas=[
                CargaResponse(
                    potencia_tipica_kw=c.potencia_tipica_kw, encendidos=c.encendidos, apagados=c.apagados, ciclos=c.ciclos
                )
                for c in cargas
            ],
        )
