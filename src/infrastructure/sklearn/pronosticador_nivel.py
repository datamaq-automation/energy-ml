"""src/infrastructure/sklearn/pronosticador_nivel.py ? Implementaci?n del m?dulo."""

from sklearn.linear_model import LinearRegression


class PronosticadorNivel:
    """Implementa un predictor de niveles mediante regresión lineal."""

    def __init__(self) -> None:
        self._modelo = LinearRegression()
        self._entrenado = False

    def entrenar(self, variables: list[list[float]], objetivos: list[float]) -> None:
        """Ajusta el modelo con observaciones históricas."""
        if len(variables) != len(objetivos) or not variables:
            raise ValueError("Se necesitan variables y objetivos de igual longitud.")
        self._modelo.fit(variables, objetivos)
        self._entrenado = True

    def predecir(self, variables: list[list[float]]) -> list[float]:
        """Predice niveles para uno o varios conjuntos de variables."""
        if not self._entrenado:
            raise RuntimeError("El pronosticador todavía no fue entrenado.")
        if not variables:
            return []
        return self._modelo.predict(variables).tolist()
