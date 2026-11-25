"""tests/unit/medioambiente/test_caso_de_uso.py — Caso de uso, controlador y presentador con dobles."""

from __future__ import annotations

from datetime import datetime

import pytest

from src.adapters.medioambiente.controllers.episodios_co_controller import EpisodiosCOController
from src.adapters.medioambiente.presenters.episodios_co_presenter import EpisodiosCOPresenter
from src.application.medioambiente.use_cases.analizar_episodios_co import (
    AnalizarEpisodiosCOUseCase,
)
from src.domain.medioambiente.exceptions import FugaDeDatosError, SinDiagnosticosError
from src.domain.medioambiente.repositories import ModeladorEpisodios, RepositorioCalidadAire
from src.domain.medioambiente.services import (
    elegir_mejor_k,
    elegir_mejor_modelo,
    verificar_sin_fuga,
)
from src.domain.medioambiente.value_objects import (
    CambioDistribucion,
    DiagnosticoK,
    MatrizConfusion,
    MetricasModelo,
    Particion,
    PerfilGrupo,
)

MATRIZ = MatrizConfusion(50, 5, 3, 12)


class RepositorioFalso(RepositorioCalidadAire):
    def cargar(self) -> list[float]:
        return [1.0, 2.0, 3.0]


class ModeladorFalso(ModeladorEpisodios):
    def __init__(self) -> None:
        self.destino = ""

    def contar_filas(self, crudo: list[float]) -> int:
        return len(crudo)

    def diagnosticar_k(self, crudo: list[float]) -> list[DiagnosticoK]:
        return [DiagnosticoK(2, 10.0, 0.30), DiagnosticoK(3, 8.0, 0.45), DiagnosticoK(4, 7.0, 0.40)]

    def perfilar_grupos(self, crudo: list[float], k: int) -> list[PerfilGrupo]:
        return [PerfilGrupo(g, 10, 20.0, 50.0, 1.0, 0.1 * g) for g in range(k)]

    def preparar(self, crudo: list[float]) -> list[float]:
        return crudo

    def evaluar(self, datos: list[float], particion: Particion) -> list[MetricasModelo]:
        return [
            MetricasModelo("linea_base", particion, 0.8, 0.0, 0.0, 0.0, MATRIZ),
            MetricasModelo("arbol", particion, 0.85, 0.6, 0.7, 0.65, MATRIZ),
            MetricasModelo("regresion_logistica", particion, 0.8, 0.5, 0.8, 0.62, MATRIZ),
        ]

    def detectar_cambios(self, datos: list[float]) -> list[CambioDistribucion]:
        return [
            CambioDistribucion("T_t1", 15.0, 25.0, 1.2, True),
            CambioDistribucion("hora", 11.5, 11.5, 0.0, False),
        ]

    def graficar_diagnosticos(self, diagnosticos: list[DiagnosticoK], destino: str) -> list[str]:
        self.destino = destino
        return [f"{destino}/codo_kmeans.png"]


def test_controlador_corre_las_tres_tareas_en_orden() -> None:
    modelador = ModeladorFalso()
    controlador = EpisodiosCOController(
        AnalizarEpisodiosCOUseCase(RepositorioFalso(), modelador), EpisodiosCOPresenter()
    )

    respuesta, lineas = controlador.analizar("graficos", datetime(2026, 11, 25, 10, 30))

    assert respuesta.id_informe == "episodios-co-20261125T103000"
    assert respuesta.filas_cargadas == 3
    assert respuesta.mejor_k == 3
    assert len(respuesta.grupos) == 3
    assert len(respuesta.metricas) == 6
    assert respuesta.mejor_modelo == "arbol"
    assert respuesta.matriz_confusion == [[50, 5], [3, 12]]
    assert respuesta.features_con_cambio == ["T_t1"]
    assert [e.split(":")[0] for e in respuesta.eventos] == [
        "Tarea A — K-means sobre meteorología (sin etiqueta)",
        "Tarea B — Modelos con split aleatorio estratificado",
        "Tarea C — Split temporal (80 % más antiguo → 20 % más reciente)",
    ]
    assert modelador.destino == "graficos"
    assert any("Mejor k por silueta: 3" in linea for linea in lineas)


def test_reglas_de_dominio() -> None:
    with pytest.raises(SinDiagnosticosError):
        elegir_mejor_k([])
    with pytest.raises(FugaDeDatosError, match="CO\\(GT\\)"):
        verificar_sin_fuga(["T_t1", "CO(GT)"])
    empate = [
        MetricasModelo("primero", Particion.TEMPORAL, 0.9, 0.5, 0.5, 0.5, MATRIZ),
        MetricasModelo("segundo", Particion.TEMPORAL, 0.9, 0.5, 0.5, 0.5, MATRIZ),
    ]
    assert elegir_mejor_modelo(empate).modelo == "primero"
