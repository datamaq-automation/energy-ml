"""src/infrastructure/sklearn/extractor_reglas.py — Extracción de reglas desde árbol CART."""

from uuid import uuid4

from sklearn.tree import DecisionTreeClassifier

from src.domain.cargas.reglas import Condicion, ConjuntoReglas, Regla

RASGOS = ["ΔP", "ΔP_previo", "ΔP_siguiente"]


class ExtractorReglas:
    """Extrae reglas conjuntivas desde un árbol de decisión entrenado."""

    def __init__(self, modelo: DecisionTreeClassifier) -> None:
        self._modelo = modelo
        self._tree = modelo.tree_
        self._feature_names = RASGOS

    def extraer_reglas(self, numero_ejemplos: int = 0) -> ConjuntoReglas:
        """Extrae todas las reglas (caminos raíz-hoja) del árbol."""
        reglas: list[Regla] = []

        def _extraer_camino(node_id: int, condiciones: list[Condicion]) -> None:
            """Recorre recursivamente el árbol extrayendo caminos a hojas."""
            es_hoja = self._tree.feature[node_id] == -2

            if es_hoja:
                valores = self._tree.value[node_id][0]
                clase_predicha = str(self._modelo.classes_[valores.argmax()])
                soporte = int(self._tree.n_node_samples[node_id])

                if condiciones:
                    confianza_numerador = valores[
                        self._modelo.classes_.tolist().index(clase_predicha)
                    ]
                    confianza = float(confianza_numerador / soporte) if soporte > 0 else 0.0

                    regla = Regla(
                        id_regla=str(uuid4()),
                        condiciones=condiciones,
                        clase_predicha=clase_predicha,
                        soporte=soporte,
                        confianza=confianza,
                    )
                    reglas.append(regla)
            else:
                rasgo_idx = self._tree.feature[node_id]
                threshold = self._tree.threshold[node_id]
                rasgo_nombre = (
                    self._feature_names[rasgo_idx]
                    if rasgo_idx < len(self._feature_names)
                    else f"rasgo_{rasgo_idx}"
                )

                condicion_izq = Condicion(rasgo=rasgo_nombre, operador="<=", valor=threshold)
                condicion_der = Condicion(rasgo=rasgo_nombre, operador=">", valor=threshold)

                _extraer_camino(self._tree.children_left[node_id], condiciones + [condicion_izq])
                _extraer_camino(self._tree.children_right[node_id], condiciones + [condicion_der])

        _extraer_camino(0, [])

        reglas_ordenadas = sorted(reglas, key=lambda r: (-r.soporte, -r.confianza))

        return ConjuntoReglas(reglas=reglas_ordenadas, numero_ejemplos=numero_ejemplos)
