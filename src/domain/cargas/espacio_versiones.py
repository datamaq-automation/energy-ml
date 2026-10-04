"""src/domain/cargas/espacio_versiones.py — Entidades para Version Space Learning."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Restriccion:
    """Restricción de un rasgo: rango [min, max] o valor específico."""

    rasgo: str
    minimo: float | None
    maximo: float | None

    def es_universo(self) -> bool:
        """Restricción universal: acepta cualquier valor."""
        return self.minimo is None and self.maximo is None

    def es_vacio(self) -> bool:
        """Restricción vacía: no acepta ningún valor."""
        return self.minimo is not None and self.maximo is not None and self.minimo > self.maximo

    def contiene(self, valor: float) -> bool:
        """¿Este valor satisface la restricción?"""
        if self.es_universo():
            return True
        if self.minimo is not None and valor < self.minimo:
            return False
        if self.maximo is not None and valor > self.maximo:
            return False
        return True


@dataclass(frozen=True)
class Hipotesis:
    """Hipótesis conjuntiva: debe cumplir TODAS las restricciones de rasgos."""

    restricciones: dict[str, Restriccion]

    def es_universo(self) -> bool:
        """Hipótesis más general: acepta todo."""
        return all(r.es_universo() for r in self.restricciones.values())

    def es_vacio(self) -> bool:
        """Hipótesis vacía: no acepta nada."""
        return any(r.es_vacio() for r in self.restricciones.values())

    def cubre(self, rasgos: dict[str, float]) -> bool:
        """¿Esta hipótesis cubre (es consistente con) el ejemplo?"""
        if self.es_vacio():
            return False
        return all(
            self.restricciones.get(rasgo, Restriccion(rasgo, None, None)).contiene(valor)
            for rasgo, valor in rasgos.items()
        )

    def especificar(self, rasgos: dict[str, float]) -> "Hipotesis":
        """Devuelve la versión especializada para cubrir exactamente este ejemplo."""
        nuevas_restricciones = dict(self.restricciones)
        for rasgo, valor in rasgos.items():
            vieja_restriccion = nuevas_restricciones.get(rasgo, Restriccion(rasgo, None, None))
            if vieja_restriccion.es_universo():
                nuevas_restricciones[rasgo] = Restriccion(rasgo, valor, valor)
            else:
                min_val = vieja_restriccion.minimo
                max_val = vieja_restriccion.maximo
                if min_val is not None:
                    min_val = min(min_val, valor)
                else:
                    min_val = valor
                if max_val is not None:
                    max_val = max(max_val, valor)
                else:
                    max_val = valor
                nuevas_restricciones[rasgo] = Restriccion(rasgo, min_val, max_val)
        return Hipotesis(nuevas_restricciones)


@dataclass(frozen=True)
class EstadoEspacioVersiones:
    """Estado del espacio de versiones: fronteras específica (S) y general (G)."""

    S: set[Hipotesis]
    G: set[Hipotesis]
    numero_ejemplos: int

    def es_consistente(self) -> bool:
        """Espacio válido: S y G no deben ser vacíos o inconsistentes."""
        return not any(h.es_vacio() for h in self.S.union(self.G))

    def hipotesis_limite(self) -> set[Hipotesis]:
        """Todas las hipótesis válidas en la frontera del espacio."""
        return self.S.union(self.G)
