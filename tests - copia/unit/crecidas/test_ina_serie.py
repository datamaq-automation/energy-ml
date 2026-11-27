"""tests/unit/crecidas/test_ina_serie.py"""

from datetime import date, datetime, timezone

from src.domain.crecidas.modelos import NivelRio
from src.infrastructure.crecidas.ina_serie import (
    SERIE_TIGRE_ALTURA_DIARIA,
    construir_url,
    obtener_serie,
    parsear_csv,
)

# Muestra real del endpoint del INA (serie 49, Tigre), recortada a 3 filas.
CSV_TIGRE = (
    "id,tipo,series_id,timestart,timeend,nombre,descripcion,unit_id,timeupdate,valor\n"
    "22238722592,puntual,49,2024-01-01T03:00:00.000Z,2024-01-01T03:00:00.000Z,"
    "upsertObservacionesPuntual,,,2024-01-02T15:00:59.908Z,1.6\n"
    "22238722593,puntual,49,2024-01-02T03:00:00.000Z,2024-01-02T03:00:00.000Z,"
    "upsertObservacionesPuntual,,,2024-01-02T15:00:59.908Z,1.7\n"
    "29671927499,puntual,49,2026-11-06T03:00:00.000Z,2026-11-06T03:00:00.000Z,"
    "upsertObservacionesPuntual,,,2026-11-06T14:34:02.533Z,0.6\n"
)


def test_construir_url_usa_serie_y_rango() -> None:
    url = construir_url(SERIE_TIGRE_ALTURA_DIARIA, date(2024, 1, 1), date(2024, 12, 31))
    assert url.startswith("https://alerta.ina.gob.ar/a5/getObservaciones?")
    assert "series_id=49" in url
    assert "timestart=2024-01-01" in url
    assert "timeend=2024-12-31" in url
    assert "format=csv" in url


def test_parsear_csv_devuelve_niveles_con_instante_utc() -> None:
    niveles = parsear_csv(CSV_TIGRE)
    assert len(niveles) == 3
    assert niveles[0] == NivelRio(
        instante=datetime(2024, 1, 1, 3, 0, tzinfo=timezone.utc), nivel_m=1.6
    )
    assert niveles[-1].nivel_m == 0.6


def test_parsear_csv_ordena_por_instante() -> None:
    lineas = CSV_TIGRE.splitlines()
    desordenado = "\n".join([lineas[0], lineas[3], lineas[1], lineas[2]]) + "\n"
    instantes = [n.instante for n in parsear_csv(desordenado)]
    assert instantes == sorted(instantes)


def test_parsear_csv_descarta_filas_sin_valor() -> None:
    texto = CSV_TIGRE + ("1,puntual,49,2024-01-03T03:00:00.000Z,2024-01-03T03:00:00.000Z,x,,,,\n")
    assert len(parsear_csv(texto)) == 3


def test_obtener_serie_usa_el_descargador_inyectado() -> None:
    pedidas: list[str] = []

    def falso(url: str) -> str:
        pedidas.append(url)
        return CSV_TIGRE

    niveles = obtener_serie(49, date(2024, 1, 1), date(2024, 1, 31), descargar=falso)
    assert len(niveles) == 3
    assert "series_id=49" in pedidas[0]
