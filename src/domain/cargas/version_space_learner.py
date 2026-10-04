"""src/domain/cargas/version_space_learner.py — Algoritmo de aprendizaje por espacio de versiones."""

from src.domain.cargas.entities import Salto
from src.domain.cargas.espacio_versiones import EstadoEspacioVersiones, Hipotesis, Restriccion


class VersionSpaceLearner:
    """Mantiene el espacio de versiones: fronteras S y G de hipótesis."""

    def __init__(self, rasgos: list[str]) -> None:
        self._rasgos = rasgos
        self._estado = EstadoEspacioVersiones(
            S=set(),
            G={self._hipotesis_universo()},
            numero_ejemplos=0,
        )

    def _hipotesis_universo(self) -> Hipotesis:
        """Hipótesis más general: todos los rasgos sin restricción."""
        return Hipotesis({rasgo: Restriccion(rasgo, None, None) for rasgo in self._rasgos})

    def actualizar(self, salto: Salto, etiqueta: str) -> None:
        """Actualiza S y G dado un nuevo ejemplo etiquetado."""
        rasgos_dict = {self._rasgos[i]: valor for i, valor in enumerate(salto.rasgos)}

        if etiqueta == "ninguna":
            self._actualizar_negativo(rasgos_dict)
        else:
            self._actualizar_positivo(rasgos_dict, etiqueta)

        self._estado = EstadoEspacioVersiones(
            S=self._estado.S,
            G=self._estado.G,
            numero_ejemplos=self._estado.numero_ejemplos + 1,
        )

    def _actualizar_positivo(self, rasgos: dict[str, float], etiqueta: str) -> None:
        """El ejemplo es positivo: especializa S, generaliza G si es necesario."""
        S_nuevo = self._especializar_S(rasgos)
        G_nuevo = self._generalizar_G(rasgos, S_nuevo)

        self._estado.S.clear()
        self._estado.S.update(S_nuevo)
        self._estado.G.clear()
        self._estado.G.update(G_nuevo if G_nuevo else self._estado.G)

    def _especializar_S(self, rasgos: dict[str, float]) -> set[Hipotesis]:
        """Especializa la frontera S con el nuevo ejemplo positivo."""
        S_nuevo: set[Hipotesis] = set()
        for h_s in self._estado.S:
            if h_s.cubre(rasgos):
                S_nuevo.add(h_s)
            else:
                h_especializada = h_s.especificar(rasgos)
                if not h_especializada.es_vacio() and any(
                    h_g.cubre(rasgos) for h_g in self._estado.G
                ):
                    S_nuevo.add(h_especializada)

        if not S_nuevo:
            nueva_h = self._hipotesis_universo().especificar(rasgos)
            S_nuevo.add(nueva_h)
        return S_nuevo

    def _generalizar_G(self, rasgos: dict[str, float], S_nuevo: set[Hipotesis]) -> set[Hipotesis]:
        """Generaliza la frontera G consistente con S."""
        G_nuevo: set[Hipotesis] = set()
        for h_g in self._estado.G:
            if h_g.cubre(rasgos) or any(h_s.cubre(rasgos) for h_s in S_nuevo):
                G_nuevo.add(h_g)
            else:
                generalizadas = self._generalizar(h_g, rasgos)
                G_nuevo.update(
                    h for h in generalizadas if any(h_s.cubre(rasgos) for h_s in S_nuevo)
                )
        return G_nuevo

    def _actualizar_negativo(self, rasgos: dict[str, float]) -> None:
        """El ejemplo es negativo: elimina G que lo cubren, especializa S si es necesario."""
        G_nuevo: set[Hipotesis] = set()
        for h_g in self._estado.G:
            if not h_g.cubre(rasgos):
                G_nuevo.add(h_g)

        S_nuevo: set[Hipotesis] = set()
        for h_s in self._estado.S:
            if not h_s.cubre(rasgos):
                S_nuevo.add(h_s)

        self._estado.S.clear()
        self._estado.S.update(S_nuevo)
        self._estado.G.clear()
        self._estado.G.update(G_nuevo if G_nuevo else {self._hipotesis_universo()})

    def _generalizar(self, hipotesis: Hipotesis, rasgos: dict[str, float]) -> set[Hipotesis]:
        """Generaliza una hipótesis eliminando restricciones de un rasgo."""
        generalizadas: set[Hipotesis] = set()
        for rasgo in self._rasgos:
            restriccion_original = hipotesis.restricciones.get(
                rasgo, Restriccion(rasgo, None, None)
            )
            if not restriccion_original.es_universo():
                nuevas_restricciones = dict(hipotesis.restricciones)
                nuevas_restricciones[rasgo] = Restriccion(rasgo, None, None)
                generalizada = Hipotesis(nuevas_restricciones)
                generalizadas.add(generalizada)
        return generalizadas

    def obtener_estado(self) -> EstadoEspacioVersiones:
        """Retorna el estado actual del espacio de versiones."""
        return self._estado

    def predecir(self, salto: Salto) -> str:
        """Predice la etiqueta de un nuevo ejemplo usando el espacio de versiones."""
        rasgos_dict = {self._rasgos[i]: valor for i, valor in enumerate(salto.rasgos)}

        cubre_s = any(h.cubre(rasgos_dict) for h in self._estado.S)
        cubre_g = any(h.cubre(rasgos_dict) for h in self._estado.G)

        if cubre_s and cubre_g:
            return "AB"
        elif not cubre_s and not cubre_g:
            return "ninguna"
        else:
            return "incierto"
