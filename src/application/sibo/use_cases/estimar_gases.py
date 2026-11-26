"""src/application/sibo/use_cases/estimar_gases.py — Caso de uso de la curva de gases."""

from __future__ import annotations

import calendar
from datetime import date, datetime, time, timedelta

from src.application.sibo.dtos import SerieGases
from src.domain.sibo.entities import PrediccionPico, PuntoGases, RegistroComida
from src.domain.sibo.repositories import AlimentoRepository, PredictorGases, RegistroRepository
from src.domain.sibo.services import curva_absorcion
from src.domain.sibo.value_objects import VENTANA_DIGESTION_HORAS

NIVEL_BASE = 5.0
FACTOR_CONTRIBUCION = 0.9


class EstimarGasesUseCase:
    """Construye la curva sumando la contribución de cada comida registrada."""

    def __init__(
        self,
        alimentos: AlimentoRepository,
        registros: RegistroRepository,
        predictor: PredictorGases,
    ) -> None:
        self._alimentos = alimentos
        self._registros = registros
        self._predictor = predictor

    def execute(self, rango: str, fecha: date | None = None) -> SerieGases:
        inicio, fin, paso = _ventana(rango, fecha or date.today())
        margen = timedelta(hours=VENTANA_DIGESTION_HORAS)
        registros = self._registros.listar(inicio - margen, fin)
        alimentos = {
            a.id: a for a in self._alimentos.listar_por_ids({r.alimento_id for r in registros})
        }

        picos = [
            (
                registro,
                self._predictor.predecir_pico(
                    alimentos[registro.alimento_id],
                    registro.porcion_g,
                    registro.fecha_hora.hour + registro.fecha_hora.minute / 60,
                    registro.sintomas,
                ),
            )
            for registro in registros
            if registro.alimento_id in alimentos
        ]

        puntos = _construir_puntos(inicio, fin, paso, picos)
        niveles = [punto.nivel_estimado for punto in puntos]
        return SerieGases(
            rango=rango,
            desde=inicio,
            hasta=fin,
            promedio=round(sum(niveles) / len(niveles), 1) if niveles else 0.0,
            pico=round(max(niveles), 1) if niveles else 0.0,
            puntos=puntos,
        )


def _ventana(rango: str, fecha: date) -> tuple[datetime, datetime, timedelta]:
    if rango == "dia":
        inicio = datetime.combine(fecha, time.min)
        return inicio, inicio + timedelta(days=1), timedelta(hours=1)
    if rango == "semana":
        lunes = fecha - timedelta(days=fecha.weekday())
        inicio = datetime.combine(lunes, time.min)
        return inicio, inicio + timedelta(days=7), timedelta(hours=1)
    if rango == "mes":
        inicio = datetime.combine(fecha.replace(day=1), time.min)
        dias = calendar.monthrange(fecha.year, fecha.month)[1]
        return inicio, inicio + timedelta(days=dias), timedelta(days=1)
    raise ValueError(f"Rango inválido: {rango!r}. Usá 'dia', 'semana' o 'mes'.")


def _construir_puntos(
    inicio: datetime,
    fin: datetime,
    paso: timedelta,
    picos: list[tuple[RegistroComida, PrediccionPico]],
) -> list[PuntoGases]:
    puntos: list[PuntoGases] = []
    instante = inicio
    while instante <= fin:
        nivel = NIVEL_BASE
        nivel_bajo = NIVEL_BASE
        nivel_alto = NIVEL_BASE
        for registro, prediccion in picos:
            horas = (instante - registro.fecha_hora).total_seconds() / 3600
            forma = curva_absorcion(horas) * FACTOR_CONTRIBUCION
            nivel += prediccion.pico * forma
            nivel_bajo += prediccion.bajo * forma
            nivel_alto += prediccion.alto * forma
        puntos.append(
            PuntoGases(
                instante=instante,
                nivel_estimado=round(min(nivel, 100.0), 1),
                nivel_bajo=round(min(nivel_bajo, 100.0), 1),
                nivel_alto=round(min(nivel_alto, 100.0), 1),
            )
        )
        instante += paso
    return puntos
