# SRS-SPECS: EnergyAI-NILM (Identificador de Cargas Energéticas) — Single Source of Truth (SSOT) & Especificación del Sistema

> **Documento:** `srs-spec-backend-fastapi.md`  
> **Versión:** `0.1.0`  
> **Estado:** `borrador`  
> **Fecha:** `2026-10-02`  
> **Autor(es):** `agustin (docente) + alumnos`  
> **Repositorio / Módulo:** `datamaq-automation/energy-ml` (antes DiabetesAI-ML)  

> 💡 **Acompañamiento Pedagógico:** Antes de completar esta plantilla, se recomienda consultar la [Guía de Andamiaje Pedagógico y Metacognición](../docs/guia-andamiaje-proyectos.md) para reflexionar sobre los problemas de negocio, casos de borde y evitar la sobreingeniería.

---

## 1. Contexto Estratégico & Propuesta de Valor

### 1.1. Foco Estratégico & Alcance
* **Mercado Objetivo:** Plantas industriales PyME con medidores de energía trifásicos ya instalados (caso piloto: planta UPP).
* **Buyer Persona (Decisor / Cliente Ideal):** Gerente de planta / responsable de mantenimiento que busca reducir el costo energético.
* **User Persona (Operador / Usuario Final):** Técnico de mantenimiento que consulta qué equipos estuvieron encendidos y cuándo.
* **Alcance Geográfico & Modalidad:** Servicio en VPS propio que lee la base `datamaq_telemetry` (MySQL 8).
* **Fuera de Alcance (*Out of Scope*):** Control de equipos, facturación, autenticación de usuarios, deep learning, tiempo real sub-minuto.

### 1.2. Pilares de Valor de la Solución
| Pilar | Enfoque | Implementación en este Sistema |
| :--- | :--- | :--- |
| **1. Activos & Entorno Operativo** | Infraestructura física, dispositivos, hardware o fuentes de datos base. | Medidores 'Trafo arriba' y 'Trafo abajo': potencia cada 5 min (`telemetry_instantaneous`, en W) y contadores kWh cada ~42 s (`telemetry_energy`) |
| **2. Software & Lógica de Negocio** | Captura, procesamiento en tiempo real, persistencia y APIs. | Lectura de series → detección de eventos ΔP → agrupamiento (DBSCAN) en cargas → API REST `/identify-loads` |
| **3. Impacto Económico & ROI** | Optimización de costos, generación de ingresos o eficiencia operativa. | Atribuir consumo por equipo (ej. carga ON/OFF de ~90 kW, ≈19 ciclos/día) para detectar usos ociosos |

### 1.3. Coordinación Operativa, Roles & Seguridad
* **Liderazgo Técnico / Responsable:** agustin.
* **Ventanas Operativas & Disponibilidad:** Análisis histórico batch; sin SLA de producción (proyecto educativo).
* **Habilitaciones, Normativas & Seguridad:** Acceso de solo lectura a la BD de telemetría; credenciales solo en `.env`.

---

## 2. Modelo de Negocio Canvas (BMC de 9 Bloques) & Gobernanza

### 2.1. Matriz del Business Model Canvas
| Bloque Canvas | Definición Estratégica | Componentes Clave en el Software |
| :--- | :--- | :--- |
| **1. Socios Clave (KP)** | Proveedor de medidores y VPS | Lectura de `datamaq_telemetry` |
| **2. Actividades Clave (KA)** | Desagregación de consumo (NILM) | Casos de uso `DetectarEventos`, `IdentificarCargas` |
| **3. Recursos Clave (KR)** | Series históricas de telemetría | Repositorio MySQL de mediciones |
| **4. Propuesta de Valor (VP)** | Saber qué equipo consume sin instalar medidores por equipo | `GET /api/v1/identify-loads` |
| **5. Relación con Clientes (CR)** | Informes y validación con personal de planta | Etiquetado manual de cargas (posterior) |
| **6. Canales de Distribución (CH)** | API REST + vista web | Routers FastAPI |
| **7. Segmentos de Clientes (CS)** | Plantas con medición trifásica | Un medidor = una serie |
| **8. Estructura de Costos (CS)** | VPS existente | Consultas agregadas, sin GPU |
| **9. Fuentes de Ingresos (RS)** | Fuera de alcance (proyecto educativo) | — |

