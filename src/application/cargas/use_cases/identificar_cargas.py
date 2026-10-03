"""src/application/cargas/use_cases/identificar_cargas.py — Caso de uso: qué cargas hay detrás del consumo total."""

from src.application.cargas.dtos.identificar_cargas import (
    CargaResponse,
    IdentificarCargasRequest,
    IdentificarCargasResponse,
)
from src.domain.cargas.repositories import AgrupadorEventos, Bitacora, MedicionRepository
from src.domain.cargas.services import detectar_eventos, resumir_cargas


class IdentificarCargasUseCase:
    def __init__(
        self, mediciones: MedicionRepository, agrupador: AgrupadorEventos, umbral_kw: float, logger: Bitacora
    ) -> None:
        self._logger = logger
        self._mediciones = mediciones
        self._agrupador = agrupador
        self._umbral_kw = umbral_kw

    def execute(self, request: IdentificarCargasRequest) -> IdentificarCargasResponse:
        self._logger.info("Paso 1/4 · Leyendo mediciones de %s (%s → %s)", request.medidor, request.desde, request.hasta)
        serie = self._mediciones.listar(request.medidor, request.desde, request.hasta)
        if not serie:
            self._logger.warning("%s no tiene mediciones en el rango pedido", request.medidor)

        self._logger.info("Paso 2/4 · Detectando saltos de potencia |ΔP| >= %s kW", self._umbral_kw)
        eventos = detectar_eventos(serie, self._umbral_kw)
        self._logger.info("%d eventos detectados en %d mediciones", len(eventos), len(serie))
        if serie and not eventos:
            self._logger.warning("Ningún salto supera %s kW: probá con un umbral más bajo", self._umbral_kw)

        self._logger.info("Paso 3/4 · Agrupando eventos por magnitud")
        etiquetas = self._agrupador.agrupar(eventos) if eventos else []

        self._logger.info("Paso 4/4 · Resumiendo cargas")
        cargas = resumir_cargas(eventos, etiquetas)
        for c in cargas:
            self._logger.info("Carga de ~%s kW: %d encendidos, %d apagados", c.potencia_tipica_kw, c.encendidos, c.apagados)
        if eventos and not cargas:
            self._logger.warning("Hubo eventos pero ningún grupo alcanzó el mínimo para ser una carga")
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
