"""tests/integration/test_residuos_pipeline.py — El pipeline reproduce los resultados versionados."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.adapters.residuos.gateways.residuos_csv_gateway import (
    DEFAULT_DATA,
    DEFAULT_OUTPUT,
    load_monthly_totals,
)
from src.domain.residuos.exceptions import DatosInvalidosError
from src.infrastructure.cli.pronosticar_residuos import pronosticar


def test_reproduce_los_csv_de_resultados(tmp_path: Path) -> None:
    respuesta = pronosticar(DEFAULT_DATA, tmp_path)

    assert respuesta.meses == 111
    assert (respuesta.primer_mes, respuesta.ultimo_mes) == ("2017-07", "2026-09")
    assert len(respuesta.archivos) == 3
    for nombre in ("serie_mensual_ciudad.csv", "pronostico_3_meses.csv"):
        pd.testing.assert_frame_equal(
            pd.read_csv(tmp_path / nombre), pd.read_csv(DEFAULT_OUTPUT / nombre)
        )
    # El bosque usa n_jobs=-1: la suma en paralelo varía en el decimal 13 entre corridas.
    pd.testing.assert_frame_equal(
        pd.read_csv(tmp_path / "metricas_validacion.csv"),
        pd.read_csv(DEFAULT_OUTPUT / "metricas_validacion.csv"),
        rtol=1e-9,
    )


def test_rechaza_meses_incompletos(tmp_path: Path) -> None:
    registros = pd.read_csv(DEFAULT_DATA)
    incompleto = tmp_path / "incompleto.csv"
    registros.iloc[1:].to_csv(incompleto, index=False)
    with pytest.raises(DatosInvalidosError, match="categorías"):
        load_monthly_totals(incompleto)
