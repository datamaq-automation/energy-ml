"""tests/unit/crecidas/test_pipeline_crecidas.py"""

import csv
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

from src.application.crecidas.clasificar_episodios import clasificar_episodios
from src.application.crecidas.comparar_estaciones import comparar_estaciones
from src.application.crecidas.construir_dataset import construir_dataset
from src.application.crecidas.evaluar_episodios import evaluar_episodios
from src.application.crecidas.evaluar_pronosticador import (
    EvaluarPronosticadorUseCase,
)
from src.domain.crecidas.modelos import NivelRio
from src.infrastructure.csv.observaciones_repository import (
    CsvObservacionesRepository,
)
from src.infrastructure.sklearn.pronosticador_nivel import PronosticadorNivel


def crear_niveles(cantidad=60):
    """Genera observaciones históricas sintéticas para las pruebas."""
    tigre = []
    san_fernando = []

    inicio = date(2025, 1, 1)

    for i in range(cantidad):
        dia = inicio + timedelta(days=i)

        valor = 1.0 + (i % 12) * 0.15

        tigre.append(
            NivelRio(
                instante=datetime.combine(dia, datetime.min.time()),
                nivel_m=valor,
            )
        )

        san_fernando.append(
            NivelRio(
                instante=datetime.combine(dia, datetime.min.time()),
                nivel_m=valor * 0.95,
            )
        )

    return tigre, san_fernando


@pytest.fixture
def dataset():
    tigre, san_fernando = crear_niveles()
    return construir_dataset(tigre, san_fernando, 1)


def test_construir_dataset(dataset):
    assert dataset.fechas
    assert dataset.variables
    assert dataset.objetivos
    assert dataset.horizonte_dias == 1


def test_pronosticador_entrena_y_predice(dataset):
    modelo = PronosticadorNivel()

    modelo.entrenar(dataset.variables, dataset.objetivos)

    resultado = modelo.predecir(dataset.variables[:2])

    assert len(resultado) == 2


def test_pronosticador_rechaza_prediccion_sin_entrenar():
    modelo = PronosticadorNivel()

    with pytest.raises(RuntimeError):
        modelo.predecir([[1.0]])


def test_repository_lee_csv_temporal(tmp_path: Path):
    ruta = tmp_path / "tigre_49.csv"

    with ruta.open("w", encoding="utf-8", newline="") as archivo:
        escritor = csv.DictWriter(
            archivo,
            fieldnames=["timestart", "valor"],
        )
        escritor.writeheader()
        escritor.writerow({
            "timestart": "2025-01-01T12:00:00Z",
            "valor": "2.5",
        })
        escritor.writerow({
            "timestart": "2025-01-01T15:00:00Z",
            "valor": "2.7",
        })

    repositorio = CsvObservacionesRepository(tmp_path)

    resultado = repositorio.listar(
        "tigre",
        datetime(2025, 1, 1),
        datetime(2025, 1, 2),
    )

    assert len(resultado) == 1
    assert resultado[0].nivel_m == pytest.approx(2.6)


def test_evaluar_pronosticador(dataset):
    resultado = EvaluarPronosticadorUseCase().execute(
        dataset,
        PronosticadorNivel,
    )

    assert resultado.ejemplos_entrenamiento > 0
    assert resultado.ejemplos_prueba > 0
    assert resultado.mae_modelo >= 0


def test_comparar_estaciones(dataset):
    resultado = comparar_estaciones(dataset, PronosticadorNivel)

    assert resultado.mae_tigre >= 0
    assert resultado.mae_dos_estaciones >= 0



def test_evaluar_episodios(dataset):
    niveles = dict(zip(
        dataset.fechas,
        dataset.objetivos,
        strict=True,
    ))

    resultado = evaluar_episodios(
        dataset,
        niveles,
        PronosticadorNivel,
    )

    assert resultado.episodios_reales >= 0
    assert resultado.anticipados_modelo >= 0


def test_clasificar_episodios(dataset):
    niveles = dict(zip(
        dataset.fechas,
        dataset.objetivos,
        strict=True,
    ))

    resultados = clasificar_episodios(dataset, niveles)

    assert len(resultados) == 3
    assert all(resultado.f1 >= 0 for resultado in resultados)
