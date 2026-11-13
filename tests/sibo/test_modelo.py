"""Pruebas del modelo híbrido de estimación de gases."""

from __future__ import annotations

from dataclasses import replace

from sibo.domain.entities import Alimento
from sibo.infrastructure.ml.modelo_hibrido import ModeloGasesHibrido


def _alimento(**cambios: object) -> Alimento:
    base = Alimento(
        id=1,
        nombre="Alimento base",
        categoria="Verdura",
        porcion_base_g=100,
        kcal=50,
        proteinas_g=2,
        carbohidratos_g=8,
        grasas_g=1,
        fibra_g=2,
        fodmap="bajo",
        score_inflamatorio=2,
        score_desinflamatorio=7,
    )
    return replace(base, **cambios)


def test_prediccion_esta_en_rango() -> None:
    modelo = ModeloGasesHibrido(semilla=7)
    prediccion = modelo.predecir_pico(_alimento(), 150, 13, 3)
    assert 0.0 <= prediccion <= 100.0


def test_alto_fodmap_predice_mas_gases_que_bajo_fodmap() -> None:
    modelo = ModeloGasesHibrido(semilla=7)
    bajo = modelo.predecir_pico(_alimento(fodmap="bajo"), 150, 13, 3)
    alto = modelo.predecir_pico(_alimento(fodmap="alto"), 150, 13, 3)
    assert alto > bajo


def test_mayor_porcion_predice_mas_gases() -> None:
    modelo = ModeloGasesHibrido(semilla=7)
    poca = modelo.predecir_pico(_alimento(), 50, 13, 3)
    mucha = modelo.predecir_pico(_alimento(), 400, 13, 3)
    assert mucha > poca


def test_prediccion_es_deterministica_para_la_misma_semilla() -> None:
    primero = ModeloGasesHibrido(semilla=21).predecir_pico(_alimento(), 150, 13, 3)
    segundo = ModeloGasesHibrido(semilla=21).predecir_pico(_alimento(), 150, 13, 3)
    assert primero == segundo
