"""src/application/cargas/use_cases/consultar_maquinas_inferidas.py — Consultar máquinas inferidas por NILM."""

from datetime import datetime

from src.application.cargas.dtos.maquinas_inferidas import (
    ListaMaquinasInferidaDTO,
    MaquinaInferidaDTO,
)
from src.domain.cargas.repositories import RepositorioCacheMaquinas


class ConsultarMaquinasInferidaUseCase:
    """Obtiene máquinas inferidas desde cache, calculando confianza."""

    # Reglas de confianza (puntos de decisión)
    CONFIANZA_ALTA = {
        "dispersion_max_kw": 2.0,
        "ciclos_min": 10,
        "encendidos_min": 50,
    }
    CONFIANZA_MEDIA = {
        "dispersion_max_kw": 5.0,
        "ciclos_min": 5,
        "encendidos_min": 20,
    }

    def __init__(self, cache_repo: RepositorioCacheMaquinas):
        self.cache_repo = cache_repo

    def ejecutar(self, dispositivo_id: str) -> ListaMaquinasInferidaDTO:
        """Consulta máquinas inferidas y retorna DTO con confianza calculada.

        Args:
            dispositivo_id: Identificador del dispositivo (ej: "planta_2_a")

        Returns:
            ListaMaquinasInferidaDTO con máquinas inferidas

        Raises:
            RuntimeError: Si no hay análisis NILM para el dispositivo
        """
        datos_cache = self.cache_repo.obtener(dispositivo_id)
        if not datos_cache:
            raise RuntimeError(
                f"Sin análisis NILM para dispositivo '{dispositivo_id}'. "
                "Ejecutar cron a las 3:30 AM UTC."
            )

        # Convertir cargas cacheadas a DTOs con confianza
        maquinas_dtos = [
            self._crear_maquina_dto(carga_dict)
            for carga_dict in datos_cache.get("maquinas_inferidas", [])
        ]

        return ListaMaquinasInferidaDTO(
            dispositivo_id=dispositivo_id,
            maquinas_inferidas=maquinas_dtos,
            actualizado_en=datetime.fromisoformat(datos_cache["actualizado_en"]),
        )

    def _crear_maquina_dto(self, carga_dict: dict) -> MaquinaInferidaDTO:
        """Convierte dict de carga cacheada a MaquinaInferidaDTO con confianza."""
        # Calcular confianza a partir de reglas
        confianza = self._calcular_confianza(
            dispersion_kw=carga_dict.get("dispersion_kw", 0.0),
            ciclos=carga_dict.get("ciclos", 0),
            encendidos=carga_dict.get("encendidos", 0),
        )

        return MaquinaInferidaDTO(
            id=carga_dict.get("id", f"carga_{carga_dict['potencia_tipica_kw']:.0f}kw"),
            nombre=carga_dict.get("nombre"),
            potencia_tipica_kw=carga_dict["potencia_tipica_kw"],
            confianza=confianza,
            encendidos=carga_dict["encendidos"],
            apagados=carga_dict["apagados"],
            ciclos_por_dia=carga_dict.get("ciclos_por_dia"),
            dispersion_kw=carga_dict.get("dispersion_kw", 0.0),
            timestamp_analisis=datetime.fromisoformat(carga_dict["timestamp_analisis"]),
            fuente=carga_dict.get("fuente", "NILM-DBSCAN"),
        )

    def _calcular_confianza(self, dispersion_kw: float, ciclos: int, encendidos: int) -> str:
        """Calcula confianza usando reglas determinísticas.

        Args:
            dispersion_kw: Desvío estándar de magnitudes, en kW
            ciclos: Min(encendidos, apagados)
            encendidos: Total de encendidos detectados

        Returns:
            "alta", "media" o "baja"

        Reglas:
            Alta: dispersion < 2.0 AND ciclos ≥ 10 AND encendidos ≥ 50
            Media: dispersion < 5.0 AND ciclos ≥ 5 AND encendidos ≥ 20
            Baja: resto
        """
        # Revisión de Alta
        if (
            dispersion_kw < self.CONFIANZA_ALTA["dispersion_max_kw"]
            and ciclos >= self.CONFIANZA_ALTA["ciclos_min"]
            and encendidos >= self.CONFIANZA_ALTA["encendidos_min"]
        ):
            return "alta"

        # Revisión de Media
        if (
            dispersion_kw < self.CONFIANZA_MEDIA["dispersion_max_kw"]
            and ciclos >= self.CONFIANZA_MEDIA["ciclos_min"]
            and encendidos >= self.CONFIANZA_MEDIA["encendidos_min"]
        ):
            return "media"

        # Resto es Baja
        return "baja"
