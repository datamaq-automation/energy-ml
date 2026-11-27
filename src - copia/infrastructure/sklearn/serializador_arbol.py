"""src/infrastructure/sklearn/serializador_arbol.py — Serialización recursiva de DecisionTreeClassifier a JSON."""

from sklearn.tree import DecisionTreeClassifier

RASGOS = ["ΔP", "ΔP_previo", "ΔP_siguiente"]


class NodoArbol:
    """Nodo de árbol: puede ser interno (decisión) o hoja (predicción)."""

    __slots__ = (
        "es_hoja",
        "clase",
        "valor_threshold",
        "rasgo",
        "hijo_izq",
        "hijo_der",
        "muestras",
        "clases",
    )

    def __init__(
        self,
        es_hoja: bool,
        clase: str | None = None,
        valor_threshold: float | None = None,
        rasgo: str | None = None,
        hijo_izq: "NodoArbol | None" = None,
        hijo_der: "NodoArbol | None" = None,
        muestras: int = 0,
        clases: dict[str, int] | None = None,
    ) -> None:
        self.es_hoja = es_hoja
        self.clase = clase
        self.valor_threshold = valor_threshold
        self.rasgo = rasgo
        self.hijo_izq = hijo_izq
        self.hijo_der = hijo_der
        self.muestras = muestras
        self.clases = clases or {}

    def a_dict(self) -> dict:
        """Serializa el nodo a diccionario (recursivamente)."""
        if self.es_hoja:
            return {
                "tipo": "hoja",
                "clase": self.clase,
                "muestras": self.muestras,
                "distribucion": self.clases,
            }
        return {
            "tipo": "decision",
            "rasgo": self.rasgo,
            "threshold": round(self.valor_threshold, 2)
            if self.valor_threshold is not None
            else None,
            "muestras": self.muestras,
            "distribucion": self.clases,
            "izquierda": self.hijo_izq.a_dict() if self.hijo_izq else None,
            "derecha": self.hijo_der.a_dict() if self.hijo_der else None,
        }


class SerializadorArbol:
    """Convierte DecisionTreeClassifier sklearn a estructura de árbol recursiva."""

    def __init__(self, modelo: DecisionTreeClassifier) -> None:
        self._modelo = modelo
        self._tree = modelo.tree_
        self._feature_names = RASGOS

    def serializar(self) -> dict:
        """Retorna el árbol completo como diccionario (JSON-serializable)."""
        raiz = self._construir_nodo(0)
        return {
            "tipo": "arbol_clasificador",
            "rasgos": self._feature_names,
            "clases": list(self._modelo.classes_),
            "profundidad": self._modelo.get_depth(),
            "hojas": self._modelo.get_n_leaves(),
            "raiz": raiz.a_dict(),
        }

    def _construir_nodo(self, node_id: int) -> NodoArbol:
        """Construye recursivamente un nodo del árbol sklearn."""
        es_hoja = self._tree.feature[node_id] == -2

        if es_hoja:
            valores = self._tree.value[node_id][0]
            clases_str = {
                str(c): int(v) for c, v in zip(self._modelo.classes_, valores, strict=False)
            }
            clase_predicha = self._modelo.classes_[valores.argmax()]

            return NodoArbol(
                es_hoja=True,
                clase=str(clase_predicha),
                muestras=int(self._tree.n_node_samples[node_id]),
                clases=clases_str,
            )

        rasgo_idx = self._tree.feature[node_id]
        threshold = self._tree.threshold[node_id]
        rasgo_nombre = (
            self._feature_names[rasgo_idx]
            if rasgo_idx < len(self._feature_names)
            else f"rasgo_{rasgo_idx}"
        )

        hijo_izq_id = self._tree.children_left[node_id]
        hijo_der_id = self._tree.children_right[node_id]

        hijo_izq = self._construir_nodo(hijo_izq_id)
        hijo_der = self._construir_nodo(hijo_der_id)

        valores = self._tree.value[node_id][0]
        clases_str = {str(c): int(v) for c, v in zip(self._modelo.classes_, valores, strict=False)}

        return NodoArbol(
            es_hoja=False,
            valor_threshold=threshold,
            rasgo=rasgo_nombre,
            hijo_izq=hijo_izq,
            hijo_der=hijo_der,
            muestras=int(self._tree.n_node_samples[node_id]),
            clases=clases_str,
        )
