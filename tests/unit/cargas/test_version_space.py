"""tests/unit/cargas/test_version_space.py — Espacio de versiones: hipótesis, fronteras S/G y predicción."""

from datetime import datetime

from fastapi.testclient import TestClient

from src.application.cargas.dtos.version_space import PasoVersionSpaceRequest
from src.application.cargas.use_cases.actualizar_version_space import ActualizarVersionSpaceUseCase
from src.domain.cargas.entities import Salto
from src.domain.cargas.espacio_versiones import EstadoEspacioVersiones, Hipotesis, Restriccion
from src.domain.cargas.version_space_learner import VersionSpaceLearner
from src.main import app

RASGOS = ["ΔP", "ΔP_previo", "ΔP_siguiente"]


def salto(delta: float, previo: float = 0.0, siguiente: float = 0.0) -> Salto:
    return Salto(datetime(2026, 9, 20), delta, previo, siguiente)


def test_restriccion_universo_vacia_y_rango() -> None:
    assert Restriccion("ΔP", None, None).contiene(-1e9)
    rango = Restriccion("ΔP", 80, 100)
    assert rango.contiene(90) and not rango.contiene(79) and not rango.contiene(101)
    assert Restriccion("ΔP", 100, 80).es_vacio()
    assert Restriccion("ΔP", 80, None).contiene(1e9)


def test_hipotesis_igual_es_hasheable_y_se_deduplica() -> None:
    a = Hipotesis({"ΔP": Restriccion("ΔP", 80, 100)})
    b = Hipotesis({"ΔP": Restriccion("ΔP", 80, 100)})
    assert a == b and len({a, b}) == 1


def test_hipotesis_vacia_no_cubre_y_vuelve_inconsistente_el_estado() -> None:
    vacia = Hipotesis({"ΔP": Restriccion("ΔP", 100, 80)})
    assert vacia.es_vacio() and not vacia.cubre({"ΔP": 90})
    estado = EstadoEspacioVersiones(S={vacia}, G=set(), numero_ejemplos=1)
    assert not estado.es_consistente()
    assert estado.hipotesis_limite() == {vacia}


def test_especificar_amplia_el_rango_para_cubrir_el_ejemplo() -> None:
    h = Hipotesis({"ΔP": Restriccion("ΔP", 90, 90)}).especificar({"ΔP": 94, "ΔP_previo": 1})
    assert h.restricciones["ΔP"] == Restriccion("ΔP", 90, 94)
    assert h.restricciones["ΔP_previo"] == Restriccion("ΔP_previo", 1, 1)
    abierta = Hipotesis({"ΔP": Restriccion("ΔP", 90, None)}).especificar({"ΔP": 50})
    assert abierta.restricciones["ΔP"] == Restriccion("ΔP", 50, None)


def test_arranca_con_g_universal_y_s_vacia() -> None:
    estado = VersionSpaceLearner(RASGOS).obtener_estado()
    assert estado.S == set() and estado.numero_ejemplos == 0
    assert [h.es_universo() for h in estado.G] == [True]


def test_positivos_generalizan_s_hasta_cubrirlos() -> None:
    learner = VersionSpaceLearner(RASGOS)
    learner.actualizar(salto(90, 1, 0), "AB")
    assert learner.predecir(salto(90, 1, 0)) == "AB"
    assert learner.predecir(salto(10, 1, 0)) == "incierto"
    learner.actualizar(salto(94, 2, 1), "AB")
    assert learner.predecir(salto(92, 1.5, 0.5)) == "AB"
    assert learner.obtener_estado().numero_ejemplos == 2


def test_negativo_quita_las_hipotesis_que_lo_cubren() -> None:
    learner = VersionSpaceLearner(RASGOS)
    learner.actualizar(salto(90), "AB")
    learner.actualizar(salto(90), "ninguna")
    estado = learner.obtener_estado()
    assert estado.S == set() and estado.numero_ejemplos == 2
    assert learner.predecir(salto(500)) == "incierto"


def test_negativo_fuera_de_s_la_conserva() -> None:
    learner = VersionSpaceLearner(RASGOS)
    learner.actualizar(salto(90), "AB")
    learner.actualizar(salto(5), "ninguna")
    assert learner.predecir(salto(90)) == "AB"


def test_caso_de_uso_devuelve_las_fronteras() -> None:
    res = ActualizarVersionSpaceUseCase().execute(
        PasoVersionSpaceRequest(delta_kw=90, delta_previo_kw=1, delta_siguiente_kw=0, etiqueta="AB")
    )
    assert res.numero_ejemplos == 1 and res.es_consistente
    assert len(res.frontera_s) == 1 and not res.frontera_s[0].es_universo
    assert res.frontera_s[0].restricciones["ΔP"].minimo == 90


def test_endpoint_version_space_step() -> None:
    r = TestClient(app).post(
        "/api/v1/version-space/step",
        json={"delta_kw": 90, "delta_previo_kw": 1, "delta_siguiente_kw": 0, "etiqueta": "AB"},
    )
    assert r.status_code == 200
    assert r.json()["numero_ejemplos"] == 1
