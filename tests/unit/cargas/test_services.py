"""tests/unit/cargas/test_services.py — Reglas de detección de eventos y resumen de cargas."""

from datetime import datetime, timedelta

import pytest

from src.domain.cargas.entities import EventoCarga, Medicion
from src.domain.cargas.services import detectar_eventos, resumir_cargas

T0 = datetime(2026, 9, 20, 8, 0)


def serie(*kw: float) -> list[Medicion]:
    return [Medicion(instante=T0 + timedelta(minutes=5 * i), potencia_kw=p) for i, p in enumerate(kw)]


def test_detecta_encendido_y_apagado_de_carga_grande() -> None:
    eventos = detectar_eventos(serie(120, 121, 212, 210, 119), umbral_kw=60)
    assert [round(e.delta_kw) for e in eventos] == [91, -91]
    assert [e.es_encendido for e in eventos] == [True, False]


def test_ignora_variaciones_menores_al_umbral() -> None:
    assert detectar_eventos(serie(100, 110, 95, 105), umbral_kw=60) == []


def test_ordena_mediciones_desordenadas() -> None:
    datos = serie(100, 200)
    eventos = detectar_eventos(list(reversed(datos)), umbral_kw=60)
    assert eventos[0].delta_kw == 100


def test_umbral_invalido() -> None:
    with pytest.raises(ValueError):
        detectar_eventos(serie(1, 2), umbral_kw=0)


def test_resume_grupos_e_ignora_ruido() -> None:
    eventos = [EventoCarga(T0, 90), EventoCarga(T0, -92), EventoCarga(T0, 30), EventoCarga(T0, 500)]
    cargas = resumir_cargas(eventos, [0, 0, 1, -1])
    assert [(c.potencia_tipica_kw, c.encendidos, c.apagados) for c in cargas] == [(91.0, 1, 1), (30.0, 1, 0)]
    assert cargas[0].ciclos == 1


def test_resumir_exige_una_etiqueta_por_evento() -> None:
    with pytest.raises(ValueError):
        resumir_cargas([EventoCarga(T0, 90)], [])


def test_carga_on_off_requiere_encendidos_y_apagados_parecidos() -> None:
    from src.domain.cargas.entities import Carga

    assert Carga(potencia_tipica_kw=90, encendidos=10, apagados=9).es_on_off(0.5)
    assert not Carga(potencia_tipica_kw=227, encendidos=2, apagados=10).es_on_off(0.5)
    assert not Carga(potencia_tipica_kw=1, encendidos=0, apagados=0).es_on_off(0.5)


def _serie(kw: list[float]) -> list[Medicion]:
    return [Medicion(T0 + timedelta(minutes=5 * i), p) for i, p in enumerate(kw)]


def test_estimar_umbral_cae_en_el_valle_entre_ruido_y_eventos() -> None:
    from src.domain.cargas.services import estimar_umbral

    # Ruido de ±2 kW alrededor de 100 kW y una carga de 90 kW que entra y sale.
    base = [100 + (i % 5) - 2 for i in range(200)]
    kw = [p + (90 if (i // 10) % 2 else 0) for i, p in enumerate(base)]
    estimacion = estimar_umbral(_serie(kw))
    assert estimacion is not None
    assert 5 < estimacion.umbral_kw < 85
    assert estimacion.es_confiable(0.8)


def test_estimar_umbral_sin_variacion_no_estima() -> None:
    from src.domain.cargas.services import estimar_umbral

    assert estimar_umbral(_serie([100, 100, 100])) is None
    assert estimar_umbral(_serie([100])) is None


def test_histograma_reparte_hasta_el_percentil_99_y_junta_el_resto_al_final() -> None:
    from src.domain.cargas.services import histograma

    barras = histograma([float(v) for v in range(100)] + [10_000.0], barras=10)
    assert len(barras) == 10
    assert sum(b.cantidad for b in barras) == 101
    assert barras[0].desde_kw == 0
    assert barras[-1].hasta_kw == 99.0
    assert barras[-1].cantidad >= 2  # 99 y el valor extremo caen en la última barra
    assert histograma([]) == []
