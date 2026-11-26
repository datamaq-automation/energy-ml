"""src/domain/sibo/exceptions.py — Errores de negocio del seguimiento nutricional SIBO.

Heredan de LookupError para que la API siga respondiendo 404 cuando falta un
alimento o un registro, sin acoplar el dominio a FastAPI.
"""

from __future__ import annotations


class AlimentoNoEncontradoError(LookupError):
    """Se intentó registrar una comida con un alimento que no existe en la semilla."""

    def __init__(self, alimento_id: int) -> None:
        self.alimento_id = alimento_id
        super().__init__(f"No existe el alimento {alimento_id}")


class RegistroNoEncontradoError(LookupError):
    """Se intentó eliminar un registro que no está en el historial."""

    def __init__(self, registro_id: int) -> None:
        self.registro_id = registro_id
        super().__init__(f"No existe el registro {registro_id}")
