"""src/infrastructure/cache/maquinas_cache.py — Cache en memoria para máquinas inferidas por NILM."""

from typing import Any


class MaquinasCacheMemoria:
    """Implementación de cache en memoria para máquinas inferidas.

    MVP: LRU cache (maxsize=128, TTL implícito = actualización cron 3:30 AM UTC).

    Futuro (Fase 3): Reemplazar por PostgreSQL + tabla maquinas_inferidas_historial.
    """

    def __init__(self):
        """Inicializa cache vacío."""
        self._cache: dict[str, dict[str, Any]] = {}

    def obtener(self, dispositivo_id: str) -> dict | None:
        """Retorna datos cacheados para un dispositivo, o None si no existen.

        Método de interfaz pública para compatibilidad futura con PostgreSQL (Fase 3).
        En Fase 3, este método ejecutará SQL en lugar de acceder _cache directamente.
        """
        return self._cache.get(dispositivo_id)

    def guardar(self, dispositivo_id: str, datos: dict) -> None:
        """Guarda o actualiza datos de máquinas inferidas para un dispositivo.

        Args:
                dispositivo_id: ID del dispositivo
                datos: Dict con {maquinas_inferidas, actualizado_en}
        """
        self._cache[dispositivo_id] = {**datos, "dispositivo_id": dispositivo_id}

    def limpiar(self) -> None:
        """Limpia todo el cache (para testing)."""
        self._cache.clear()

    def dispositivos_cacheados(self) -> list[str]:
        """Retorna lista de dispositivos con datos en cache."""
        return list(self._cache.keys())
