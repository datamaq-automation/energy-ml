"""src/application/cargas/dtos/version_space.py — DTOs para Version Space Learning."""

from pydantic import BaseModel, ConfigDict, Field


class PasoVersionSpaceRequest(BaseModel):
    """Solicitud para actualizar el espacio de versiones con un nuevo ejemplo."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    delta_kw: float = Field(description="Salto de potencia ΔP en kW")
    delta_previo_kw: float = Field(description="Salto anterior ΔP_previo en kW")
    delta_siguiente_kw: float = Field(description="Salto siguiente ΔP_siguiente en kW")
    etiqueta: str = Field(description="Etiqueta del ejemplo: 'AB' (carga) o 'ninguna' (ruido)")


class RestriccionDTO(BaseModel):
    """Restricción de un rasgo en una hipótesis."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    rasgo: str = Field(description="Nombre del rasgo")
    minimo: float | None = Field(None, description="Límite inferior (None = sin restricción)")
    maximo: float | None = Field(None, description="Límite superior (None = sin restricción)")


class HipotesisDTO(BaseModel):
    """Hipótesis conjuntiva: conjunto de restricciones por rasgo."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    restricciones: dict[str, RestriccionDTO] = Field(description="Restricciones por rasgo")
    es_universo: bool = Field(description="¿Esta hipótesis es la más general?")
    es_vacia: bool = Field(description="¿Esta hipótesis no cubre ningún ejemplo?")


class EstadoVersionSpaceResponse(BaseModel):
    """Estado actual del espacio de versiones después de un paso."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    numero_ejemplos: int = Field(description="Cantidad de ejemplos vistos")
    frontera_s: list[HipotesisDTO] = Field(
        description="Frontera específica (hipótesis más específicas)"
    )
    frontera_g: list[HipotesisDTO] = Field(description="Frontera general (hipótesis más generales)")
    es_consistente: bool = Field(description="¿El espacio es válido y consistente?")
    tamano_espacio: int = Field(description="Cantidad total de hipótesis válidas (aproximado)")