### 2.2. Organigrama Operativo / Gobernanza de Agentes IA (Opcional)
* **`agente-orquestador` / `agente-lead`:** Gobernanza general, alineación técnica y resolución de conflictos entre módulos.
* **`agente-core-dominio`:** Supervisión de la lógica de negocio pura, entidades y reglas de dominio.
* **`agente-integraciones-api`:** Gestión de endpoints, controladores, validación de schemas y contratos externos.
* **`agente-persistencia-datos`:** Modelado de datos, migraciones, optimización de queries y repositorios.
* **`agente-qa-calidad`:** Validación continua del Guantelete de Restricciones (`test_architecture.py`), Pyright y tests.

### 2.3. Escalera de Valor / Modelo de Conversión
* **Nivel de Entrada (*Lead Magnet* / Tier Gratuito):** Informe NILM estático de una planta.
* **Servicio Core (*Core Offering*):** API de identificación de cargas sobre la telemetría existente.
* **Nivel Avanzado (*Enterprise* / Retención):** Etiquetado asistido de cargas y alertas por consumo anómalo.

---

## 3. Especificación de Requisitos de Software (SRS)

### 3.1. Requisitos Funcionales (FR)
* **FR-01 - Ingesta y Validación de Datos:** El sistema debe leer series de potencia y energía de `datamaq_telemetry` por medidor y rango de fechas, validando estrictamente los schemas mediante Pydantic v2.
* **FR-02 - Persistencia Transaccional:** El sistema debe almacenar las transacciones en MySQL 8 (lectura; resultados en tabla propia en etapa posterior) mediante el patrón Repository tipado.
* **FR-03 - Emisión de Eventos y Notificaciones:** El sistema debe emitir alertas/eventos asíncronos vía (etapa posterior) webhook cuando una carga identificada supere su consumo típico.
* **FR-04 - Control de Acceso y Autorización:** El sistema debe restringir el acceso a los recursos mediante API key (etapa posterior); en la etapa didáctica la API es local.
* **FR-05 - Seguridad y Anti-Abuso:** El sistema debe implementar rate limiting, sanitización estricta de entradas y mitigación de vulnerabilidades OWASP (SQLi, XSS, SSRF).
* **FR-06 - Detección de Eventos:** El sistema debe detectar cambios de estado como saltos |ΔP| entre muestras consecutivas mayores a un umbral configurable (por defecto 60 kW).
* **FR-07 - Identificación de Cargas:** El sistema debe agrupar los eventos por magnitud (DBSCAN, `eps` y `min_samples` configurables) y devolver cada grupo como carga candidata con potencia típica y cantidad de encendidos/apagados.
* **FR-08 - Validación de Unidades:** El sistema debe convertir la potencia de W a kW en el adaptador de datos; el dominio trabaja siempre en kW.

### 3.2. Requisitos No Funcionales (NFR)
* **NFR-01 - Latencia y Rendimiento:** La latencia p95 en lecturas debe ser inferior a 2000 ms bajo condiciones normales de operación.
* **NFR-02 - Concurrencia & Throughput:** Capacidad para procesar 5 solicitudes por segundo concurrentes sin degradación.
* **NFR-03 - Disponibilidad & Resiliencia:** SLA objetivo del 95% con reconexión automática y degradación elegante ante caídas de dependencias externas.
* **NFR-04 - Seguridad y Cifrado:** Cifrado en tránsito (TLS 1.3) y en reposo para datos sensibles; gestión de secretos aislada vía variables de entorno (`.env` protegido por `.gitignore`).
* **NFR-05 - Conformidad Arquitectónica:** 100% de cumplimiento en pruebas automáticas del Guantelete AST (`tests/test_architecture.py`) en cada commit o PR.

---

