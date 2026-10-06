"""tests/unit/cargas/test_maquinas_inferidas.py — Tests para DTOs y UseCase de máquinas inferidas."""

from datetime import datetime

import pytest

from src.application.cargas.dtos.maquinas_inferidas import (
    ListaMaquinasInferidaDTO,
    MaquinaInferidaDTO,
)
from src.application.cargas.use_cases.consultar_maquinas_inferidas import (
    ConsultarMaquinasInferidaUseCase,
)


class MockRepositorioCacheMaquinas:
    """Mock de repositorio para testing."""

    def __init__(self, datos: dict | None = None):
        self.datos = datos

    def obtener(self, dispositivo_id: str) -> dict | None:
        if self.datos and self.datos.get("dispositivo_id") == dispositivo_id:
            return self.datos
        return None

    def guardar(self, dispositivo_id: str, datos: dict) -> None:
        self.datos = {**datos, "dispositivo_id": dispositivo_id}


# ============ DTO TESTS (T1) ============


class TestMaquinaInferidaDTO:
    """Tests para MaquinaInferidaDTO."""

    def test_creacion_valida(self):
        """DTO válido con todos los campos."""
        maquina = MaquinaInferidaDTO(
            id="carga_001",
            nombre="Bomba A",
            potencia_tipica_kw=92.5,
            confianza="alta",
            encendidos=412,
            apagados=380,
            ciclos_por_dia=24.5,
            dispersion_kw=3.2,
            timestamp_analisis=datetime(2026, 10, 5, 3, 30, 0),
            fuente="NILM-DBSCAN",
        )
        assert maquina.id == "carga_001"
        assert maquina.confianza == "alta"
        assert maquina.potencia_tipica_kw == 92.5

    def test_nombre_puede_ser_none(self):
        """Nombre puede ser None (sin nombre asignado)."""
        maquina = MaquinaInferidaDTO(
            id="carga_002",
            nombre=None,
            potencia_tipica_kw=45.0,
            confianza="media",
            encendidos=100,
            apagados=100,
            dispersion_kw=2.0,
            timestamp_analisis=datetime(2026, 10, 5, 3, 30, 0),
        )
        assert maquina.nombre is None

    def test_confianza_invalida_rechazada(self):
        """Confianza fuera de {alta, media, baja} debe fallar."""
        with pytest.raises(ValueError):
            MaquinaInferidaDTO(
                id="carga_003",
                nombre="Test",
                potencia_tipica_kw=50.0,
                confianza="muy_alta",  # ❌ inválido
                encendidos=10,
                apagados=10,
                dispersion_kw=1.0,
                timestamp_analisis=datetime(2026, 10, 5, 3, 30, 0),
            )

    def test_potencia_negativa_rechazada(self):
        """Potencia debe ser positiva."""
        with pytest.raises(ValueError):
            MaquinaInferidaDTO(
                id="carga_004",
                nombre="Test",
                potencia_tipica_kw=-50.0,  # ❌ negativa
                confianza="alta",
                encendidos=10,
                apagados=10,
                dispersion_kw=1.0,
                timestamp_analisis=datetime(2026, 10, 5, 3, 30, 0),
            )

    def test_ciclos_por_dia_puede_ser_none(self):
        """ciclos_por_dia puede ser None (rango < 1 día)."""
        maquina = MaquinaInferidaDTO(
            id="carga_005",
            nombre="Test",
            potencia_tipica_kw=50.0,
            confianza="baja",
            encendidos=1,
            apagados=1,
            ciclos_por_dia=None,  # ✓
            dispersion_kw=5.0,
            timestamp_analisis=datetime(2026, 10, 5, 3, 30, 0),
        )
        assert maquina.ciclos_por_dia is None


