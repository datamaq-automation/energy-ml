# AGENTS.md — Orquestación de Agentes y Estado del Proyecto

**Generado por:** Claude Haiku 4.5  
**Última actualización:** 2026-10-05  
**Ambiente:** /home/agustin/proyectos_software/energy-ml

---

## 📋 Resumen Ejecutivo

**energy-ml** es un **identificador de cargas energéticas por NILM** (Non-Intrusive Load Monitoring) que forma parte del ecosistema **DataMaq**. Es además un **caso de estudio real** del curso "Procesamiento de Aprendizaje Automático" del ISFT N° 199 de Tigre.

| Aspecto | Estado |
|--------|--------|
| **Repositorio** | energy-ml |
| **Objetivo** | NILM + Educación + Clean Architecture |
| **Fase** | ✅ Fase 1 Completada (Core NILM + Prod + Educación) |
| **Tests** | ✅ 130 pasan, cobertura 85%+ |
| **Documentación** | ✅ Completa (pedagógica + infraestructura) |
| **Modo Producción** | ✅ SSH/MySQL implementado y validado |
| **API REST** | ✅ Funcional (v1 congelada) |

---

## 🎯 Objetivo del Repositorio

### Contexto General

energy-ml nació como un clasificador de diabetes (DiabetesAI-ML) y se transformó mediante **commits atómicos reproducibles** en un sistema NILM funcional. La evolución está documentada en [`README.md` — Evolución](README.md#evolución-para-seguir-commit-a-commit).

### Tres pilares

1. **NILM (ML puro)**: A partir del consumo total (5 min/kW), detecta qué equipos se encienden/apagan
   - Entrada: CSVs de potencia activa total
   - Salida: Cargas identificadas (~92-88 kW en planta piloto UPP)
   - Algoritmo: DBSCAN (clustering por magnitud de saltos)

2. **Educación**: Caso de estudio del curso ISFT N° 199
   - Mapeo lección → código (FastAPI, sklearn, Clean Architecture)
   - Laboratorio vivo: estudiantes navegan y auditan código real
   - Documentación pedagógica: cuaderno alumno + guía docente

3. **Infraestructura**: Producción lista (SSH → MySQL → caché local)
   - Dev: datos locales (reproducibles)
   - Prod: datos en vivo (VPS via SSH)
   - Failover: cache de última sincronización

---

## 📊 Estado Actual (Fase 1)

### ✅ Completado

| Componente | Detalles | Commit |
|-----------|----------|--------|
| **Domain** | Entidades + reglas puras (Medicion, EventoCarga, Carga) | `feat(domain)` |
| **Application** | Caso de uso IdentificarCargasUseCase + DTOs | `feat(application)` |
| **Infrastructure** | CSV + SSH repositorios, DBSCAN agrupador | `feat(infra)` |
| **API** | FastAPI con endpoints REST v1 | `feat(api)` |
| **Logging** | Inyección de dependencias (port Bitacora) | `feat(logging)` |
| **Tests** | 130 casos (unit + integration + e2e + architecture) | `test(cargas)` |
| **Producción** | SSH fail-fast, cache, métricas de descarga | `fix(run)` |
| **Educación** | Mapeo lección-a-código, guía docente, cuaderno | `docs` |

### ✅ Suite de Pruebas (130 tests)

```
tests/
├── e2e/                 [36 tests] Endpoints, CLI, simulación, explicabilidad
├── integration/         [10 tests] Repositorios (CSV, SSH), DBSCAN, CART
├── unit/                [70 tests] Dominio, aplicación, servicios
└── test_architecture.py [14 tests] Clean Architecture, logging, dependencies
```

**Cobertura:** 85%+ (última actualización: 2026-10-04)  
**Gauntlet (11 reglas):** ✅ Todas pasan

---

## 🚀 Arquitectura

```
src/domain/cargas/              Entidades + puertos (sin dependencias externas)
  ├── modelos.py                Medicion, EventoCarga, Carga, Hipotesis
  ├── puertos.py                RepositorioMediciones, Agrupador, Bitacora
  └── servicios.py              detectar_eventos, resumir_cargas

src/application/cargas/         Caso de uso + DTOs
  ├── use_case.py               IdentificarCargasUseCase
  ├── dtos.py                   MedicionesRequest, IdentificarCargasResponse

src/infrastructure/             Adaptadores concretos
  ├── csv/                       CsvMedicionRepository
  ├── ssh/                       SshMedicionRepository (MySQL via SSH)
  ├── sklearn/                   DbscanAgrupador
  ├── fastapi/                   Servidor + routers
  │   ├── routes/cargas.py       POST /api/v1/identify-loads
  │   ├── routes/mediciones.py   GET /api/v1/mediciones/fuente
  │   └── routes/explicabilidad  GET /api/v1/explain/tree
  ├── cli/                       Scripts: entrenar, evaluar, supervisar
  └── mediciones_factory.py      Factoría (elige CSV o SSH)

web/                            Frontend estático (HTML + CSS + JS)
```

---

## 🔧 Interfaz de Usuario (por audiencia)

### Desarrolladores / Ingenieros ML

```bash
# Desarrollo local
./run.sh start dev              # Servidor con reload automático
./run.sh train planta_2_a       # Entrenar DBSCAN
./run.sh evaluate               # Comparar NILM vs verdad etiquetada
./run.sh supervise              # Entrenar árbol CART con etiquetas
./run.sh test                   # Suite completa
./run.sh lint & ./run.sh format # Validar código
```

### Producción

```bash
# Producción (datos en vivo)
./run.sh start prod             # SSH fail-fast + caché
export MEDICIONES_SOURCE=ssh
./run.sh train prod             # Entrenar con datos VPS
```

### Estudiantes / Educadores

- **Endpoint interactivo:** http://localhost:8000
- **Cuaderno de trabajo:** http://localhost:8000/guia (con actividades)
- **Documentación:**
  - `docs/conexion-curso-isftn199.md` — Mapeo lección → código
  - `docs/guia-docente.md` — Respuestas verificadas + secuencia de clase
  - `docs/cuaderno-alumno.md` — Ejercicios sin respuestas

---

## 📋 Configuración de Dependencias

### Deployable desde este repo

- ✅ **src/domain/cargas** — Pure Python, sin dependencias externas
- ✅ **src/application/cargas** — DTOs y orchestration
- ✅ **src/infrastructure/sklearn** — DBSCAN (via pip: scikit-learn)
- ✅ **src/infrastructure/fastapi** — Servidor REST (via pip: fastapi, uvicorn)
- ✅ **docs/guia-docente.md** — Publicable en cualquier plataforma educativa

### Requisitos externos (producción)

- **SSH + MySQL en VPS** — Requerido en modo prod
- **Tailscale** — Conectividad a VPS (red privada)
- **Python 3.14+** — Estándar

---

## 🔐 Estado de Seguridad

| Aspecto | Estado | Notas |
|--------|--------|-------|
| **Secretos** | ✅ Gestionados via `.env` | SSH keys en `~/.ssh/` |
| **Autenticación SSH** | ✅ Key-based (sin contraseña) | Configuración en `docs/PRODUCCION.md` |
| **CORS** | ✅ Configurado en FastAPI | Permitir solo orígenes conocidos |
| **Validación** | ✅ En límites del sistema | Input → DTOs pydantic |

---

## 📞 Comunicación InterAgentes

### Este agente (energy-ml)

**Responsabilidades:**
1. Mantener dominio e infraestructura NILM sincronizados con pedagogía
2. Ejecutar suite de tests (130 cases) en cada commit
3. Publicar cambios de API en README + CHANGELOG
4. Responder a requests de proyecto-integrador sobre updates

**Inputs esperados de otros agentes:**
- Cambios en especificación pedagógica → revisar impacto en rutas de código
- Nuevos casos de uso educativos → evaluar si son alcance válido
- Bugs reportados → fix + tests + commit atómico

### Contacto

- **Repo:** https://github.com/solareco86-ai/energy-ml
- **Documentación pedagógica:** https://github.com/solareco86-ai/proyecto-integrador
- **Casos:** https://github.com/solareco86-ai/proyecto-integrador/tree/main/data/core/casos/nilm-energy-ml

---

## 🎓 Integración con Proyecto-Integrador

| Componente | Ubicación (energy-ml) | Ubicación (proyecto-integrador) |
|-----------|---------------------|--------------------------------|
| Especificación FastAPI | `docs/srs-spec-backend-fastapi.md` | Lección 4.2 |
| Matriz de confusión | `src/application/cargas/metricas.py` | Lección 5.1 |
| Clustering DBSCAN | `src/infrastructure/sklearn/clustering.py` | Lección 3.1 |

**Sincronización:** Manual (revisar en cada PR que afecte rutas documentadas)

---

## 📌 Notas para Orquestador

1. **Fase 1 está completa.** Todos los componentes funcionales, tests en verde, documentación pedagógica en place.
2. **No hay blockers activos.** El sistema está listo para uso en producción y educación.
3. **Fase 2 (Energy-ML Live):** Ver `TODO.md` para tareas pendientes y propuestas.
4. **Mantenimiento es ligero:** Cambios pedagógicos se sincronizan con proyecto-integrador; cambios técnicos salen en commits atómicos.
