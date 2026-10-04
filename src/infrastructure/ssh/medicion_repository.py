"""src/infrastructure/ssh/medicion_repository.py — Exporta mediciones desde VPS via SSH + MySQL."""

import csv
import re
import subprocess
import time
import unicodedata
from datetime import datetime
from pathlib import Path

from src.domain.cargas.entities import Medicion
from src.infrastructure.settings.logger import logger


class SshMedicionRepository:
    """Descarga mediciones del VPS (datamaq-telemetry MySQL) y las cachea en CSV locales.

    Una sola descarga por proceso (guardada en `_sincronizado`).
    """

    # Alias conocidos: nombre real en VPS → nombre anonimizado
    ALIASES_CONOCIDOS = {
        "Trafo arriba": "planta_2_a.csv",
        "Trafo abajo": "planta_2_b.csv",
    }

    SSH_HOST = "vps"
    SSH_TIMEOUT = 30

    CONSULTA_SQL = """
    SELECT d.name, t.recorded_at, t.total_active_power
    FROM datamaq_telemetry.telemetry_instantaneous t
    JOIN datamaq_telemetry.devices d ON d.id = t.device_id
    WHERE t.total_active_power IS NOT NULL AND t.es_dato_confiable = 1
    ORDER BY d.name, t.recorded_at
    """

    def __init__(self, cache_dir: Path | str) -> None:
        self._cache_dir = Path(cache_dir)
        self._sincronizado = False
        self._ultima_descarga: datetime | None = None
        self._duracion_descarga: float = 0.0
        self._filas_por_medidor: dict[str, int] = {}

    @staticmethod
    def _nombre_archivo(medidor: str) -> str:
        """Nombre anonimizado para un medidor.

        Usa alias si existe, sino genera slug ASCII.
        """
        if medidor in SshMedicionRepository.ALIASES_CONOCIDOS:
            return SshMedicionRepository.ALIASES_CONOCIDOS[medidor]
        sin_tildes = unicodedata.normalize("NFKD", medidor).encode("ascii", "ignore").decode()
        return re.sub(r"[^a-z0-9]+", "_", sin_tildes.lower()).strip("_") + ".csv"

    def _ejecutar_ssh(self) -> str:
        """Ejecuta SSH + MySQL query en VPS. Retorna stdout.

        Raises:
            RuntimeError: Si SSH o MySQL fallan.
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

        return resultado.stdout

    def _parsear_salida(self, salida_ssh: str) -> dict[str, list[tuple[str, float]]]:
        """Parsea stdout de MySQL. Retorna mediciones por medidor.

        Convierte W → kW, formatea timestamps ISO.
        """
        logger.info("✅ Descarga desde VPS completada. Procesando datos...")
        por_medidor: dict[str, list[tuple[str, float]]] = {}

        for linea in salida_ssh.splitlines():
            if not linea.strip():
                continue
            partes = linea.split("\t")
            if len(partes) < 3:
                logger.warning("Línea malformada (ignorada): %s", linea)
                continue

            medidor, instante, potencia_w = partes[0], partes[1], partes[2]

            # Solo exportar medidores conocidos (anonimización)
            if medidor not in self.ALIASES_CONOCIDOS:
                logger.debug("Medidor no mapeado (ignorado): %s", medidor)
                continue

            W_POR_KW = 1000.0
            instante_iso = instante.replace(" ", "T")
            potencia_kw = round(float(potencia_w) / W_POR_KW, 4)

            if medidor not in por_medidor:
                por_medidor[medidor] = []
            por_medidor[medidor].append((instante_iso, potencia_kw))

        logger.info("📊 Datos recuperados: %d medidores", len(por_medidor))
        for med, filas in por_medidor.items():
            logger.info("  - %s: %d registros", med, len(filas))
            self._filas_por_medidor[med] = len(filas)

        return por_medidor

    def _cachear_en_csv(self, por_medidor: dict[str, list[tuple[str, float]]]) -> None:
        """Escribe datos descargados en CSV locales (cache)."""
        self._cache_dir.mkdir(parents=True, exist_ok=True)

        for medidor, filas in por_medidor.items():
            archivo_local = self._nombre_archivo(medidor)
            ruta = self._cache_dir / archivo_local

            with ruta.open("w", newline="", encoding="utf-8") as f:
                escritor = csv.writer(f)
                escritor.writerow(["instante", "potencia_kw"])
                escritor.writerows(filas)

            logger.info("💾 Cacheado: %s → %s (%d registros)", medidor, ruta, len(filas))

    def sincronizar(self) -> None:
        """Descargar del VPS e itempotencia: una sola vez por proceso.

        Raises:
            RuntimeError: Si SSH/MySQL fallan.
        """
        if self._sincronizado:
            logger.info("ℹ️  Ya sincronizado con VPS (usando cache)")
            return

        logger.info("🚀 Sincronizando con VPS...")
        inicio = time.time()

        salida_ssh = self._ejecutar_ssh()
        por_medidor = self._parsear_salida(salida_ssh)
        self._cachear_en_csv(por_medidor)

        self._duracion_descarga = time.time() - inicio
        self._ultima_descarga = datetime.now()
        self._sincronizado = True

        logger.info("✅ Sincronización completada en %.1f segundos", self._duracion_descarga)

    def medidores(self) -> list[str]:
        """Retorna medidores disponibles en cache (nombres anonimizados)."""
        nombres_anonimizados = {Path(v).stem for v in self.ALIASES_CONOCIDOS.values()}
        return sorted(
            p.stem for p in self._cache_dir.glob("*.csv") if p.stem in nombres_anonimizados
        )

    def _resolver_medidor(self, medidor: str) -> str:
        """Resuelve nombre de medidor (alias o anonimizado) al nombre real.

        Args:
            medidor: Alias conocido, nombre real, o nombre anonimizado

        Returns:
            Nombre real (clave de ALIASES_CONOCIDOS)

        Raises:
            LookupError: Si no se encuentra el medidor
        """
        # Por alias conocido o nombre real
        for real, anonimizado in self.ALIASES_CONOCIDOS.items():
            if Path(anonimizado).stem == medidor or real == medidor:
                return real

        # Por slug generado
        for real in self.ALIASES_CONOCIDOS.keys():
            if self._nombre_archivo(real).startswith(medidor):
                return real

        disponibles = ", ".join(Path(v).stem for v in self.ALIASES_CONOCIDOS.values())
        logger.error("Medidor desconocido: %s (disponibles: %s)", medidor, disponibles)
        raise LookupError(f"Medidor desconocido: {medidor}")

    def listar(self, medidor: str, desde: datetime, hasta: datetime) -> list[Medicion]:
        """Recupera mediciones en rango temporal.

        Sincroniza con VPS si es necesario (red de seguridad).

        Args:
            medidor: Nombre anonimizado (ej: "planta_2_a")
            desde: Fecha inicio (inclusiva)
            hasta: Fecha fin (exclusiva)

        Returns:
            Lista de Medicion filtradas

        Raises:
            LookupError: Si medidor no existe
            RuntimeError: Si sincronización SSH falla
        """
        # Red de seguridad: si no está sincronizado, hacerlo ahora
        if not self._sincronizado:
            self.sincronizar()

        # Resolver el nombre real del medidor
        medidor_real = self._resolver_medidor(medidor)

        ruta = self._cache_dir / self._nombre_archivo(medidor_real)
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

    def ultima_descarga_info(self) -> dict:
        """Retorna metadatos de la última descarga (para métricas)."""
        return {
            "instante": self._ultima_descarga.isoformat() if self._ultima_descarga else None,
            "duracion_segundos": self._duracion_descarga,
            "filas_por_medidor": self._filas_por_medidor,
        }
