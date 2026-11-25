"""src/adapters/ventas/presentador.py — Convierte los resultados de ventas en renglones de texto legibles."""

from __future__ import annotations

from src.application.ventas.use_cases import ResultadoPronostico
from src.domain.ventas.modelos import Agrupamiento

NOMBRES_METODOS: dict[str, str] = {
    "ayer": "Igual que ayer",
    "lineal": "Regresión lineal",
    "bosque": "Bosque aleatorio",
}


def presentar_agrupamiento(agrupamiento: Agrupamiento) -> list[str]:
    """Tarea A: codo y silueta por k, y perfil de cada grupo."""
    renglones = [
        f"k={m.k}: inercia={m.inercia:.0f} | silueta={m.silueta:.3f}" for m in agrupamiento.metricas
    ]
    renglones += [
        f"Grupo {p.grupo}: {p.cantidad_series} series, vende {p.venta_media:.0f} unidades/día"
        for p in agrupamiento.perfiles
    ]
    return renglones


def presentar_pronostico(resultado: ResultadoPronostico) -> list[str]:
    """Tareas B y C: error de cada método en total y por grupo."""
    renglones = [
        f"{NOMBRES_METODOS.get(e.metodo, e.metodo)} -> MAE={e.mae:.1f} | RMSE={e.rmse:.1f}"
        for e in resultado.por_metodo
    ]
    renglones += [
        f"Grupo {e.grupo} | {NOMBRES_METODOS.get(e.metodo, e.metodo)} -> "
        f"MAE={e.mae:.1f} ({e.error_relativo:.0%} de {e.venta_media:.0f} unidades/día)"
        for e in resultado.por_grupo
    ]
    return renglones
