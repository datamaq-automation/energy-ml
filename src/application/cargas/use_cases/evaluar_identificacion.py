"""src/application/cargas/use_cases/evaluar_identificacion.py — Caso de uso: ¿qué tan bien acertó el algoritmo?"""

from src.application.cargas.dtos.identificar_cargas import IdentificarCargasRequest
from src.application.cargas.use_cases.identificar_cargas import IdentificarCargasUseCase
from src.domain.cargas.entities import Evaluacion, EventoDetectado
from src.domain.cargas.evaluacion import evaluar
from src.domain.cargas.repositories import Bitacora, VerdadRepository


class EvaluarIdentificacionUseCase:
    """Corre la identificación sobre un medidor simulado y la compara con sus eventos reales."""

    def __init__(self, identificar: IdentificarCargasUseCase, verdad: VerdadRepository, logger: Bitacora) -> None:
        self._identificar = identificar
        self._verdad = verdad
        self._logger = logger

    def execute(self, request: IdentificarCargasRequest) -> Evaluacion:
        resultado = self._identificar.execute(request)
        verdad = [e for e in self._verdad.listar(request.medidor) if request.desde <= e.instante < request.hasta]
        detectados = [EventoDetectado(e.instante, e.delta_kw, e.carga_kw) for e in resultado.detalle_eventos]
        evaluacion = evaluar(detectados, verdad)
        self._informar(evaluacion)
        return evaluacion

    def _informar(self, evaluacion: Evaluacion) -> None:
        self._logger.info("Evaluación contra la verdad (una carga está bien asignada si su potencia está a ±20 %)")
        for r in evaluacion.por_carga:
            estimada = f"~{r.potencia_estimada_kw} kW" if r.potencia_estimada_kw is not None else "no encontrada"
            self._logger.info(
                "Carga real de %s kW: %d eventos, %d detectados, %d bien asignados (sensibilidad %.0f %%) → %s",
                r.potencia_real_kw, r.eventos_reales, r.detectados, r.bien_asignados, 100 * r.sensibilidad, estimada,
            )  # fmt: skip
            if r.potencia_estimada_kw is None:
                self._logger.warning("La carga real de %s kW no se encontró", r.potencia_real_kw)
        self._logger.info(
            "Precisión: %.0f %% de los %d eventos detectados corresponden a algo que pasó (%d falsos positivos)",
            100 * evaluacion.precision, evaluacion.eventos_detectados, evaluacion.falsos_positivos,
        )  # fmt: skip
        for kw in evaluacion.cargas_inventadas:
            self._logger.warning("Carga inventada: ~%s kW no se parece a ninguna carga real", kw)
