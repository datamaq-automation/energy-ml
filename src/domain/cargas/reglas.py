"""src/domain/cargas/reglas.py — Entidades para reglas de clasificación inductivas."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Condicion:
    """Una condición atómica: rasgo comparador valor."""

    rasgo: str
    operador: str
    valor: float

    def a_texto(self) -> str:
        """Serializa la condición a texto legible."""
        return f"{self.rasgo} {self.operador} {self.valor:.2f}"


@dataclass(frozen=True)
class Regla:
    """Regla conjuntiva: TODAS las condiciones deben cumplirse para clasificar."""

    id_regla: str
    condiciones: list[Condicion]
    clase_predicha: str
    soporte: int
    confianza: float

    def __post_init__(self) -> None:
        if not self.condiciones:
            raise ValueError("Una regla debe tener al menos una condición")

    def cubre(self, rasgos: dict[str, float]) -> bool:
        """¿Este ejemplo cumple todas las condiciones de la regla?"""
        for condicion in self.condiciones:
            valor = rasgos.get(condicion.rasgo)
            if valor is None:
                return False
            if condicion.operador == "<=":
                if not (valor <= condicion.valor):
                    return False
            elif condicion.operador == ">":
                if not (valor > condicion.valor):
                    return False
            elif condicion.operador == "==":
                if not (abs(valor - condicion.valor) < 1e-6):
                    return False
        return True

    def a_texto(self) -> str:
        """Serializa la regla a texto legible."""
        condiciones_str = " AND ".join(c.a_texto() for c in self.condiciones)
        return f"IF {condiciones_str} THEN {self.clase_predicha} (soporte={self.soporte}, confianza={self.confianza:.2%})"


@dataclass(frozen=True)
class ConjuntoReglas:
    """Conjunto de reglas para clasificación."""

    reglas: list[Regla]
    numero_ejemplos: int

    def predecir(self, rasgos: dict[str, float]) -> str | None:
        """Predice usando la primera regla que cubre el ejemplo."""
        for regla in self.reglas:
            if regla.cubre(rasgos):
                return regla.clase_predicha
        return None

    def cobertura_total(self) -> float:
        """Fracción de ejemplos cubiertos por al menos una regla."""
        ejemplos_cubiertos = sum(r.soporte for r in self.reglas)
        return ejemplos_cubiertos / self.numero_ejemplos if self.numero_ejemplos > 0 else 0.0
