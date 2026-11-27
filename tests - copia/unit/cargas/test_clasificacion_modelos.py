"""tests/unit/cargas/test_clasificacion_modelos.py — Pruebas unitarias para clasificadores Bayes y k-NN."""

from pathlib import Path

from src.application.cargas.dtos.clasificacion import (
    ClassifyBayesRequest,
    ClassifyKNNRequest,
)
from src.application.cargas.use_cases.clasificar_bayes import ClasificarBayesUseCase
from src.application.cargas.use_cases.clasificar_knn import ClasificarKNNUseCase
from src.domain.cargas.entities import FirmaElectrica, TelemetriaTransformador
from src.infrastructure.sklearn.bayes_clasificador import BayesClasificador
from src.infrastructure.sklearn.knn_clasificador import KNNClasificador


def test_bayes_clasificador_entrenamiento_y_prediccion() -> None:
    clasificador = BayesClasificador()
    clasificador.entrenar_con_defaults()

    # Muestra con parámetros normales
    telemetria_normal = TelemetriaTransformador(
        potencia_kva=400.0,
        temperatura_aceite_c=55.0,
        temperatura_devanados_c=65.0,
        corriente_a=320.0,
    )
    diagnostico_normal = clasificador.predecir_contingencia(telemetria_normal)
    assert diagnostico_normal.estado == "NORMAL"
    assert not diagnostico_normal.es_contingencia
    assert diagnostico_normal.probabilidades["NORMAL"] > 0.5

    # Muestra con parámetros críticos
    telemetria_critica = TelemetriaTransformador(
        potencia_kva=950.0,
        temperatura_aceite_c=105.0,
        temperatura_devanados_c=125.0,
        corriente_a=900.0,
    )
    diagnostico_critico = clasificador.predecir_contingencia(telemetria_critica)
    assert diagnostico_critico.estado == "CRITICA"
    assert diagnostico_critico.es_contingencia


def test_bayes_clasificador_persistencia_joblib(tmp_path: Path) -> None:
    ruta = tmp_path / "modelos" / "bayes.joblib"
    BayesClasificador.cargar_o_entrenar(ruta)
    assert ruta.exists()

    # Cargar existente
    clasificador_cargado = BayesClasificador.cargar_o_entrenar(ruta)
    telemetria = TelemetriaTransformador(
        potencia_kva=400.0,
        temperatura_aceite_c=55.0,
        temperatura_devanados_c=65.0,
        corriente_a=320.0,
    )
    diag = clasificador_cargado.predecir_contingencia(telemetria)
    assert diag.estado in ("NORMAL", "ALERTA", "CRITICA")


def test_knn_clasificador_entrenamiento_y_prediccion() -> None:
    clasificador = KNNClasificador()
    clasificador.entrenar_con_defaults()

    # Firma típica de LED (alto THD, potencia baja)
    firma_led = FirmaElectrica(
        potencia_activa_kw=6.0,
        potencia_reactiva_kvar=0.5,
        thd_corriente=20.0,
        factor_desbalance=1.0,
    )
    diag_led = clasificador.clasificar_firma(firma_led, k=5)
    assert diag_led.clase_predicha == "ILUMINACION_LED"
    assert diag_led.confianza >= 0.6
    assert len(diag_led.vecinos) == 5

    # Firma típica de Motor de Inducción
    firma_motor = FirmaElectrica(
        potencia_activa_kw=30.0,
        potencia_reactiva_kvar=22.0,
        thd_corriente=5.0,
        factor_desbalance=2.0,
    )
    diag_motor = clasificador.clasificar_firma(firma_motor, k=5)
    assert diag_motor.clase_predicha == "MOTOR_INDUCCION"


def test_knn_clasificador_persistencia_joblib(tmp_path: Path) -> None:
    ruta = tmp_path / "modelos" / "knn.joblib"
    KNNClasificador.cargar_o_entrenar(ruta)
    assert ruta.exists()

    clasificador_cargado = KNNClasificador.cargar_o_entrenar(ruta)
    firma = FirmaElectrica(
        potencia_activa_kw=50.0,
        potencia_reactiva_kvar=0.6,
        thd_corriente=1.5,
        factor_desbalance=0.5,
    )
    diag = clasificador_cargado.clasificar_firma(firma, k=3)
    assert diag.clase_predicha == "RESISTENCIA_TERMICA"


def test_casos_de_uso_clasificacion() -> None:
    bayes = BayesClasificador()
    bayes.entrenar_con_defaults()
    uc_bayes = ClasificarBayesUseCase(bayes)

    req_bayes = ClassifyBayesRequest(
        potencia_kva=400.0,
        temperatura_aceite_c=55.0,
        temperatura_devanados_c=65.0,
        corriente_a=320.0,
    )
    res_bayes = uc_bayes.execute(req_bayes)
    assert res_bayes.estado == "NORMAL"
    assert not res_bayes.es_contingencia

    knn = KNNClasificador()
    knn.entrenar_con_defaults()
    uc_knn = ClasificarKNNUseCase(knn)

    req_knn = ClassifyKNNRequest(
        potencia_activa_kw=85.0,
        potencia_reactiva_kvar=55.0,
        thd_corriente=7.5,
        factor_desbalance=2.8,
        k=3,
        metrica="euclidean",
    )
    res_knn = uc_knn.execute(req_knn)
    assert res_knn.clase_predicha == "COMPRESOR"
    assert len(res_knn.vecinos) == 3
