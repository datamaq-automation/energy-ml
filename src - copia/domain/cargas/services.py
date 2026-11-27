"""src/domain/cargas/services.py — Reglas de negocio puras para detectar y resumir cargas."""

from collections import defaultdict
from itertools import pairwise
from statistics import pstdev

from src.domain.cargas.entities import (
    BarraHistograma,
    Carga,
    EstimacionUmbral,
    EventoCarga,
    Medicion,
)


def detectar_eventos(mediciones: list[Medicion], umbral_kw: float) -> list[EventoCarga]:
    """Devuelve los saltos |ΔP| >= umbral entre mediciones consecutivas (ordenadas por instante)."""
    if umbral_kw <= 0:
        raise ValueError("El umbral debe ser positivo.")
    ordenadas = sorted(mediciones, key=lambda m: m.instante)
    eventos: list[EventoCarga] = []
    for previa, actual in pairwise(ordenadas):
        delta = actual.potencia_kw - previa.potencia_kw
        if abs(delta) >= umbral_kw:
            eventos.append(EventoCarga(instante=actual.instante, delta_kw=delta))
    return eventos


def saltos_kw(mediciones: list[Medicion]) -> list[float]:
    """|ΔP| entre mediciones consecutivas (ordenadas por instante)."""
    ordenadas = sorted(mediciones, key=lambda m: m.instante)
    return [abs(b.potencia_kw - a.potencia_kw) for a, b in pairwise(ordenadas)]


def histograma(valores: list[float], barras: int = 30) -> list[BarraHistograma]:
    """Histograma de 0 al percentil 99; la última barra junta también los valores más grandes."""
    if not valores or barras < 1:
        return []
    ordenados = sorted(valores)
    limite = ordenados[int(0.99 * (len(ordenados) - 1))] or ordenados[-1] or 1.0
    ancho = limite / barras
    cantidades = [0] * barras
    for v in ordenados:
        cantidades[min(int(v / ancho), barras - 1)] += 1
    return [
        BarraHistograma(
            desde_kw=round(i * ancho, 1), hasta_kw=round((i + 1) * ancho, 1), cantidad=c
        )
        for i, c in enumerate(cantidades)
    ]


def estimar_umbral(mediciones: list[Medicion]) -> EstimacionUmbral | None:
    """Elige el umbral |ΔP| con el método de Otsu: el corte que maximiza la varianza entre clases.

    Separa los saltos chicos (ruido: cargas que varían de a poco) de los grandes (encendidos y
    apagados). Devuelve None si no hay al menos dos valores distintos de |ΔP| para separar.
    """
    saltos = sorted(saltos_kw(mediciones))
    n, total = len(saltos), sum(saltos)
    if n < 2 or saltos[0] == saltos[-1]:
        return None
    media = total / n
    varianza_total = sum((x - media) ** 2 for x in saltos) / n
    mejor_varianza, mejor_corte, acumulado = 0.0, 1, 0.0
    for i in range(1, n):
        acumulado += saltos[i - 1]
        if saltos[i] == saltos[i - 1]:
            continue
        peso_ruido = i / n
        media_ruido, media_eventos = acumulado / i, (total - acumulado) / (n - i)
        varianza_entre = peso_ruido * (1 - peso_ruido) * (media_ruido - media_eventos) ** 2
        if varianza_entre > mejor_varianza:
            mejor_varianza, mejor_corte = varianza_entre, i
    umbral = (saltos[mejor_corte - 1] + saltos[mejor_corte]) / 2
    return EstimacionUmbral(
        umbral_kw=round(umbral, 1), separacion=round(mejor_varianza / varianza_total, 2)
    )


def nivel_de_ruido(mediciones: list[Medicion], umbral_kw: float) -> float:
    """Mediana de los saltos que NO llegan al umbral: cuánto "tiembla" la señal sin eventos."""
    ruido = sorted(s for s in saltos_kw(mediciones) if s < umbral_kw)
    return ruido[len(ruido) // 2] if ruido else 0.0


def estimar_radio(eventos: list[EventoCarga], ruido_kw: float = 0.0) -> float | None:
    """Radio de agrupamiento (eps de DBSCAN): el mayor entre Freedman–Diaconis y el ruido.

    - Freedman–Diaconis (2·IQR·n^(-1/3)) es el ancho "natural" para agrupar valores en una
      dimensión: crece con la dispersión de las magnitudes y se achica con más datos.
    - El ruido pone un piso físico: cada salto ya trae el ruido de dos mediciones, así que dos
      saltos de la misma carga (encendido de 89 kW, apagado de 91 kW) pueden diferir hasta en
      2 × ruido.
    Devuelve None si no hay eventos.
    """
    magnitudes = sorted(abs(e.delta_kw) for e in eventos)
    n = len(magnitudes)
    if n == 0:
        return None
    rango_intercuartil = magnitudes[int(0.75 * (n - 1))] - magnitudes[int(0.25 * (n - 1))]
    radio = 2 * rango_intercuartil * n ** (-1 / 3)
    # Si todos los saltos son casi iguales el IQR es 0: alcanza un radio mínimo para juntarlos.
    return round(max(radio, 2 * ruido_kw, 0.01 * magnitudes[n // 2], 0.1), 2)


def estimar_min_eventos(dias: float, minimo: int = 3) -> int:
    """Eventos mínimos para que un grupo sea una carga: en promedio, al menos uno por día analizado.

    Así el criterio no depende del largo del rango: 10 eventos en una semana es una carga
    frecuente; 10 eventos en tres meses, algo que casi no pasa. Nunca baja de `minimo`.
    """
    return max(minimo, round(dias))


def resumir_cargas(eventos: list[EventoCarga], etiquetas: list[int]) -> list[Carga]:
    """Convierte eventos etiquetados en cargas candidatas, de mayor a menor potencia."""
    if len(eventos) != len(etiquetas):
        raise ValueError("Cada evento necesita exactamente una etiqueta.")
    grupos: dict[int, list[EventoCarga]] = defaultdict(list)
    for evento, etiqueta in zip(eventos, etiquetas, strict=True):
        if etiqueta >= 0:
            grupos[etiqueta].append(evento)
    cargas = [
        Carga(
            potencia_tipica_kw=round(sum(abs(e.delta_kw) for e in grupo) / len(grupo), 1),
            encendidos=sum(e.es_encendido for e in grupo),
            apagados=sum(not e.es_encendido for e in grupo),
            dispersion_kw=round(pstdev(abs(e.delta_kw) for e in grupo), 1),
        )
        for grupo in grupos.values()
    ]
    return sorted(cargas, key=lambda c: c.potencia_tipica_kw, reverse=True)