class TestListaMaquinasInferidaDTO:
    """Tests para ListaMaquinasInferidaDTO."""

    def test_lista_vacia_valida(self):
        """Lista vacía de máquinas es válida."""
        lista = ListaMaquinasInferidaDTO(
            dispositivo_id="planta_2_a",
            maquinas_inferidas=[],
            actualizado_en=datetime(2026, 10, 5, 3, 30, 0),
        )
        assert lista.maquinas_inferidas == []

    def test_lista_con_multiples_maquinas(self):
        """Lista con varias máquinas."""
        m1 = MaquinaInferidaDTO(
            id="c1",
            nombre="M1",
            potencia_tipica_kw=92.5,
            confianza="alta",
            encendidos=50,
            apagados=50,
            dispersion_kw=1.0,
            timestamp_analisis=datetime(2026, 10, 5, 3, 30, 0),
        )
        m2 = MaquinaInferidaDTO(
            id="c2",
            nombre="M2",
            potencia_tipica_kw=45.0,
            confianza="media",
            encendidos=25,
            apagados=25,
            dispersion_kw=3.0,
            timestamp_analisis=datetime(2026, 10, 5, 3, 30, 0),
        )
        lista = ListaMaquinasInferidaDTO(
            dispositivo_id="planta_2_a",
            maquinas_inferidas=[m1, m2],
            actualizado_en=datetime(2026, 10, 5, 3, 30, 0),
        )
        assert len(lista.maquinas_inferidas) == 2


# ============ USECASE TESTS (T2) ============


