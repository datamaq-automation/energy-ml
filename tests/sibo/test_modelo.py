"""tests/sibo/test_modelo.py — Pruebas del modelo híbrido con etiquetas reales."""

from __future__ import annotations

import random
from dataclasses import replace
from datetime import datetime, timedelta

import pytest

from src.domain.sibo.entities import Alimento, PrediccionPico, RegistroComida
from src.domain.sibo.services import es_seguimiento_valido, factor_fodmap, puntaje_heuristico
from src.domain.sibo.value_objects import PoliticaModelo
from src.infrastructure.sibo.ml.entrenamiento import MuestraReal
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


def _muestras(cantidad: int = 40, semilla: int = 7, factor: float = 1.0) -> list[MuestraReal]:
    generador = random.Random(semilla)
    inicio = datetime(2026, 1, 1, 8, 0)
    muestras: list[MuestraReal] = []
    for indice in range(cantidad):
        fodmap = generador.choice(["bajo", "medio", "alto"])
        sintomas = generador.uniform(0, 10)
        ruido = generador.gauss(0, 3)
        etiqueta = 15 + 55 * factor_fodmap(fodmap) + 8 * sintomas / 10 + ruido
        muestras.append(
            MuestraReal(
                fecha_hora=inicio + timedelta(hours=indice),
                alimento=_alimento(fodmap=fodmap),
                porcion_g=generador.uniform(50, 300),
                hora=generador.uniform(8, 20),
                sintomas=sintomas,
                etiqueta=min(max(etiqueta * factor, 0.0), 100.0),
            )
        )
    return muestras


def _modelo(muestras: list[MuestraReal] | None = None, **cambios: float) -> ModeloGasesHibrido:
    return ModeloGasesHibrido(
        politica=PoliticaModelo(**cambios),
        semilla=7,
        muestras=muestras or [],
    )


def _predecir(modelo: ModeloGasesHibrido, alimento: Alimento | None = None) -> PrediccionPico:
    return modelo.predecir_pico(alimento or _alimento(), 150, 13, 3)


def test_sin_muestras_reales_usa_solo_heuristica() -> None:
    modelo = _modelo()
    alimento = _alimento()
    prediccion = modelo.predecir_pico(alimento, 150, 13, 3)
    esperado = round(puntaje_heuristico(alimento, 150, 13, 3), 1)
    assert prediccion == PrediccionPico(esperado, esperado, esperado)
    assert modelo.estado()["modelo_activo"] is False
    assert modelo.estado()["muestras_reales"] == 0


def test_con_muestras_reales_compara_contra_la_heuristica() -> None:
    modelo = _modelo(_muestras())
    estado = modelo.estado()
    assert estado["muestras_reales"] == 40
    assert estado["muestras_validacion"] == 8
    assert estado["mae_modelo"] is not None
    assert estado["mae_heuristica"] is not None
    prediccion = _predecir(modelo)
    assert 0.0 <= prediccion.pico <= 100.0


def test_etiqueta_no_se_usa_como_feature() -> None:
    primero = _modelo(_muestras(factor=1.0))
    segundo = _modelo(_muestras(factor=0.45))
    assert primero.estado()["modelo_activo"] is True
    assert segundo.estado()["modelo_activo"] is True
    assert _predecir(primero).pico != _predecir(segundo).pico


def test_etiqueta_inmediata_no_es_valida() -> None:
    comida = RegistroComida(
        fecha_hora=datetime(2026, 1, 1, 12, 0),
        alimento_id=1,
        porcion_g=100,
        sintomas_2h=8,
    )
    assert es_seguimiento_valido(comida, datetime(2026, 1, 1, 12, 30)) is False
    assert es_seguimiento_valido(comida, datetime(2026, 1, 1, 14, 0)) is True


def test_banda_sale_de_los_residuos_reales() -> None:
    modelo = _modelo(_muestras())
    prediccion = _predecir(modelo)
    assert modelo.estado()["modelo_activo"] is True
    assert prediccion.bajo <= prediccion.pico <= prediccion.alto
    assert prediccion.bajo < prediccion.alto


def test_banda_mas_ancha_con_percentiles_extremos() -> None:
    muestras = _muestras()
    amplia = _predecir(_modelo(muestras, percentil_bajo=0.0, percentil_alto=100.0))
    estrecha = _predecir(_modelo(muestras, percentil_bajo=10.0, percentil_alto=90.0))
    assert (amplia.alto - amplia.bajo) >= (estrecha.alto - estrecha.bajo)


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
    muestras = _muestras()
    primero = _predecir(ModeloGasesHibrido(politica=PoliticaModelo(), muestras=muestras))
    segundo = _predecir(ModeloGasesHibrido(politica=PoliticaModelo(), muestras=muestras))
    assert primero == segundo
