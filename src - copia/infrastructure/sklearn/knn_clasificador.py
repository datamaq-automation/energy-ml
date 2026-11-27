"""src/infrastructure/sklearn/knn_clasificador.py — Clasificador k-NN con StandardScaler para firmas eléctricas."""

from collections import Counter
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler

from src.domain.cargas.entities import DiagnosticoFirma, FirmaElectrica, VecinoCercano
from src.infrastructure.settings.logger import logger

CLASES_CARGA = [
    "MOTOR_INDUCCION",
    "COMPRESOR",
    "ILUMINACION_LED",
    "RESISTENCIA_TERMICA",
]


class KNNClasificador:
    """Implementa ClasificadorKNN con normalización z-score y cálculo de vecindario."""

    def __init__(
        self,
        scaler: StandardScaler | None = None,
        knn: KNeighborsClassifier | None = None,
        etiquetas: list[str] | None = None,
    ) -> None:
        self._scaler = scaler or StandardScaler()
        self._knn = knn or KNeighborsClassifier(n_neighbors=5, metric="euclidean")
        self._etiquetas = etiquetas or []
        self._entrenado = knn is not None and etiquetas is not None and len(etiquetas) > 0

    def entrenar(self, X: list[list[float]], y: list[str]) -> None:
        x_arr = np.array(X)
        x_scaled = self._scaler.fit_transform(x_arr)
        self._knn.fit(x_scaled, y)
        self._etiquetas = list(y)
        self._entrenado = True
        logger.info("Modelo k-NN entrenado con %d firmas eléctricas", len(X))

    def entrenar_con_defaults(self) -> None:
        """Entrena con firmas eléctricas industriales típicas."""
        rng = np.random.default_rng(101)
        X_list: list[list[float]] = []
        y_list: list[str] = []

        # MOTOR_INDUCCION: P ~ 25-45 kW, Q ~ 18-35 kvar, THD ~ 4-7%, desbalance ~ 1-3%
        for _ in range(60):
            p = float(rng.normal(30.0, 4.0))
            q = float(rng.normal(22.0, 3.0))
            thd = float(rng.normal(5.0, 0.8))
            desb = float(rng.normal(2.0, 0.4))
            X_list.append([p, q, max(0.1, thd), max(0.0, desb)])
            y_list.append("MOTOR_INDUCCION")

        # COMPRESOR: P ~ 60-110 kW, Q ~ 40-70 kvar, THD ~ 6-10%, desbalance ~ 1.5-4%
        for _ in range(60):
            p = float(rng.normal(85.0, 8.0))
            q = float(rng.normal(55.0, 6.0))
            thd = float(rng.normal(7.5, 1.0))
            desb = float(rng.normal(2.8, 0.5))
            X_list.append([p, q, max(0.1, thd), max(0.0, desb)])
            y_list.append("COMPRESOR")

        # ILUMINACION_LED: P ~ 3-12 kW, Q ~ -1 a 2 kvar, THD ~ 15-28%, desbalance ~ 0.5-2%
        for _ in range(60):
            p = float(rng.normal(6.0, 1.5))
            q = float(rng.normal(0.5, 0.4))
            thd = float(rng.normal(20.0, 2.5))
            desb = float(rng.normal(1.0, 0.3))
            X_list.append([p, q, max(0.1, thd), max(0.0, desb)])
            y_list.append("ILUMINACION_LED")

        # RESISTENCIA_TERMICA: P ~ 30-75 kW, Q ~ 0-1.5 kvar, THD ~ 1-2.5%, desbalance ~ 0.2-1%
        for _ in range(60):
            p = float(rng.normal(50.0, 6.0))
            q = float(rng.normal(0.6, 0.2))
            thd = float(rng.normal(1.5, 0.3))
            desb = float(rng.normal(0.5, 0.15))
            X_list.append([p, q, max(0.1, thd), max(0.0, desb)])
            y_list.append("RESISTENCIA_TERMICA")

        self.entrenar(X_list, y_list)

    def clasificar_firma(
        self,
        firma: FirmaElectrica,
        k: int = 5,
        metrica: str = "euclidean",
    ) -> DiagnosticoFirma:
        if not self._entrenado:
            self.entrenar_con_defaults()

        x = np.array([firma.rasgos])
        x_scaled = self._scaler.transform(x)

        if self._knn.metric != metrica:
            self._knn.metric = metrica

        k_val = min(k, len(self._etiquetas))
        distancias, indices = self._knn.kneighbors(
            x_scaled, n_neighbors=k_val, return_distance=True
        )

        dist_arr = distancias[0]
        idx_arr = indices[0]

        vecinos: list[VecinoCercano] = [
            VecinoCercano(
                clase=self._etiquetas[idx],
                distancia=float(dist),
            )
            for dist, idx in zip(dist_arr, idx_arr, strict=False)
        ]

        clases_vecinos = [v.clase for v in vecinos]
        contador = Counter(clases_vecinos)
        clase_predicha, votos = contador.most_common(1)[0]
        confianza = votos / len(vecinos) if vecinos else 0.0
        distancia_promedio = float(np.mean(dist_arr)) if len(dist_arr) > 0 else 0.0

        return DiagnosticoFirma(
            clase_predicha=clase_predicha,
            confianza=confianza,
            distancia_promedio=distancia_promedio,
            vecinos=vecinos,
        )

    def guardar(self, ruta: Path | str) -> None:
        p = Path(ruta)
        p.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "scaler": self._scaler,
            "knn": self._knn,
            "etiquetas": self._etiquetas,
        }
        joblib.dump(payload, p)
        logger.info("Modelo k-NN serializado en %s", p)

    @classmethod
    def cargar_o_entrenar(cls, ruta: Path | str) -> "KNNClasificador":
        p = Path(ruta)
        if p.exists():
            try:
                data: Any = joblib.load(p)
                if isinstance(data, dict) and "scaler" in data and "knn" in data:
                    logger.info("Modelo k-NN cargado desde %s", p)
                    instancia = cls(
                        scaler=data["scaler"],
                        knn=data["knn"],
                        etiquetas=data.get("etiquetas", []),
                    )
                    instancia._entrenado = True
                    return instancia
            except Exception as e:
                logger.warning("Fallo al deserializar %s: %s. Reentrenando...", p, e)

        instancia = cls()
        instancia.entrenar_con_defaults()
        instancia.guardar(p)
        return instancia
