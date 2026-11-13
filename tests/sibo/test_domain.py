"""Pruebas de las reglas puras del dominio SIBO."""

from __future__ import annotations

from dataclasses import replace

from sibo.domain.entities import Alimento
from sibo.domain.servicios import (
    curva_absorcion,
    factor_fodmap,
    factor_porcion,
    motivo_recomendacion,
    puntaje_heuristico,
)


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


def test_factor_fodmap_ordena_las_categorias() -> None:
    assert factor_fodmap("bajo") < factor_fodmap("medio") < factor_fodmap("alto")
    assert factor_fodmap("desconocido") == 0.5


def test_factor_porcion_se_acota_entre_limites() -> None:
    alimento = _alimento(porcion_base_g=100)
    assert factor_porcion(alimento, 50) == 0.5
    assert factor_porcion(alimento, 10000) == 3.0


def test_puntaje_sube_con_fodmap_inflamacion_y_porcion() -> None:
    bajo = puntaje_heuristico(_alimento(fodmap="bajo"), 100, 12, 0)
    alto = puntaje_heuristico(_alimento(fodmap="alto", score_inflamatorio=9), 300, 12, 0)
    assert alto > bajo


def test_puntaje_baja_con_score_desinflamatorio() -> None:
    inflamatorio = puntaje_heuristico(_alimento(score_desinflamatorio=1), 100, 12, 0)
    desinflamatorio = puntaje_heuristico(_alimento(score_desinflamatorio=10), 100, 12, 0)
    assert desinflamatorio < inflamatorio


def test_puntaje_sube_con_sintomas() -> None:
    sin_sintomas = puntaje_heuristico(_alimento(), 100, 12, 0)
    con_sintomas = puntaje_heuristico(_alimento(), 100, 12, 10)
    assert con_sintomas > sin_sintomas


def test_curva_absorcion_tiene_pico_a_las_dos_horas() -> None:
    assert curva_absorcion(-1) == 0.0
    assert curva_absorcion(9) == 0.0
    assert curva_absorcion(2) == 1.0
    assert curva_absorcion(1) < curva_absorcion(2)
    assert curva_absorcion(4) < curva_absorcion(2)


def test_motivo_menciona_consumo_reciente() -> None:
    motivo = motivo_recomendacion(_alimento(), consumido_recientemente=True)
    assert "Ya lo registraste esta semana" in motivo
