"""src/application/cargas/use_cases/identificar_cargas.py — Caso de uso: qué cargas hay detrás del consumo total."""

from src.application.cargas.dtos.identificar_cargas import (
    BarraHistogramaResponse,
    CargaResponse,
    IdentificarCargasRequest,
    IdentificarCargasResponse,
    RadioResponse,
    UmbralResponse,
)
from src.domain.cargas.entities import Carga, EventoCarga, Medicion
from src.domain.cargas.repositories import AgrupadorEventos, Bitacora, MedicionRepository
from src.domain.cargas.services import (
    detectar_eventos,
    estimar_radio,
    estimar_umbral,
    histograma,
    nivel_de_ruido,
    resumir_cargas,
    saltos_kw,
)


class IdentificarCargasUseCase:
    def __init__(
        self,
        mediciones: MedicionRepository,
        agrupador: AgrupadorEventos,
        umbral_kw: float | None,
        logger: Bitacora,
        balance_minimo: float = 0.5,
        separacion_minima: float = 0.8,
        radio_kw: float | None = None,
    ) -> None:
        self._radio_kw = radio_kw
        self._separacion_minima = separacion_minima
        self._balance_minimo = balance_minimo
        self._logger = logger
        self._mediciones = mediciones
        self._agrupador = agrupador
        self._umbral_kw = umbral_kw

    def execute(self, request: IdentificarCargasRequest) -> IdentificarCargasResponse:
        serie = self._leer(request)
        umbral = self._elegir_umbral(serie)
        eventos = self._detectar(serie, umbral.kw)
        radio = self._elegir_radio(eventos, nivel_de_ruido(serie, umbral.kw) if umbral.kw else 0.0)
        etiquetas = self._agrupador.agrupar(eventos, radio.kw) if eventos and radio.kw else []
        cargas = self._resumir(serie, eventos, etiquetas)
        return self._responder(request.medidor, serie, eventos, etiquetas, cargas, umbral, radio)

    def _responder(
        self,
        medidor: str,
        serie: list[Medicion],
        eventos: list[EventoCarga],
        etiquetas: list[int],
        cargas: list[Carga],
        umbral: UmbralResponse,
        radio: RadioResponse,
    ) -> IdentificarCargasResponse:
        dias = _dias(serie)
        encendidos = sum(e.es_encendido for e in eventos)
        return IdentificarCargasResponse(
            medidor=medidor,
            mediciones=len(serie),
            eventos=len(eventos),
            encendidos=encendidos,
            apagados=len(eventos) - encendidos,
            eventos_sin_grupo=etiquetas.count(-1),
            dias=round(dias, 1),
            potencia_media_kw=round(sum(m.potencia_kw for m in serie) / len(serie), 1) if serie else 0.0,
            cargas=[
                CargaResponse(
                    potencia_tipica_kw=c.potencia_tipica_kw,
                    encendidos=c.encendidos,
                    apagados=c.apagados,
                    ciclos=c.ciclos,
                    ciclos_por_dia=round(c.ciclos / dias, 1) if dias >= 1 else None,
                    on_off=c.es_on_off(self._balance_minimo),
                )
                for c in cargas
            ],
            umbral=umbral,
            radio=radio,
            histograma=[
                BarraHistogramaResponse(desde_kw=b.desde_kw, hasta_kw=b.hasta_kw, cantidad=b.cantidad)
                for b in histograma(saltos_kw(serie))
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

    def _elegir_umbral(self, serie: list[Medicion]) -> UmbralResponse:
        self._logger.info("Paso 2/4 · Detectando saltos de potencia |ΔP|")
        if self._umbral_kw is not None:
            self._logger.info("Umbral fijo por configuración: %s kW", self._umbral_kw)
            return UmbralResponse(kw=self._umbral_kw, automatico=False)
        estimacion = estimar_umbral(serie)
        if estimacion is None:
            self._logger.warning("No hay suficientes mediciones para estimar el umbral automático")
            return UmbralResponse(kw=None, automatico=True)
        self._logger.info(
            "Umbral automático: %s kW (Otsu, separación ruido/eventos η=%.2f)",
            estimacion.umbral_kw, estimacion.separacion,
        )  # fmt: skip
        confiable = estimacion.es_confiable(self._separacion_minima)
        if not confiable:
            self._logger.warning(
                "No hay un valle claro entre ruido y eventos (η=%.2f < %.2f): el umbral es poco confiable",
                estimacion.separacion, self._separacion_minima,
            )  # fmt: skip
        return UmbralResponse(
            kw=estimacion.umbral_kw, automatico=True, separacion=estimacion.separacion, confiable=confiable
        )

    def _elegir_radio(self, eventos: list[EventoCarga], ruido_kw: float) -> RadioResponse:
        self._logger.info("Paso 3/4 · Agrupando eventos por magnitud (DBSCAN)")
        if self._radio_kw is not None:
            self._logger.info("Radio fijo por configuración: %s kW", self._radio_kw)
            return RadioResponse(kw=self._radio_kw, automatico=False)
        radio = estimar_radio(eventos, ruido_kw)
        if radio is not None:
            self._logger.info(
                "Radio automático: %s kW (mayor entre Freedman–Diaconis y 2 × ruido de la señal, ruido = %.1f kW)",
                radio, ruido_kw,
            )  # fmt: skip
        return RadioResponse(kw=radio, automatico=True)

    def _detectar(self, serie: list[Medicion], umbral: float | None) -> list[EventoCarga]:
        if umbral is None:
            return []
        eventos = detectar_eventos(serie, umbral)
        encendidos = sum(e.es_encendido for e in eventos)
        self._logger.info(
            "%d eventos detectados en %d mediciones (%d ↑ encendidos, %d ↓ apagados)",
            len(eventos), len(serie), encendidos, len(eventos) - encendidos,
        )  # fmt: skip
        if serie and not eventos:
            self._logger.warning("Ningún salto supera %s kW: probá con un umbral más bajo", umbral)
        return eventos

    def _resumir(self, serie: list[Medicion], eventos: list[EventoCarga], etiquetas: list[int]) -> list[Carga]:
        self._logger.info("Paso 4/4 · Resumiendo cargas")
        cargas = resumir_cargas(eventos, etiquetas)
        dias = _dias(serie)
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


def _dias(serie: list[Medicion]) -> float:
    if not serie:
        return 0.0
    return (max(m.instante for m in serie) - min(m.instante for m in serie)).total_seconds() / 86400
