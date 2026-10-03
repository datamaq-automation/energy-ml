"""src/domain/cargas/services.py — Reglas de negocio puras para detectar y resumir cargas."""

from collections import defaultdict

from src.domain.cargas.entities import Carga, EventoCarga, Medicion


def detectar_eventos(mediciones: list[Medicion], umbral_kw: float) -> list[EventoCarga]:
    """Devuelve los saltos |ΔP| >= umbral entre mediciones consecutivas (ordenadas por instante)."""
    if umbral_kw <= 0:
        raise ValueError("El umbral debe ser positivo.")
    ordenadas = sorted(mediciones, key=lambda m: m.instante)
    eventos: list[EventoCarga] = []
    for previa, actual in zip(ordenadas, ordenadas[1:]):
        delta = actual.potencia_kw - previa.potencia_kw
        if abs(delta) >= umbral_kw:
            eventos.append(EventoCarga(instante=actual.instante, delta_kw=delta))
    return eventos


def resumir_cargas(eventos: list[EventoCarga], etiquetas: list[int]) -> list[Carga]:
    """Convierte eventos etiquetados en cargas candidatas, de mayor a menor potencia."""
    if len(eventos) != len(etiquetas):
        raise ValueError("Cada evento necesita exactamente una etiqueta.")
    grupos: dict[int, list[EventoCarga]] = defaultdict(list)
    for evento, etiqueta in zip(eventos, etiquetas):
        if etiqueta >= 0:
            grupos[etiqueta].append(evento)
    cargas = [
        Carga(
            potencia_tipica_kw=round(sum(abs(e.delta_kw) for e in grupo) / len(grupo), 1),
            encendidos=sum(e.es_encendido for e in grupo),
            apagados=sum(not e.es_encendido for e in grupo),
        )
        for grupo in grupos.values()
    ]
    return sorted(cargas, key=lambda c: c.potencia_tipica_kw, reverse=True)
