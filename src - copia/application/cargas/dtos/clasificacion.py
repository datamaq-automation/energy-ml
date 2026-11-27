"""src/application/cargas/dtos/clasificacion.py — Contratos de entrada/salida para inferencia supervisada."""

from pydantic import BaseModel, ConfigDict, Field


class ClassifyBayesRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    potencia_kva: float = Field(ge=0.0, description="Potencia aparente medida en el transformador")
    temperatura_aceite_c: float = Field(description="Temperatura del aceite aislante en °C")
    temperatura_devanados_c: float = Field(description="Temperatura de devanados en °C")
    corriente_a: float = Field(ge=0.0, description="Corriente eficaz de fase en Amperes")


class ClassifyBayesResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    estado: str = Field(description="Estado de contingencia predicho: NORMAL, ALERTA o CRITICA")
    probabilidades: dict[str, float] = Field(
        description="Probabilidades a posteriori calculadas por Naive Bayes"
    )
    es_contingencia: bool = Field(description="Indica si existe anomalía operativa")
    mensaje: str = Field(description="Recomendación o justificación del diagnóstico")


class VecinoDTO(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    clase: str = Field(description="Etiqueta de clase del vecino cercano")
    distancia: float = Field(ge=0.0, description="Distancia métrica estandarizada")


class ClassifyKNNRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    potencia_activa_kw: float = Field(description="Potencia activa medida")
    potencia_reactiva_kvar: float = Field(description="Potencia reactiva medida")
    thd_corriente: float = Field(ge=0.0, description="Distorsión armónica total de corriente (%)")
    factor_desbalance: float = Field(
        default=0.0, ge=0.0, description="Factor de desbalance entre fases"
    )
    k: int = Field(default=5, ge=1, le=50, description="Número de vecinos k")
    metrica: str = Field(
        default="euclidean", description="Métrica de distancia euclidiana o manhattan"
    )


class ClassifyKNNResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    clase_predicha: str = Field(description="Clase de carga predicha por k-NN")
    confianza: float = Field(ge=0.0, le=1.0, description="Confianza empírica del vecindario")
    distancia_promedio: float = Field(ge=0.0, description="Distancia euclidiana/manhattan promedio")
    vecinos: list[VecinoDTO] = Field(description="Lista de vecinos más cercanos")
