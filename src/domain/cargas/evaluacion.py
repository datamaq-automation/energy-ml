"""src/domain/cargas/evaluacion.py — Comparar lo detectado con la verdad de un tablero simulado."""

from collections import defaultdict

from src.domain.cargas.entities import Evaluacion, EventoDetectado, EventoReal, ResultadoCarga


def evaluar(detectados: list[EventoDetectado], verdad: list[EventoReal], tolerancia: float = 0.2) -> Evaluacion:
    """Empareja por instante y signo, y considera bien asignado un evento si su carga está a ±tolerancia.

    - Un evento real está **detectado** si en ese instante hay un evento detectado del mismo signo.
    - Está **bien asignado** si además el algoritmo lo puso en una carga de potencia parecida.
    - Un evento detectado es **falso positivo** si en ese instante no pasó nada.
    - Una carga es **inventada** si no se parece a ninguna carga real.
    """
    por_instante = {(d.instante, d.delta_kw > 0): d for d in detectados}
    reales = sorted({e.carga_kw for e in verdad}, reverse=True)
    cuentas: dict[float, list[int]] = defaultdict(lambda: [0, 0, 0])
    for evento in verdad:
        cuenta = cuentas[evento.carga_kw]
        cuenta[0] += 1
        detectado = por_instante.get((evento.instante, evento.delta_kw > 0))
        if detectado is not None:
            cuenta[1] += 1
            if detectado.carga_kw is not None and _parecida(detectado.carga_kw, evento.carga_kw, tolerancia):
                cuenta[2] += 1
    encontradas = sorted({d.carga_kw for d in detectados if d.carga_kw is not None}, reverse=True)
    instantes_reales = {(e.instante, e.delta_kw > 0) for e in verdad}
    return Evaluacion(
        por_carga=[
            ResultadoCarga(
                potencia_real_kw=kw,
                eventos_reales=cuentas[kw][0],
                detectados=cuentas[kw][1],
                bien_asignados=cuentas[kw][2],
                potencia_estimada_kw=next((e for e in encontradas if _parecida(e, kw, tolerancia)), None),
            )
            for kw in reales
        ],
        eventos_detectados=len(detectados),
        falsos_positivos=sum((d.instante, d.delta_kw > 0) not in instantes_reales for d in detectados),
        cargas_inventadas=[e for e in encontradas if not any(_parecida(e, kw, tolerancia) for kw in reales)],
    )


def _parecida(estimada_kw: float, real_kw: float, tolerancia: float) -> bool:
    return abs(estimada_kw - real_kw) <= tolerancia * real_kw