## 4. Stack Tecnológico, Arquitectura Limpia & Convenciones (CONVENTIONS)

### 4.1. Stack Tecnológico Base
* **Lenguaje:** Python 3.10+ (Tipado estricto con `typing`, `Annotated`, `dataclasses`).
* **Arquitectura:** Clean Architecture Canónica (4 Círculos de Uncle Bob) + Screaming DDD.
* **Framework Web:** FastAPI (asíncrono, OpenAPI autodocumentado).
* **Validación & Schemas:** Pydantic v2 (`BaseModel`, `Field`, `ConfigDict`).
* **Configuración Centralizada:** `pydantic-settings` (`BaseSettings`, `SettingsConfigDict`).
* **ORM & Persistencia:** SQLAlchemy 2.0 Core + PyMySQL (consultas parametrizadas, solo lectura).
* **Broker & Mensajería (Opcional):** no aplica en esta etapa.
* **Testing:** Pytest (`pytest-asyncio`, `httpx`).
* **Linters & Tipado:** Ruff y Pyright (modo estricto).
* **ML:** scikit-learn (DBSCAN) — solo en `infrastructure`; el dominio no depende de librerías externas.
* **Bounded context:** `cargas` (`src/domain/cargas`, `src/application/cargas`, ...).

### 4.2. Estructura Canónica de Directorios (Screaming DDD + Clean Architecture)

```
.
├── .env                                         # Variables de entorno secretas (NUNCA en git)
├── .env.example                                 # Plantilla canónica de variables de entorno
├── .gitignore                                   # Exclusiones estándar (ignora .env, __pycache__, .venv)
│
├── src/
│   ├── domain/                                  # CÍRCULO 1: Reglas de Negocio del Negocio (DDD Puro)
│   │   └── {bounded_context_tematico}/          # Bounded Context temático (Grita el dominio)
│   │       ├── __init__.py                      # (0 bytes obligatorio)
│   │       ├── entities.py                      # Entidades de negocio con identidad ({Entidad_1}, {Entidad_2})
│   │       ├── value_objects.py                 # Value Objects inmutables ({VO_1}, {VO_2})
│   │       ├── services.py                      # Servicios de Dominio / Lógica multi-entidad ({ServicioDominio_1})
│   │       ├── repositories.py                  # Interfaces abstractas de repositorios ({Entidad_1}Repository)
│   │       ├── events.py                        # Eventos de Dominio ({EventoDominio_1})
│   │       └── exceptions.py                    # Excepciones de negocio de dominio puro
│   │
│   ├── application/                             # CÍRCULO 2: Reglas de la Aplicación (Casos de Uso / Interactors)
│   │   └── {bounded_context_tematico}/
│   │       ├── __init__.py                      # (0 bytes obligatorio)
│   │       ├── use_cases/                       # Orquestación de Casos de Uso (Verbos que gritan la acción)
│   │       │   ├── {nombre_caso_uso_1_verbo}.py # class {NombreCasoUso1}UseCase(execute)
│   │       │   └── {nombre_caso_uso_2_verbo}.py # class {NombreCasoUso2}UseCase(execute)
│   │       ├── dtos/                            # Data Transfer Objects (Pydantic BaseModel)
│   │       │   ├── {nombre_dto_request}.py      # class {NombreCasoUso1}Request
│   │       │   └── {nombre_dto_response}.py     # class {NombreCasoUso1}Response
│   │       └── mappers/                         # Traductores bidireccionales puros DTO <-> Entity
│   │           └── {nombre_mapper}.py           # class {NombreEntidad}Mapper
│   │
│   ├── adapters/                                # CÍRCULO 3: Interface Adapters (Agnósticos de Frameworks Web)
│   │   └── {bounded_context_tematico}/
│   │       ├── __init__.py                      # (0 bytes obligatorio)
│   │       ├── controllers/                     # Controladores que reciben DTOs y llaman al UseCase
│   │       │   └── {nombre_controlador}.py      # class {NombreEntidad}Controller
│   │       ├── presenters/                      # Formatean ResponseDTO o excepciones a HTTP/JSON/ViewModel
│   │       │   └── {nombre_presentador}.py      # class {NombreEntidad}Presenter
│   │       ├── gateways/                        # Adaptadores hacia servicios externos (APIs, notificaciones)
│   │       │   └── {nombre_gateway}.py          # class {NombreServicioExterno}Gateway
│   │       └── view_models/                     # (Opcional) Modelos para renderizado visual server-side
│   │
│   ├── infrastructure/                          # CÍRCULO 4: Frameworks & Drivers (Detalles Externos)
│   │   ├── fastapi/                             # Mecanismo de entrega Web
│   │   │   ├── routers/                         # Endpoints REST delgados (Thin Controllers)
│   │   │   └── dependencies.py                  # Inyección de dependencias (Depends)
│   │   ├── {orm_driver_dir}/                    # Persistencia concreta (ej. sqlalchemy)
│   │   │   ├── models/                          # DeclarativeBase y esquemas de tablas
│   │   │   └── repositories/                    # Implementaciones concretas de domain/.../repositories.py
│   │   ├── {broker_driver_dir}/                 # Daemons/suscriptores para mensajería (si aplica)
│   │   └── settings/                            # Configuración y Logging Centralizado
│   │       ├── __init__.py                      # (0 bytes obligatorio)
│   │       ├── config.py                        # Settings(BaseSettings) con pydantic-settings
│   │       └── logger.py                        # Logging estructurado JSON/texto configurado desde Settings
│   │
│   └── main.py                                  # Entrypoint ASGI (app = create_app())
│
└── tests/
    ├── __init__.py                              # (0 bytes obligatorio)
    ├── test_architecture.py                     # Validador AST del Guantelete de Restricciones
    ├── unit/                                    # Pruebas unitarias de domain y use_cases
    ├── integration/                             # Pruebas de integración con DB/broker
    └── e2e/                                     # Pruebas de endpoints FastAPI (httpx.AsyncClient)
```

