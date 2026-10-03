"""scripts/entrenar_cargas.py — Identifica las cargas de cada data/input/*.csv y las guarda en data/output/.

Uso:
    .venv/bin/python -m scripts.entrenar_cargas
"""

import csv
import sys
from datetime import datetime
from pathlib import Path

from src.application.cargas.dtos.identificar_cargas import IdentificarCargasRequest
from src.application.cargas.use_cases.identificar_cargas import IdentificarCargasUseCase
from src.infrastructure.csv.medicion_repository import CsvMedicionRepository
from src.infrastructure.settings.config import get_settings
from src.infrastructure.sklearn.dbscan_agrupador import DbscanAgrupador

DATA = Path(__file__).resolve().parent.parent / "data"
ENTRADA, SALIDA = DATA / "input", DATA / "output"
TODO_EL_RANGO = (datetime(2000, 1, 1), datetime(2100, 1, 1))


def main() -> None:
    settings = get_settings()
    caso_de_uso = IdentificarCargasUseCase(
        mediciones=CsvMedicionRepository(ENTRADA),
        agrupador=DbscanAgrupador(eps_kw=settings.NILM_EPS_KW, min_eventos=settings.NILM_MIN_EVENTOS),
        umbral_kw=settings.NILM_UMBRAL_KW,
    )
    SALIDA.mkdir(parents=True, exist_ok=True)
    for entrada in sorted(ENTRADA.glob("*.csv")):
        desde, hasta = TODO_EL_RANGO
        r = caso_de_uso.execute(IdentificarCargasRequest(medidor=entrada.stem, desde=desde, hasta=hasta))
        destino = SALIDA / f"cargas_{entrada.name}"
        with destino.open("w", newline="", encoding="utf-8") as archivo:
            escritor = csv.writer(archivo)
            escritor.writerow(["potencia_tipica_kw", "encendidos", "apagados", "ciclos"])
            escritor.writerows((c.potencia_tipica_kw, c.encendidos, c.apagados, c.ciclos) for c in r.cargas)
        sys.stdout.write(
            f"{entrada.stem}: {r.mediciones} mediciones, {r.eventos} eventos, {len(r.cargas)} cargas -> {destino.name}\n"
        )


if __name__ == "__main__":
    main()