class TestConsultarMaquinasInferidaUseCase:
    """Tests para ConsultarMaquinasInferidaUseCase."""

    def test_calcular_confianza_alta(self):
        """Confianza alta si dispersion < 2.0, ciclos >= 10, encendidos >= 50."""
        use_case = ConsultarMaquinasInferidaUseCase(MockRepositorioCacheMaquinas())
        confianza = use_case._calcular_confianza(
            dispersion_kw=1.5,
            ciclos=15,
            encendidos=100,
        )
        assert confianza == "alta"

    def test_calcular_confianza_media(self):
        """Confianza media si dispersion < 5.0, ciclos >= 5, encendidos >= 20."""
        use_case = ConsultarMaquinasInferidaUseCase(MockRepositorioCacheMaquinas())
        confianza = use_case._calcular_confianza(
            dispersion_kw=3.0,
            ciclos=8,
            encendidos=30,
        )
        assert confianza == "media"

    def test_calcular_confianza_baja(self):
        """Confianza baja si no cumple criterios de alta ni media."""
        use_case = ConsultarMaquinasInferidaUseCase(MockRepositorioCacheMaquinas())
        confianza = use_case._calcular_confianza(
            dispersion_kw=6.0,  # > 5.0
            ciclos=2,  # < 5
            encendidos=10,  # < 20
        )
        assert confianza == "baja"

    def test_ejecutar_sin_datos_cachados_raise(self):
        """RuntimeError si no hay datos en cache."""
        repo = MockRepositorioCacheMaquinas(None)
        use_case = ConsultarMaquinasInferidaUseCase(repo)

        with pytest.raises(RuntimeError, match="Sin análisis NILM"):
            use_case.ejecutar("planta_2_a")

    def test_ejecutar_con_datos_cachados(self):
        """Retorna ListaMaquinasInferidaDTO con datos del cache."""
        datos_cache = {
            "dispositivo_id": "planta_2_a",
            "actualizado_en": "2026-10-05T03:30:00",
            "maquinas_inferidas": [
                {
                    "id": "carga_001",
                    "nombre": "Bomba A",
                    "potencia_tipica_kw": 92.5,
                    "encendidos": 412,
                    "apagados": 380,
                    "ciclos": 380,
                    "ciclos_por_dia": 24.5,
                    "dispersion_kw": 1.5,  # < 2.0
                    "timestamp_analisis": "2026-10-05T03:30:00",
                    "fuente": "NILM-DBSCAN",
                }
            ],
        }
        repo = MockRepositorioCacheMaquinas(datos_cache)
        use_case = ConsultarMaquinasInferidaUseCase(repo)

        resultado = use_case.ejecutar("planta_2_a")

        assert isinstance(resultado, ListaMaquinasInferidaDTO)
        assert resultado.dispositivo_id == "planta_2_a"
        assert len(resultado.maquinas_inferidas) == 1
        assert resultado.maquinas_inferidas[0].confianza == "alta"

    def test_ejecutar_confianza_media_en_dto(self):
        """Confianza correcta en DTO cuando es media."""
        datos_cache = {
            "dispositivo_id": "planta_2_b",
            "actualizado_en": "2026-10-05T03:30:00",
            "maquinas_inferidas": [
                {
                    "id": "carga_002",
                    "nombre": "Compresor B",
                    "potencia_tipica_kw": 45.0,
                    "encendidos": 198,
                    "apagados": 195,
                    "ciclos": 195,
                    "ciclos_por_dia": 12.1,
                    "dispersion_kw": 4.5,  # < 5.0, pero > 2.0
                    "timestamp_analisis": "2026-10-05T03:30:00",
                    "fuente": "NILM-DBSCAN",
                }
            ],
        }
        repo = MockRepositorioCacheMaquinas(datos_cache)
        use_case = ConsultarMaquinasInferidaUseCase(repo)

        resultado = use_case.ejecutar("planta_2_b")

        assert resultado.maquinas_inferidas[0].confianza == "media"

    def test_ejecutar_confianza_baja_en_dto(self):
        """Confianza correcta en DTO cuando es baja."""
        datos_cache = {
            "dispositivo_id": "planta_2_c",
            "actualizado_en": "2026-10-05T03:30:00",
            "maquinas_inferidas": [
                {
                    "id": "carga_003",
                    "nombre": "Ventilador C",
                    "potencia_tipica_kw": 15.0,
                    "encendidos": 8,
                    "apagados": 7,
                    "ciclos": 7,
                    "ciclos_por_dia": 2.1,
                    "dispersion_kw": 6.5,  # > 5.0
                    "timestamp_analisis": "2026-10-05T03:30:00",
                    "fuente": "NILM-DBSCAN",
                }
            ],
        }
        repo = MockRepositorioCacheMaquinas(datos_cache)
        use_case = ConsultarMaquinasInferidaUseCase(repo)

        resultado = use_case.ejecutar("planta_2_c")

        assert resultado.maquinas_inferidas[0].confianza == "baja"

    def test_ejecutar_multiples_maquinas(self):
        """Retorna varias máquinas con confianzas diferentes."""
        datos_cache = {
            "dispositivo_id": "planta_2_a",
            "actualizado_en": "2026-10-05T03:30:00",
            "maquinas_inferidas": [
                {
                    "id": "c1",
                    "nombre": "M1",
                    "potencia_tipica_kw": 92.5,
                    "encendidos": 412,
                    "apagados": 380,
                    "ciclos": 380,
                    "ciclos_por_dia": 24.5,
                    "dispersion_kw": 1.5,
                    "timestamp_analisis": "2026-10-05T03:30:00",
                },
                {
                    "id": "c2",
                    "nombre": "M2",
                    "potencia_tipica_kw": 45.0,
                    "encendidos": 100,
                    "apagados": 100,
                    "ciclos": 100,
                    "ciclos_por_dia": 12.0,
                    "dispersion_kw": 6.0,
                    "timestamp_analisis": "2026-10-05T03:30:00",
                },
            ],
        }
        repo = MockRepositorioCacheMaquinas(datos_cache)
        use_case = ConsultarMaquinasInferidaUseCase(repo)

        resultado = use_case.ejecutar("planta_2_a")

        assert len(resultado.maquinas_inferidas) == 2
        assert resultado.maquinas_inferidas[0].confianza == "alta"
        assert resultado.maquinas_inferidas[1].confianza == "baja"