### 4.3. Especificación de Configuración & Logging Centralizado

#### A. Gestión de Entorno (`.env`, `.env.example`, `.gitignore`)
* **Regla de Seguridad:** El archivo `.env` contiene credenciales sensibles y **NUNCA** se commitea a Git. El archivo [`.gitignore`](file:///home/agustin/proyectos_software/spec/.gitignore) debe excluir explícitamente `.env` y `.env.*` (excepto `!.env.example`).
* **Plantilla Canónica (`.env.example`):** Define todas las claves de configuración necesarias con valores ficticios o de desarrollo para guiar el setup local y pipelines de CI/CD.

#### B. `src/infrastructure/settings/config.py` (Pydantic Settings)
* Centraliza toda la configuración del sistema en una clase `Settings` derivada de `pydantic_settings.BaseSettings`:
  ```python
  from functools import lru_cache
  from typing import List
  from pydantic import Field
  from pydantic_settings import BaseSettings, SettingsConfigDict

  class Settings(BaseSettings):
      model_config = SettingsConfigDict(
          env_file=".env",
          env_file_encoding="utf-8",
          case_sensitive=True,
          extra="ignore",
      )

      # Entorno
      ENVIRONMENT: str = Field(default="development")
      DEBUG: bool = Field(default=False)
      LOG_LEVEL: str = Field(default="INFO")

      # API
      PROJECT_NAME: str = Field(default="{nombre_del_sistema_o_proyecto}")
      VERSION: str = Field(default="1.0.0")
      API_V1_PREFIX: str = Field(default="/api/v1")
      ALLOWED_HOSTS: List[str] = Field(default_factory=lambda: ["*"])

      # Seguridad
      SECRET_KEY: str = Field(default="insecure-secret-key-change-in-production")
      ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60)

      # Base de Datos
      DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./app.db")

  @lru_cache()
  def get_settings() -> Settings:
      return Settings()
  ```

#### C. `src/infrastructure/settings/logger.py` (Logging Estructurado)
* Centraliza la inicialización de loggers con formato estructurado (JSON en producción, formateado en desarrollo):
  ```python
  import logging
  import sys
  from src.infrastructure.settings.config import get_settings

  def setup_logging() -> logging.Logger:
      settings = get_settings()
      log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
      
      logging.basicConfig(
          level=log_level,
          format="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
          handlers=[logging.StreamHandler(sys.stdout)],
      )
      logger = logging.getLogger(settings.PROJECT_NAME)
      logger.setLevel(log_level)
      return logger

  logger = setup_logging()
  ```

---

### 4.4. Las Siete Reglas Innegociables de Arquitectura

1. **Regla de Dependencia de Capas (Validada por AST):**
   * `domain` nunca importa de capas externas (`application`, `adapters`, `infrastructure`).
   * `application` solo depende de `domain` y `pydantic`.
   * `adapters` depende de `application` y `domain` (nunca de `infrastructure` ni de FastAPI/ORM).
   * `infrastructure` aísla frameworks, bases de datos y librerías externas.
2. **Archivos `__init__.py` de 0 Bytes:**
   * El 100% de los archivos `__init__.py` en `src/` y `tests/` deben estar completamente vacíos (0 bytes) para evitar dependencias circulares y efectos secundarios al importar módulos.
3. **Desacople Absoluto de Datos (`data/`):**
   * Fuentes de verdad estáticas (JSON, Markdown, YAML) residen en `data/` desacopladas del código ejecutable.
4. **Gobernanza Antialucinación de Parámetros Críticos:**
   * Precios, constantes de ingeniería, reglas tarifarias y fórmulas clave deben provenir de `Settings` o base de datos, nunca *hardcoded* en código fuente.
5. **Controladores Delgados (*Thin Controllers*):**
   * Los routers en `infrastructure/fastapi/routers/` no contienen lógica de negocio ni importan ORMs directamente; delegan exclusivamente en `adapters/controllers/` o `application/use_cases/`.
6. **Imports Absolutos:**
   * Prohibidos los imports relativos (`from . import ...` o `from .. import ...`). Se exige siempre sintaxis absoluta `from src....`.
7. **Tipado Estricto Exhaustivo:**
   * Prohibidas colecciones o variables sin tipo explícito (e.g. `list[str]`, `dict[str, Any]`). Toda función debe especificar tipos de parámetros y retorno validados por Pyright.
8. **Cabecera de Path Relativo (Trazabilidad):**
   * Todo archivo fuente `.py` en `src/` y `tests/` debe comenzar con un docstring o comentario indicando su ruta relativa exacta respecto a la raíz del repositorio (e.g. `"""src/main.py — ..."""` o `"""tests/test_architecture.py — ..."""`). Se excluyen terminantemente los archivos `__init__.py` que deben tener exactamente 0 bytes según la Regla 2.

---

## 5. Gobernanza Normativa, Calidad & Matriz de Pruebas

### 5.1. Filosofía de Desarrollo Asistido por Agentes IA ("The Constraint Gauntlet")
> *"Mi estrategia actual es no leer el código generado por mis agentes. Lo que hago en su lugar es rodearlos de **restricciones extremas**: Unit tests, QA procedures, métricas de calidad, mutation testing, coverage... Tengo muy alta confianza en el código porque tiene que superar todo mi guantelete de restricciones."*  
> — **Robert C. Martin ("Uncle Bob")**

Bajo este paradigma, el equipo de ingeniería y los agentes de IA operan dentro de un marco de verificación estricto, automatizado y determinista donde ningún código se fusiona a producción sin superar el 100% de los invariantes formales.

### 5.2. Las 11 Baterías del Guantelete (`tests/test_architecture.py`)
1. **`test_no_hardcoded_secrets`:** Detecta y bloquea contraseñas, tokens JWT, API keys o connection strings quemadas en código fuente.
2. **`test_no_raw_sql_formatting`:** Prohíbe concatenación de strings o f-strings en `text(...)` para mitigar vectores de SQL Injection (OWASP).
3. **`test_no_os_environ_direct_access`:** Prohíbe el acceso directo a `os.environ` u `os.getenv` fuera de `src/infrastructure/settings/config.py`.
4. **`test_domain_isolation`:** Garantiza que el Core de Dominio (`src/domain`) sea 100% puro y no importe frameworks ni librerías de I/O.
5. **`test_application_and_adapters_layers`:** Valida la regla de dependencia de capas (Application desacoplada, Adapters agnósticos y Thin Controllers sin acceso a ORMs).
6. **`test_function_return_types`:** Exige que el 100% de las funciones en `src/domain` y `src/application` declaren tipo de retorno explícito (`-> Type`).
7. **`test_function_arg_types`:** Exige que todos los parámetros de funciones en `domain` y `application` declaren Type Annotations.
8. **`test_init_files_must_be_empty`:** Comprueba que todos los `__init__.py` en `src/` y `tests/` tengan exactamente 0 bytes (sin código, docstrings ni imports).
9. **`test_no_relative_imports`:** Prohíbe imports relativos en `src/` (`from . import ...` o `from .. import ...`), obligando al uso de imports absolutos (`from src...`).
10. **`test_no_unstructured_prints`:** Prohíbe llamadas a `print()` en código de producción (`src/`), exigiendo logging formal.
11. **`test_relative_path_headers`:** Exige que todo archivo `.py` en `src/` y `tests/` comience con un docstring o comentario con su ruta relativa exacta (excluyendo `__init__.py` que debe tener 0 bytes).

### 5.3. Detección Determinística de Código Muerto y Sobreingeniería (`tests/test_clean_design.py`)
Complementando el Guantelete y el detector de Componentes Dios, el archivo `tests/test_clean_design.py` analiza el AST local ($0 tokens) para evitar los sesgos de sobreingeniería y código residual típicos de agentes IA:
1. **`UNREACHABLE_FILE`:** Detecta archivos `.py` huérfanos en `src/` no alcanzables mediante el Grafo de Alcance desde `main.py` ni desde suites de tests.
2. **`GHOST_INTERFACE`:** Alerta cuando un `Protocol` o `ABC` tiene solo una implementación concreta en `src/` (y 0 mocks en `tests/`), aplicando YAGNI.
3. **`MIDDLE_MAN_METHOD`:** Identifica métodos que solo delegan argumentos de forma idéntica en otro objeto sin aportar valor ni lógica.
4. **`DEEP_INHERITANCE`:** Detecta árboles de herencia con profundidad superior a 2 niveles (`DIT > 2`), promoviendo composición.
5. **`ORPHAN_PRIVATE_SYMBOL`:** Identifica funciones, clases o métodos privados declarados pero nunca referenciados en el módulo.
6. **`SPECULATIVE_MICRO_FILE`:** Detecta archivos micro-fragmentados (< 10 LOC) que dispersan el contexto sin justificación.

Soporta ejecución humana (`python3 tests/test_clean_design.py`), modo estricto para CI (`--strict`) y salida estructurada para agentes IA (`--json`).

### 5.4. Estándares de Calidad, Trazabilidad & Commits Atómicos
* **Marco de Referencia:** Alineación con buenas prácticas de calidad de producto (ISO/IEC 25010) y seguridad de la información (ISO/IEC 27001).
* **Lineamiento de Commits Atómicos (Principio de Responsabilidad Única en Git):**
  * **Una Unidad Lógica por Commit:** Cada commit debe representar un cambio único, autocontenido, indivisible y con propósito claro. Queda estrictamente prohibido agrupar en un único commit features nuevas, refactorizaciones, corrección de bugs no relacionados y ajustes de formato cosmético.
  * **Integridad del Repositorio:** Cada commit individual debe dejar el proyecto en un estado compilable, estable y pasando el 100% de la suite de tests y linters (cero commits con código roto o a medio implementar).
  * **Aislamiento para Bisect y Revert:** La granularidad atómica asegura que cualquier regresión se aísle inmediatamente mediante `git bisect` y pueda revertirse con `git revert` limpiamente sin efectos secundarios ni destrucción de código colateral.
  * **Regla del Conector "Y" (*And Rule*):** Si la descripción del commit necesita la conjunción "y" o "además" para describir lo realizado (e.g. `feat: add user login and fix footer style`), el commit NO es atómico y debe dividirse en micro-commits independientes.
* **Convención Estricta de Mensajes ([Conventional Commits](https://www.conventionalcommits.org/)):**
  * **Estructura Obligatoria:** `<tipo>(<alcance opcional>): <descripción concisa e imperativa>`
  * **Tipos Permitidos:**
    * `feat`: Nueva funcionalidad para el usuario o sistema.
    * `fix`: Corrección de un defecto o bug.
    * `refactor`: Cambio estructural de código sin alteración de funcionalidad externa ni adición de features/fixes.
    * `test`: Creación o modificación de pruebas unitarias, de integración o de arquitectura.
    * `docs`: Cambios exclusivos en documentación, especificaciones o comentarios.
    * `chore`: Mantenimiento de configuración, dependencias o herramientas sin impacto en código de producción.
    * `perf`: Optimizaciones de rendimiento o uso eficiente de memoria/recursos.

### 5.5. Matriz de Verificación Automatizada Previa a Despliegues

Todos los cambios deben superar el 100% de la siguiente batería de comandos antes de integrarse a la rama principal o desplegarse a producción:

```bash
# 1. Linter y Verificación de Formato
ruff check .
ruff format --check .

# 2. Análisis Estático de Tipos Estricto (respeta `pyrightconfig.json`; excluye `tests/` por diseño)
pyright src/

# 3. Validación de Arquitectura y Guantelete de Restricciones (AST)
python3 tests/test_architecture.py

# 4. Auditoría de Componentes Dios (Monolitos) y Sobreingeniería (YAGNI & Dead Code)
python3 tests/test_god_components.py --strict
python3 tests/test_clean_design.py --strict

# 5. Suite Completa de Pruebas en Pytest (Unit, Integration, E2E y Gauntlet)
pytest --maxfail=1 --disable-warnings -v
```

### 5.6. Configuración del Editor (Pylance / VS Code)

Todo repositorio debe incluir dos archivos de configuración de tipos para garantizar que el LSP del editor (Pylance) y el análisis estático de CI (Pyright) emitan **exactamente los mismos diagnósticos**:

1. **`pyrightconfig.json` (raíz)** — configura Pyright/Pylance:
   ```json
   {
     "include": ["src"],
     "exclude": ["tests", "venv", "**/__pycache__", "**/node_modules"],
     "venvPath": ".",
     "venv": "venv",
     "typeCheckingMode": "standard",
     "pythonVersion": "3.10"
   }
   ```
2. **`.vscode/settings.json`** — alinea Pylance con la misma exclusión:
   ```json
   {
     "python.analysis.exclude": ["tests", "venv", "**/__pycache__"]
   }
   ```

**Motivación:** Pylance analiza archivos abiertos explícitamente aunque estén en el `exclude` de `pyrightconfig.json`. Sin `.vscode/settings.json`, los archivos de `tests/` emiten falsos positivos en el editor que no existen en CI — por ejemplo, los stubs de SQLAlchemy tipan `Model.__table__` como `FromClause`, por lo que `Model.__table__.create(engine)` se marca como error pese a ser válido en runtime.

**Reglas innegociables:**
- La exclusión de `tests/` del análisis de tipos es **deliberada** (los tests ejercitan ORMs en runtime). No debe "corregirse" con `cast(Any, ...)`, `# type: ignore` ni `# noqa`.
- El `.vscode/settings.json` **debe versionarse**: en `.gitignore` usar el patrón `.vscode/*` (ignora el contenido) seguido de `!.vscode/settings.json` (re-incluye el archivo). Nunca ignorar el directorio con `.vscode/`, ya que Git no desciende a directorios ignorados.
- `pyright` en CI debe ejecutarse como `pyright src/` (o confiar en el `exclude` de `pyrightconfig.json`); nunca sobre `tests/`.
