"""src/infrastructure/sklearn/arbol_clasificador.py — Clasifica saltos de potencia con un árbol de decisión."""

from sklearn.tree import DecisionTreeClassifier, export_text

from src.domain.cargas.entities import Salto
from src.infrastructure.settings.logger import logger

RASGOS = ["ΔP", "ΔP_previo", "ΔP_siguiente"]


class ArbolClasificador:
    """Implementa ClasificadorSaltos: un árbol chico, para que sus reglas se puedan leer."""

    def __init__(self, profundidad: int = 6, semilla: int = 0) -> None:
        # class_weight="balanced": casi todos los saltos son "ninguna"; sin esto, el árbol
        # acierta mucho prediciendo siempre "ninguna" y nunca aprende las cargas chicas.
        self._modelo = DecisionTreeClassifier(
            max_depth=profundidad, class_weight="balanced", random_state=semilla
        )

    def entrenar(self, saltos: list[Salto], etiquetas: list[str]) -> None:
        self._modelo.fit([s.rasgos for s in saltos], etiquetas)
        logger.info(
            "Árbol entrenado con %d saltos: profundidad %d, %d hojas",
            len(saltos), self._modelo.get_depth(), self._modelo.get_n_leaves(),
        )  # fmt: skip

    def predecir(self, saltos: list[Salto]) -> list[str]:
        if not saltos:
            return []
        return [str(p) for p in self._modelo.predict([s.rasgos for s in saltos])]

    def explicar(self) -> str:
        return export_text(self._modelo, feature_names=RASGOS, decimals=1)
