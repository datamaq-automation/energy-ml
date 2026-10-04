"""src/application/cargas/dtos/explicabilidad.py — DTOs para explicabilidad e interpretabilidad."""

from pydantic import BaseModel, ConfigDict, Field


class NodoArbolResponse(BaseModel):
    """Nodo del árbol de decisión: puede ser interno (decisión) o hoja (predicción)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    tipo: str = Field(description="'decision' o 'hoja'")
    rasgo: str | None = Field(None, description="Nombre del rasgo en nodos de decisión")
    threshold: float | None = Field(None, description="Umbral de comparación en nodos de decisión")
    clase: str | None = Field(None, description="Clase predicha en nodos hoja")
    muestras: int = Field(description="Cantidad de ejemplos de entrenamiento en este nodo")
    distribucion: dict[str, int] = Field(description="Conteo de ejemplos por clase en este nodo")
    izquierda: "NodoArbolResponse | None" = Field(
        None, description="Subárbol izquierdo (rasgo <= threshold)"
    )
    derecha: "NodoArbolResponse | None" = Field(
        None, description="Subárbol derecho (rasgo > threshold)"
    )


NodoArbolResponse.model_rebuild()


class ExplicarArbolResponse(BaseModel):
    """Árbol de decisión completo serializado a JSON."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    tipo: str = Field(description="Siempre 'arbol_clasificador'")
    rasgos: list[str] = Field(description="Nombres de los rasgos/features")
    clases: list[str] = Field(description="Clases que el árbol puede predecir")
    profundidad: int = Field(description="Profundidad máxima del árbol")
    hojas: int = Field(description="Número de nodos hoja")
    raiz: NodoArbolResponse = Field(description="Nodo raíz del árbol de decisión")
