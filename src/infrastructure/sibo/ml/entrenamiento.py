"""src/infrastructure/sibo/ml/entrenamiento.py — Entrenamiento con etiquetas reales posteriores."""

from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from sklearn.ensemble import RandomForestRegressor

from src.domain.sibo.entities import Alimento, RegistroComida
from src.domain.sibo.services import es_seguimiento_valido, puntaje_heuristico
from src.domain.sibo.value_objects import (
    MIN_MUESTRAS_REALES,
    MIN_VALIDACION_REAL,
    PoliticaModelo,
)
from src.infrastructure.sibo.ml.caracteristicas import caracteristicas


@dataclass(frozen=True)
class MuestraReal:
    """Comida con su etiqueta observada a las 2 h y sin fuga de información."""

    fecha_hora: datetime
    alimento: Alimento
    porcion_g: float
    hora: float
    sintomas: float
    etiqueta: float


@dataclass(frozen=True)
class ResultadoEntrenamiento:
    """Estado del predictor después de compararlo con la heurística en el tiempo."""

    modelo: RandomForestRegressor | None
    peso_modelo: float
    peso_heuristica: float
    residuos: tuple[float, ...]
    mae_modelo: float | None
    mae_heuristica: float | None
    cantidad: int
    validacion: int


CONSULTA_MUESTRAS = """
SELECT r.fecha_hora, r.porcion_g, r.sintomas, r.sintomas_2h, r.fecha_sintomas_2h,
       a.id AS alimento_id, a.nombre AS alimento_nombre, a.categoria AS alimento_categoria,
       a.porcion_base_g, a.kcal, a.proteinas_g, a.carbohidratos_g, a.grasas_g,
       a.fibra_g, a.fodmap, a.score_inflamatorio, a.score_desinflamatorio,
       a.notas AS alimento_notas
FROM registros r
JOIN alimentos a ON a.id = r.alimento_id
WHERE r.sintomas_2h IS NOT NULL AND r.fecha_sintomas_2h IS NOT NULL
ORDER BY r.fecha_hora
"""


def cargar_muestras(conexion: sqlite3.Connection) -> list[MuestraReal]:
    """Toma solo seguimientos válidos, ordenados por fecha para partir sin mirar el futuro."""
    muestras: list[MuestraReal] = []
    for fila in conexion.execute(CONSULTA_MUESTRAS):
        fecha_sintomas = datetime.fromisoformat(fila["fecha_sintomas_2h"])
        registro = RegistroComida(
            fecha_hora=datetime.fromisoformat(fila["fecha_hora"]),
            alimento_id=fila["alimento_id"],
            porcion_g=fila["porcion_g"],
            sintomas=fila["sintomas"],
            sintomas_2h=fila["sintomas_2h"],
            fecha_sintomas_2h=fecha_sintomas,
        )
        if not es_seguimiento_valido(registro, fecha_sintomas):
            continue
        muestras.append(
            MuestraReal(
                fecha_hora=registro.fecha_hora,
                alimento=_alimento_desde_fila(fila),
                porcion_g=registro.porcion_g,
                hora=registro.fecha_hora.hour + registro.fecha_hora.minute / 60,
                sintomas=registro.sintomas,
                etiqueta=registro.sintomas_2h * 10.0,
            )
        )
    return muestras


def entrenar(
    muestras: Sequence[MuestraReal],
    politica: PoliticaModelo,
    semilla: int = 42,
) -> ResultadoEntrenamiento:
    """Aprende de muestras reales; sin datos suficientes devuelve solo la heurística."""
    cantidad = len(muestras)
    if cantidad < MIN_MUESTRAS_REALES:
        return ResultadoEntrenamiento(None, 0.0, 1.0, (), None, None, cantidad, 0)

    ordenadas = sorted(muestras, key=lambda muestra: muestra.fecha_hora)
    corte = min(max(int(cantidad * 0.8), 1), cantidad - 1)
    entrenamiento, validacion = ordenadas[:corte], ordenadas[corte:]
    if len(validacion) < MIN_VALIDACION_REAL:
        return ResultadoEntrenamiento(None, 0.0, 1.0, (), None, None, cantidad, len(validacion))

    x_entrenamiento = [_vector(muestra) for muestra in entrenamiento]
    y_entrenamiento = [muestra.etiqueta for muestra in entrenamiento]
    modelo = RandomForestRegressor(n_estimators=120, random_state=semilla, n_jobs=1)
    modelo.fit(x_entrenamiento, y_entrenamiento)

    observados = [muestra.etiqueta for muestra in validacion]
    predicciones_modelo = [
        min(max(float(valor), 0.0), 100.0)
        for valor in modelo.predict([_vector(muestra) for muestra in validacion])
    ]
    predicciones_heuristica = [
        puntaje_heuristico(
            muestra.alimento,
            muestra.porcion_g,
            muestra.hora,
            muestra.sintomas,
        )
        for muestra in validacion
    ]
    mae_modelo = _mae(predicciones_modelo, observados)
    mae_heuristica = _mae(predicciones_heuristica, observados)
    supera = mae_modelo < mae_heuristica
    peso_modelo = politica.peso_modelo if supera else 0.0
    peso_heuristica = 1.0 - peso_modelo
    mezclados = [
        peso_modelo * modelo_predicho + peso_heuristica * heuristica
        for modelo_predicho, heuristica in zip(
            predicciones_modelo, predicciones_heuristica, strict=True
        )
    ]
    residuos = tuple(predicho - real for predicho, real in zip(mezclados, observados, strict=True))
    return ResultadoEntrenamiento(
        modelo=modelo if supera else None,
        peso_modelo=peso_modelo,
        peso_heuristica=peso_heuristica,
        residuos=residuos,
        mae_modelo=mae_modelo,
        mae_heuristica=mae_heuristica,
        cantidad=cantidad,
        validacion=len(validacion),
    )


def _vector(muestra: MuestraReal) -> list[float]:
    return caracteristicas(
        muestra.alimento,
        muestra.porcion_g,
        muestra.hora,
        muestra.sintomas,
    )


def _mae(predichos: Sequence[float], observados: Sequence[float]) -> float:
    return sum(
        abs(predicho - real) for predicho, real in zip(predichos, observados, strict=True)
    ) / len(observados)


def _alimento_desde_fila(fila: sqlite3.Row) -> Alimento:
    return Alimento(
        id=fila["alimento_id"],
        nombre=fila["alimento_nombre"],
        categoria=fila["alimento_categoria"],
        porcion_base_g=fila["porcion_base_g"],
        kcal=fila["kcal"],
        proteinas_g=fila["proteinas_g"],
        carbohidratos_g=fila["carbohidratos_g"],
        grasas_g=fila["grasas_g"],
        fibra_g=fila["fibra_g"],
        fodmap=fila["fodmap"],
        score_inflamatorio=fila["score_inflamatorio"],
        score_desinflamatorio=fila["score_desinflamatorio"],
        notas=fila["alimento_notas"],
    )
