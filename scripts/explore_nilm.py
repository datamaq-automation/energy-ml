"""scripts/explore_nilm.py — Corre IdentificarCargas contra la BD configurada en .env e imprime el resultado.

Uso (con túnel `ssh -L 3306:127.0.0.1:3306 vps` y DATABASE_URL en .env):
    .venv/bin/python scripts/explore_nilm.py "Trafo arriba" 2026-09-11 2026-10-03
"""

import sys
from datetime import datetime

from src.application.cargas.dtos.identificar_cargas import IdentificarCargasRequest
from src.infrastructure.fastapi.dependencies import get_identificar_cargas


def main(medidor: str, desde: str, hasta: str) -> None:
    request = IdentificarCargasRequest(
        medidor=medidor, desde=datetime.fromisoformat(desde), hasta=datetime.fromisoformat(hasta)
    )
    resultado = get_identificar_cargas().execute(request)
    sys.stdout.write(
        f"{resultado.medidor}: {resultado.mediciones} mediciones, {resultado.eventos} eventos, "
        f"potencia media {resultado.potencia_media_kw} kW\n"
    )
    for carga in resultado.cargas:
        sys.stdout.write(
            f"  ~{carga.potencia_tipica_kw:>7} kW  encendidos={carga.encendidos:<4} apagados={carga.apagados:<4}\n"
        )


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
