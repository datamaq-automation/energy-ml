"""src/infrastructure/sklearn/arbol_clasificador.py — Clasifica saltos de potencia con un árbol de decisión."""

from sklearn.tree import DecisionTreeClassifier, export_text

from src.domain.cargas.entities import Salto
from src.infrastructure.settings.logger import logger
from src.infrastructure.sklearn.extractor_reglas import ExtractorReglas
from src.infrastructure.sklearn.serializador_arbol import SerializadorArbol

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

    def obtener_arbol_dict(self) -> dict:
        """Estructura del árbol serializada a diccionario (JSON-compatible)."""
        if not hasattr(self._modelo, "tree_") or self._modelo.tree_ is None:
            self._entrenar_default()

        serializador = SerializadorArbol(self._modelo)
        return serializador.serializar()

    def _entrenar_default(self) -> None:
        """Entrena el árbol con datos sintéticos si no está entrenado."""
        import numpy as np

        rng = np.random.default_rng(42)
        X = rng.normal(0, 1, (100, 3))
        y = np.where((X[:, 0] > 0) & (X[:, 1] > 0), "AB", "ninguna")
        self._modelo.fit(X, y)

    def obtener_reglas_dict(self) -> dict:
        """Reglas extraídas del árbol como lista de diccionarios."""
        if not hasattr(self._modelo, "tree_") or self._modelo.tree_ is None:
            self._entrenar_default()

        extractor = ExtractorReglas(self._modelo)
        conjunto = extractor.extraer_reglas()

        return {
            "reglas": [
                {
                    "id_regla": r.id_regla,
                    "condiciones": [
                        {"rasgo": c.rasgo, "operador": c.operador, "valor": c.valor}
                        for c in r.condiciones
                    ],
                    "clase_predicha": r.clase_predicha,
                    "soporte": r.soporte,
                    "confianza": r.confianza,
                    "texto": r.a_texto(),
                }
                for r in conjunto.reglas
            ],
            "numero_reglas": len(conjunto.reglas),
            "cobertura_total": conjunto.cobertura_total(),
        }
