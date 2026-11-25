"""tests/unit/logistica/test_caso_de_uso.py — Caso de uso, controlador y presentador con dobles."""

from __future__ import annotations

from datetime import datetime

import pytest

from src.adapters.logistica.controllers.retrasos_controller import RetrasosController
from src.adapters.logistica.presenters.retrasos_presenter import RetrasosPresenter
from src.application.logistica.use_cases.analizar_retrasos import AnalizarRetrasosUseCase
from src.domain.logistica.entities import InformeRetrasos
from src.domain.logistica.exceptions import FugaDeDatosError, SinResultadosError
from src.domain.logistica.repositories import ModeladorRetrasos, RepositorioPedidos
from src.domain.logistica.services import validate_no_data_leakage
from src.domain.logistica.value_objects import (
    ClusterMetric,
    ClusterProfile,
    SegmentRecall,
    SupervisedModelMetrics,
)

MATRIZ = ((40, 10), (5, 45))


class RepositorioFalso(RepositorioPedidos):
    def cargar(self) -> list[int]:
        return [0, 1, 1, 0]


class ModeladorFalso(ModeladorRetrasos):
    def __init__(self) -> None:
        self.graficados: list[str] = []

    def contar_filas(self, datos: list[int]) -> int:
        return len(datos)

    def agrupar(
        self, datos: list[int], best_k: int
    ) -> tuple[list[ClusterMetric], list[ClusterProfile]]:
        metricas = [ClusterMetric(k, 100.0 / k, 0.3) for k in (2, 3)]
        perfil = ClusterProfile(0, 4, 2.0, 1.5, 100.0, 37.0, -95.7, 0.5, "First Class", "rápidos")
        return metricas, [perfil]

    def clasificar(
        self, datos: list[int], max_depth: int, segmento: str
    ) -> tuple[list[SupervisedModelMetrics], list[tuple[str, float]], list[SegmentRecall]]:
        modelos = [
            SupervisedModelMetrics("Baseline", 0.5, 0.0, 0.0, 0.0, MATRIZ),
            SupervisedModelMetrics(
                f"DecisionTree (max_depth={max_depth})", 0.8, 0.8, 0.9, 0.85, MATRIZ
            ),
        ]
        importancias = [(f"var_{i}", 0.1 * i) for i in range(7)]
        return modelos, importancias, [SegmentRecall(segmento, "First Class", 2, 1.0, 1.0)]

    def graficar_codo(self, metricas: list[ClusterMetric], best_k: int, destino: str) -> str:
        self.graficados.append(f"codo-k{best_k}")
        return f"{destino}/codo.png"

    def graficar_matriz(self, modelo: SupervisedModelMetrics, destino: str) -> str:
        self.graficados.append(modelo.model_name)
        return f"{destino}/matriz.png"


def test_controlador_corre_las_tres_tareas_en_orden() -> None:
    modelador = ModeladorFalso()
    controlador = RetrasosController(
        AnalizarRetrasosUseCase(RepositorioFalso(), modelador), RetrasosPresenter()
    )

    respuesta, lineas = controlador.analizar(3, 4, "salida", datetime(2026, 11, 25, 9, 0))

    assert respuesta.id_informe == "retrasos-20261125T090000"
    assert respuesta.pedidos == 4
    assert respuesta.ks_evaluados == [2, 3]
    assert len(respuesta.importancias) == 5
    assert respuesta.graficos == ["salida/codo.png", "salida/matriz.png"]
    assert modelador.graficados == ["codo-k3", "DecisionTree (max_depth=4)"]
    assert respuesta.modelos[-1].confusion_matrix == [[40, 10], [5, 45]]
    assert [e.split(" — ")[0] for e in respuesta.eventos] == ["Tarea A", "Tarea B", "Tarea C"]
    assert any(linea.startswith("Tarea C [Shipping Mode=First Class]") for linea in lineas)


def test_reglas_de_dominio() -> None:
    with pytest.raises(FugaDeDatosError, match="Data leakage detectado"):
        validate_no_data_leakage(["Sales", "Delivery Status"])
    with pytest.raises(SinResultadosError):
        _ = InformeRetrasos(id="vacío", pedidos=0).modelo_final
