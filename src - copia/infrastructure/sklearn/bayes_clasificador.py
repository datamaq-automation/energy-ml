"""src/infrastructure/sklearn/bayes_clasificador.py — Clasificador Naive Bayes Gaussiano para contingencias."""

from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.naive_bayes import GaussianNB

from src.domain.cargas.entities import DiagnosticoContingencia, TelemetriaTransformador
from src.infrastructure.settings.logger import logger

CLASES_CONTINGENCIA = ["NORMAL", "ALERTA", "CRITICA"]


class BayesClasificador:
    """Implementa ClasificadorBayes utilizando Naive Bayes Gaussiano."""

    def __init__(self, modelo: GaussianNB | None = None) -> None:
        self._modelo = modelo or GaussianNB()
        self._entrenado = modelo is not None

    def entrenar(self, X: list[list[float]], y: list[str]) -> None:
        self._modelo.fit(np.array(X), np.array(y))
        self._entrenado = True
        logger.info("Modelo Naive Bayes entrenado con %d ejemplos", len(X))

    def entrenar_con_defaults(self) -> None:
        """Entrena con perfiles sintéticos canónicos de transformadores de distribución."""
        rng = np.random.default_rng(42)
        X_list: list[list[float]] = []
        y_list: list[str] = []

        # Perfil NORMAL: 300-500 kVA, aceite 45-65°C, devanados 55-75°C, corriente 200-450 A
        for _ in range(120):
            p = float(rng.normal(400.0, 50.0))
            t_ac = float(rng.normal(55.0, 5.0))
            t_dev = float(rng.normal(65.0, 5.0))
            i = float(rng.normal(320.0, 40.0))
            X_list.append([max(0.0, p), t_ac, t_dev, max(0.0, i)])
            y_list.append("NORMAL")

        # Perfil ALERTA: 550-750 kVA, aceite 70-85°C, devanados 80-95°C, corriente 500-700 A
        for _ in range(80):
            p = float(rng.normal(650.0, 40.0))
            t_ac = float(rng.normal(78.0, 4.0))
            t_dev = float(rng.normal(88.0, 4.0))
            i = float(rng.normal(600.0, 40.0))
            X_list.append([p, t_ac, t_dev, i])
            y_list.append("ALERTA")

        # Perfil CRITICA: 800-1100 kVA, aceite 90-115°C, devanados 105-135°C, corriente 750-1000 A
        for _ in range(50):
            p = float(rng.normal(900.0, 60.0))
            t_ac = float(rng.normal(100.0, 7.0))
            t_dev = float(rng.normal(118.0, 8.0))
            i = float(rng.normal(850.0, 60.0))
            X_list.append([p, t_ac, t_dev, i])
            y_list.append("CRITICA")

        self.entrenar(X_list, y_list)

    def predecir_contingencia(self, telemetria: TelemetriaTransformador) -> DiagnosticoContingencia:
        if not self._entrenado:
            self.entrenar_con_defaults()

        x = np.array([telemetria.rasgos])
        clase_predicha = str(self._modelo.predict(x)[0])
        probas_arr = self._modelo.predict_proba(x)[0]
        clases_modelo = [str(c) for c in self._modelo.classes_]

        probabilidades: dict[str, float] = {
            c: round(float(p), 4) for c, p in zip(clases_modelo, probas_arr, strict=False)
        }

        es_contingencia = clase_predicha != "NORMAL"
        mensaje = (
            "Parámetros nominales estables"
            if not es_contingencia
            else f"Contingencia detectada: transformador en estado {clase_predicha}"
        )

        return DiagnosticoContingencia(
            estado=clase_predicha,
            probabilidades=probabilidades,
            es_contingencia=es_contingencia,
            mensaje=mensaje,
        )

    def guardar(self, ruta: Path | str) -> None:
        p = Path(ruta)
        p.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self._modelo, p)
        logger.info("Modelo Naive Bayes serializado en %s", p)

    @classmethod
    def cargar_o_entrenar(cls, ruta: Path | str) -> "BayesClasificador":
        p = Path(ruta)
        if p.exists():
            try:
                modelo_cargado: Any = joblib.load(p)
                if isinstance(modelo_cargado, GaussianNB):
                    logger.info("Modelo Naive Bayes cargado desde %s", p)
                    instancia = cls(modelo=modelo_cargado)
                    instancia._entrenado = True
                    return instancia
            except Exception as e:
                logger.warning("Fallo al deserializar %s: %s. Reentrenando...", p, e)

        instancia = cls()
        instancia.entrenar_con_defaults()
        instancia.guardar(p)
        return instancia
