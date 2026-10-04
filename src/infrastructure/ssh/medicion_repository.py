"""src/infrastructure/ssh/medicion_repository.py — Exporta mediciones desde VPS via SSH + MySQL."""

import csv
import subprocess
from datetime import datetime
from pathlib import Path

from src.domain.cargas.entities import Medicion
from src.infrastructure.settings.logger import logger


class SshMedicionRepository:
    """Descarga mediciones del VPS (datamaq-telemetry MySQL) y las cachea en CSV locales."""

    # Mapeo: nombre real en VPS → nombre anonimizado en archivos
    MEDIDORES_MAPPING = {
        "Trafo arriba": "planta_2_a.csv",
        "Trafo abajo": "planta_2_b.csv",
    }

    SSH_HOST = "vps"
    SSH_TIMEOUT = 30  # segundos

    # Query MySQL para exportar mediciones confiables
    CONSULTA_SQL = """
    SELECT d.name, t.recorded_at, t.total_active_power
    FROM datamaq_telemetry.telemetry_instantaneous t
    JOIN datamaq_telemetry.devices d ON d.id = t.device_id
    WHERE t.total_active_power IS NOT NULL AND t.es_dato_confiable = 1
    ORDER BY d.name, t.recorded_at
    """

    def __init__(self, cache_dir: Path | str) -> None:
        """
        Args:
            cache_dir: Directorio donde cachear los CSV descargados (ej: data/prod-cache/)
        """
        self._cache_dir = Path(cache_dir)
        self._medidores_descargados: set[str] = set()

    def _descargar_desde_vps(self) -> dict[str, list[tuple[str, float]]]:
        """Ejecuta SSH + MySQL query en VPS y retorna datos por medidor.

        Raises:
            subprocess.CalledProcessError: Si SSH o MySQL fallan
            RuntimeError: Si la conexión es imposible (fail-fast)
        """
        logger.info(
            "📥 Conectando a VPS '%s' via SSH (timeout %ds)...", self.SSH_HOST, self.SSH_TIMEOUT
        )
        try:
            resultado = subprocess.run(
                [
                    "ssh",
                    "-o",
                    "BatchMode=yes",
                    "-o",
                    f"ConnectTimeout={self.SSH_TIMEOUT}",
                    self.SSH_HOST,
                    "mysql --batch --skip-column-names",
                ],
                input=self.CONSULTA_SQL,
                capture_output=True,
                text=True,
                timeout=self.SSH_TIMEOUT,
                check=True,
            )
        except subprocess.TimeoutExpired as e:
            logger.error("❌ SSH timeout (%ds) al conectar a '%s'", self.SSH_TIMEOUT, self.SSH_HOST)
            raise RuntimeError(
                f"Timeout SSH a '{self.SSH_HOST}' después de {self.SSH_TIMEOUT}s. "
                "Verificá: (1) Tailscale conectado, (2) Host 'vps' resuelve, (3) Claves SSH válidas"
            ) from e
        except subprocess.CalledProcessError as e:
            logger.error("❌ SSH/MySQL error: %s", e.stderr)
            raise RuntimeError(
                f"Error al conectar a VPS '{self.SSH_HOST}': {e.stderr}. "
                "Verificá: (1) Tailscale activo, (2) ~/.ssh/config con host '{self.SSH_HOST}', "
                "(3) Clave pública configurada en VPS"
            ) from e

        logger.info("✅ Descarga desde VPS completada. Procesando datos...")
        por_medidor: dict[str, list[tuple[str, float]]] = {}

        for linea in resultado.stdout.splitlines():
            if not linea.strip():
                continue
            partes = linea.split("\t")
            if len(partes) < 3:
                logger.warning("Línea malformada (ignorada): %s", linea)
                continue

            medidor, instante, potencia_w = partes[0], partes[1], partes[2]

            # Solo exportar medidores mapeados (anonimización)
            if medidor not in self.MEDIDORES_MAPPING:
                logger.debug("Medidor no mapeado (ignorado): %s", medidor)
                continue

            W_POR_KW = 1000.0
            instante_iso = instante.replace(
                " ", "T"
            )  # "2026-10-03 12:30:00" → "2026-10-03T12:30:00"
            potencia_kw = round(float(potencia_w) / W_POR_KW, 4)

            if medidor not in por_medidor:
                por_medidor[medidor] = []
            por_medidor[medidor].append((instante_iso, potencia_kw))

        logger.info("📊 Datos recuperados: %d medidores", len(por_medidor))
        for med, filas in por_medidor.items():
            logger.info("  - %s: %d registros", med, len(filas))

        return por_medidor

    def _cachear_en_csv(self, por_medidor: dict[str, list[tuple[str, float]]]) -> None:
        """Escribe los datos descargados en CSV locales (cache)."""
        self._cache_dir.mkdir(parents=True, exist_ok=True)

        for medidor, filas in por_medidor.items():
            archivo_local = self.MEDIDORES_MAPPING[medidor]
            ruta = self._cache_dir / archivo_local

            with ruta.open("w", newline="", encoding="utf-8") as f:
                escritor = csv.writer(f)
                escritor.writerow(["instante", "potencia_kw"])
                escritor.writerows(filas)

            logger.info("💾 Cacheado: %s → %s (%d registros)", medidor, ruta, len(filas))
            self._medidores_descargados.add(medidor)

    def medidores(self) -> list[str]:
        """Retorna lista de medidores disponibles (nombres anonimizados)."""
        nombres_anonimizados = {Path(v).stem for v in self.MEDIDORES_MAPPING.values()}
        return sorted(
            p.stem for p in self._cache_dir.glob("*.csv") if p.stem in nombres_anonimizados
        )

    def listar(self, medidor: str, desde: datetime, hasta: datetime) -> list[Medicion]:
        """Recupera mediciones para un medidor en rango temporal.

        Si es la primera llamada, descarga desde VPS. Llamadas posteriores usan cache local.

        Args:
            medidor: Nombre anonimizado (ej: "planta_2_a")
            desde: Fecha inicio (inclusiva)
            hasta: Fecha fin (exclusiva)

        Returns:
            Lista de Medicion filtradas por rango

        Raises:
            LookupError: Si medidor no existe
            RuntimeError: Si descarga SSH falla
        """
        # En la primera llamada, descargar desde VPS
        if not self._medidores_descargados:
            logger.info("🚀 Primera solicitud: descargando todos los medidores desde VPS...")
            por_medidor = self._descargar_desde_vps()
            self._cachear_en_csv(por_medidor)

        # Construir ruta del archivo cacheado
        medidor_real = None
        for real, anonimizado in self.MEDIDORES_MAPPING.items():
            if anonimizado.startswith(medidor):
                medidor_real = real
                break

        if not medidor_real:
            disponibles = ", ".join(self.MEDIDORES_MAPPING.values())
            logger.error("Medidor desconocido: %s (disponibles: %s)", medidor, disponibles)
            raise LookupError(f"Medidor desconocido: {medidor}")

        ruta = self._cache_dir / self.MEDIDORES_MAPPING[medidor_real]
        if not ruta.exists():
            logger.error("Cache ausente: %s (intenta nuevamente)", ruta)
            raise LookupError(f"Datos de {medidor} no disponibles en cache")

        logger.info("Leyendo %s", ruta)
        with ruta.open(encoding="utf-8") as archivo:
            filas = (
                Medicion(
                    instante=datetime.fromisoformat(f["instante"]),
                    potencia_kw=float(f["potencia_kw"]),
                )
                for f in csv.DictReader(archivo)
            )
            mediciones = [m for m in filas if desde <= m.instante < hasta]

        logger.info("%d mediciones dentro del rango [%s, %s)", len(mediciones), desde, hasta)
        return mediciones
