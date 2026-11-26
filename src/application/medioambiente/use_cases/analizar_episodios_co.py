"""src/application/medioambiente/use_cases/analizar_episodios_co.py — Tareas A, B y C en orden."""

from __future__ import annotations

from typing import Generic, TypeVar

from src.application.medioambiente.dtos.analizar_episodios_request import (
    AnalizarEpisodiosRequest,
)
from src.application.medioambiente.dtos.analizar_episodios_response import (
    AnalizarEpisodiosResponse,
)
from src.application.medioambiente.mappers.informe_episodios_mapper import InformeEpisodiosMapper
from src.domain.medioambiente.entities import InformeEpisodiosCO
from src.domain.medioambiente.repositories import ModeladorEpisodios, RepositorioCalidadAire
from src.domain.medioambiente.services import elegir_mejor_k, verificar_sin_fuga
from src.domain.medioambiente.value_objects import COLUMNAS_FEATURES, Particion

Datos = TypeVar("Datos")


class AnalizarEpisodiosCOUseCase(Generic[Datos]):
    """Orquesta A (agrupar), B (split aleatorio) y C (split temporal + cambio de distribución)."""

    def __init__(
        self,
        repositorio: RepositorioCalidadAire[Datos],
        modelador: ModeladorEpisodios[Datos],
    ) -> None:
        self._repositorio = repositorio
        self._modelador = modelador

    def execute(self, request: AnalizarEpisodiosRequest) -> AnalizarEpisodiosResponse:
        """Corre las tres tareas y devuelve el informe listo para presentar."""
        verificar_sin_fuga(COLUMNAS_FEATURES)
        crudo = self._repositorio.cargar()

        diagnosticos = self._modelador.diagnosticar_k(crudo)
        grupos = self._modelador.perfilar_grupos(crudo, k=elegir_mejor_k(diagnosticos))
        graficos = self._modelador.graficar_diagnosticos(diagnosticos, request.destino_graficos)

        datos = self._modelador.preparar(crudo)
        informe = InformeEpisodiosCO(
            id=request.id_informe, filas_cargadas=self._modelador.contar_filas(crudo)
        )
        informe.registrar_agrupamiento(diagnosticos, grupos)
        informe.registrar_metricas(self._modelador.evaluar(datos, Particion.ALEATORIA))
        informe.registrar_metricas(self._modelador.evaluar(datos, Particion.TEMPORAL))
        informe.registrar_cambios(self._modelador.detectar_cambios(datos))
        return InformeEpisodiosMapper.a_response(informe, graficos)
