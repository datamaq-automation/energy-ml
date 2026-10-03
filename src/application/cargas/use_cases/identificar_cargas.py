"""src/application/cargas/use_cases/identificar_cargas.py — Caso de uso: qué cargas hay detrás del consumo total."""

from src.application.cargas.dtos.identificar_cargas import (
    CargaResponse,
    IdentificarCargasRequest,
    IdentificarCargasResponse,
)
from src.domain.cargas.entities import Carga, EventoCarga, Medicion
from src.domain.cargas.repositories import AgrupadorEventos, Bitacora, MedicionRepository
from src.domain.cargas.services import detectar_eventos, resumir_cargas


class IdentificarCargasUseCase:
    def __init__(
        self,
        mediciones: MedicionRepository,
        agrupador: AgrupadorEventos,
        umbral_kw: float,
        logger: Bitacora,
        balance_minimo: float = 0.5,
    ) -> None:
        self._balance_minimo = balance_minimo
        self._logger = logger
        self._mediciones = mediciones
        self._agrupador = agrupador
        self._umbral_kw = umbral_kw

    def execute(self, request: IdentificarCargasRequest) -> IdentificarCargasResponse:
        serie = self._leer(request)
        eventos = self._detectar(serie)
        self._logger.info("Paso 3/4 · Agrupando eventos por magnitud")
        etiquetas = self._agrupador.agrupar(eventos) if eventos else []
        cargas = self._resumir(serie, eventos, etiquetas)
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

    def _leer(self, request: IdentificarCargasRequest) -> list[Medicion]:
        self._logger.info("Paso 1/4 · Leyendo mediciones de %s (%s → %s)", request.medidor, request.desde, request.hasta)
        serie = self._mediciones.listar(request.medidor, request.desde, request.hasta)
        if serie:
            media = sum(m.potencia_kw for m in serie) / len(serie)
            self._logger.info("Potencia media del medidor: %.0f kW (para comparar con las cargas)", media)
        else:
            self._logger.warning("%s no tiene mediciones en el rango pedido", request.medidor)
        return serie

    def _detectar(self, serie: list[Medicion]) -> list[EventoCarga]:
        self._logger.info("Paso 2/4 · Detectando saltos de potencia |ΔP| >= %s kW", self._umbral_kw)
        eventos = detectar_eventos(serie, self._umbral_kw)
        encendidos = sum(e.es_encendido for e in eventos)
        self._logger.info(
            "%d eventos detectados en %d mediciones (%d ↑ encendidos, %d ↓ apagados)",
            len(eventos), len(serie), encendidos, len(eventos) - encendidos,
        )  # fmt: skip
        if serie and not eventos:
            self._logger.warning("Ningún salto supera %s kW: probá con un umbral más bajo", self._umbral_kw)
        return eventos

    def _resumir(self, serie: list[Medicion], eventos: list[EventoCarga], etiquetas: list[int]) -> list[Carga]:
        self._logger.info("Paso 4/4 · Resumiendo cargas")
        cargas = resumir_cargas(eventos, etiquetas)
        dias = (max(m.instante for m in serie) - min(m.instante for m in serie)).total_seconds() / 86400 if serie else 0
        for c in cargas:
            por_dia = ""
            if dias >= 1:
                frecuencia = c.ciclos / dias
                por_dia = f" (≈{frecuencia:.0f}/día)" if frecuencia >= 1 else f" (≈{frecuencia * 7:.1f}/semana)"
            self._logger.info(
                "Carga de ~%s kW: %d ↑ encendidos, %d ↓ apagados, %d ciclos%s",
                c.potencia_tipica_kw, c.encendidos, c.apagados, c.ciclos, por_dia,
            )  # fmt: skip
            if not c.es_on_off(self._balance_minimo):
                self._logger.warning(
                    "~%s kW tiene %d ↑ y %d ↓: probablemente no es una sola carga ON/OFF",
                    c.potencia_tipica_kw, c.encendidos, c.apagados,
                )  # fmt: skip
        if eventos and not cargas:
            self._logger.warning("Hubo eventos pero ningún grupo alcanzó el mínimo para ser una carga")
        return cargas
