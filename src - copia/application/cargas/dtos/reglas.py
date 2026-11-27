"""src/application/cargas/dtos/reglas.py — DTOs para inducción y consulta de reglas."""

from pydantic import BaseModel, ConfigDict, Field


class CondicionDTO(BaseModel):
    """Una condición atómica en una regla."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    rasgo: str = Field(description="Nombre del rasgo/feature")
    operador: str = Field(description="Operador de comparación: '<=', '>', '=='")
    valor: float = Field(description="Valor de comparación")


class ReglaDTO(BaseModel):
    """Una regla de clasificación inductiva."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id_regla: str = Field(description="ID único de la regla")
    condiciones: list[CondicionDTO] = Field(description="Condiciones conjuntivas (AND)")
    clase_predicha: str = Field(description="Clase predicha si todas las condiciones se cumplen")
    soporte: int = Field(description="Cantidad de ejemplos cubiertos por esta regla")
    confianza: float = Field(
        ge=0.0,
        le=1.0,
        description="Fracción de ejemplos cubiertos que pertenecen a la clase predicha",
    )
    texto: str = Field(description="Representación textual de la regla")


class InducirReglasResponse(BaseModel):
    """Resultado de inducción de reglas desde el árbol."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    reglas: list[ReglaDTO] = Field(
        description="Reglas extraídas, ordenadas por soporte descendente"
    )
    numero_reglas: int = Field(description="Cantidad total de reglas extraídas")
    numero_ejemplos: int = Field(description="Cantidad de ejemplos en el conjunto de entrenamiento")
    cobertura_total: float = Field(
        ge=0.0, le=1.0, description="Fracción de ejemplos cubiertos por al menos una regla"
    )


class ObtenerReglaResponse(BaseModel):
    """Detalle de una regla específica."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    regla: ReglaDTO = Field(description="La regla solicitada")
    ejemplos_cubiertos: int = Field(description="Cantidad de ejemplos que cumplen esta regla")
    ejemplos_positivos: int = Field(description="De esos, cuántos son de la clase predicha")
    tasa_exito: float = Field(ge=0.0, le=1.0, description="Porcentaje de aciertos (confianza)")
