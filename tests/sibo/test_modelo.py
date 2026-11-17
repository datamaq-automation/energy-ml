"""tests/sibo/test_modelo.py — Pruebas del modelo híbrido de estimación de gases."""

from __future__ import annotations

from dataclasses import replace

import pytest

from src.application.sibo.politica_modelo import PoliticaModelo
from src.domain.sibo.entities import Alimento, PrediccionPico
from src.domain.sibo.servicios import puntaje_heuristico
from src.infrastructure.sibo.ml.modelo_hibrido import ModeloGasesHibrido


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


def _modelo(**cambios: float) -> ModeloGasesHibrido:
    return ModeloGasesHibrido(politica=PoliticaModelo(**cambios), semilla=7)


def _predecir(modelo: ModeloGasesHibrido, alimento: Alimento | None = None) -> PrediccionPico:
    return modelo.predecir_pico(alimento or _alimento(), 150, 13, 3)


def test_prediccion_esta_en_rango() -> None:
    prediccion = _predecir(_modelo())
    assert 0.0 <= prediccion.pico <= 100.0


def test_banda_contiene_el_pico_y_tiene_orden() -> None:
    prediccion = _predecir(_modelo())
    assert prediccion.bajo <= prediccion.pico <= prediccion.alto
    assert prediccion.bajo < prediccion.alto


def test_banda_mas_ancha_con_percentiles_extremos() -> None:
    amplia = _predecir(_modelo(percentil_bajo=0.0, percentil_alto=100.0))
    estrecha = _predecir(_modelo(percentil_bajo=10.0, percentil_alto=90.0))
    assert (amplia.alto - amplia.bajo) >= (estrecha.alto - estrecha.bajo)


def test_peso_modelo_cero_usa_solo_heuristica() -> None:
    alimento = _alimento()
    modelo = _modelo(peso_modelo=0.0, peso_heuristica=1.0)
    prediccion = modelo.predecir_pico(alimento, 150, 13, 3)
    esperado = round(puntaje_heuristico(alimento, 150, 13, 3), 1)
    assert prediccion == PrediccionPico(pico=esperado, bajo=esperado, alto=esperado)


def test_politica_invalida_falla() -> None:
    with pytest.raises(ValueError):
        PoliticaModelo(peso_modelo=0.8, peso_heuristica=0.3)
    with pytest.raises(ValueError):
        PoliticaModelo(percentil_bajo=90.0, percentil_alto=10.0)


def test_alto_fodmap_predice_mas_gases_que_bajo_fodmap() -> None:
    modelo = _modelo()
    bajo = _predecir(modelo, _alimento(fodmap="bajo")).pico
    alto = _predecir(modelo, _alimento(fodmap="alto")).pico
    assert alto > bajo


def test_mayor_porcion_predice_mas_gases() -> None:
    modelo = _modelo()
    poca = modelo.predecir_pico(_alimento(), 50, 13, 3).pico
    mucha = modelo.predecir_pico(_alimento(), 400, 13, 3).pico
    assert mucha > poca


def test_prediccion_es_deterministica_para_la_misma_semilla() -> None:
    primero = _predecir(ModeloGasesHibrido(politica=PoliticaModelo(), semilla=21))
    segundo = _predecir(ModeloGasesHibrido(politica=PoliticaModelo(), semilla=21))
    assert primero == segundo
