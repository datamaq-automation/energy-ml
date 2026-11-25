"""src/infrastructure/cli/analizar_medioambiente.py — Ejecuta las Tareas A, B y C en orden.

Uso: python -m src.infrastructure.cli.analizar_medioambiente
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from src.adapters.medioambiente.controllers.episodios_co_controller import EpisodiosCOController
from src.adapters.medioambiente.gateways.air_quality_uci_gateway import (
    DEFAULT_DATA_DIR,
    AirQualityUciGateway,
)
from src.adapters.medioambiente.presenters.episodios_co_presenter import EpisodiosCOPresenter
from src.application.medioambiente.dtos.analizar_episodios_response import (
    AnalizarEpisodiosResponse,
)
from src.application.medioambiente.use_cases.analizar_episodios_co import (
    AnalizarEpisodiosCOUseCase,
)
from src.infrastructure.settings.logger import logger
from src.infrastructure.sklearn.medioambiente_modelador import ModeladorEpisodiosSklearn

DESTINO_IMAGENES = Path("docs/medioambiente/imagenes")


def ejecutar_tareas(
    destino_imagenes: Path = DESTINO_IMAGENES, carpeta_datos: Path = DEFAULT_DATA_DIR
) -> AnalizarEpisodiosResponse:
    """Arma las dependencias, corre A → B → C y registra el reporte en el log."""
    controlador = EpisodiosCOController(
        AnalizarEpisodiosCOUseCase(
            AirQualityUciGateway(carpeta_datos), ModeladorEpisodiosSklearn()
        ),
        EpisodiosCOPresenter(),
    )
    respuesta, lineas = controlador.analizar(str(destino_imagenes), datetime.now())
    for linea in lineas:
        logger.info("%s", linea)
    return respuesta


def main() -> None:
    """Punto de entrada de `python -m src.infrastructure.cli.analizar_medioambiente`."""
    ejecutar_tareas()


if __name__ == "__main__":
    main()
