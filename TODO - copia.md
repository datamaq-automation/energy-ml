# TODO.md — Roadmap y Tareas Pendientes

**Generado por:** Claude Haiku 4.5  
**Última actualización:** 2026-10-05  
**Status:** Fase 1 Completada | Fase 2 en Planificación

---

## 🎯 Visión General

### Fase 1: Core NILM + Educación ✅ COMPLETADA

- ✅ NILM funcional (DBSCAN clustering)
- ✅ API REST v1 congelada
- ✅ Clean Architecture implementada
- ✅ 130 tests con 85%+ cobertura
- ✅ Documentación pedagógica completa
- ✅ Modo producción (SSH + MySQL + caché)

### Fase 2: Energy-ML Live (PROPUESTA)

**Objetivo:** Escalabilidad, monitoreo en vivo, y ampliación educativa.

---

## 📌 Tareas Pendientes — Fase 2

### Observabilidad y Monitoreo

#### 2.1 Métricas Prometheus
- [ ] Instrumentar FastAPI con prometheus-client
- [ ] Exponer `/metrics` con:
  - Requests totales y latencia por endpoint
  - Tiempo de descarga SSH
  - Cache hits/misses
  - Errores de sincronización
- **Prioridad:** Alta (producción)
- **Estimación:** 2-3 hs
- **Tests:** unit + e2e para métricas

#### 2.2 Health Checks Mejorados
- [ ] Endpoint `/health/live` (app corriendo)
- [ ] Endpoint `/health/ready` (dependencias accesibles: SSH, MySQL, caché)
- [ ] Timeout configurables por componente
- **Prioridad:** Alta
- **Estimación:** 1-2 hs

#### 2.3 Logging Estructurado
- [ ] Cambiar de `print` a JSON structured logs
- [ ] Niveles: DEBUG, INFO, WARN, ERROR
- [ ] Rotación de logs automática
- [ ] Integración con stack de observabilidad (si aplica)
- **Prioridad:** Media
- **Estimación:** 3-4 hs

### API v2 (Backwards Compatible)

#### 2.4 Streaming de Resultados
- [ ] POST `/api/v2/identify-loads/stream` — recibir CSV por chunks, retornar cargas detectadas en tiempo real
- [ ] Websockets (opcional) para push notifications
- **Prioridad:** Media
- **Estimación:** 4-5 hs
- **Nota:** Mantener v1 congelada

#### 2.5 Batch Processing
- [ ] POST `/api/v2/batch` — procesar múltiples medidores en paralelo
- [ ] Async tasks con celery/rq
- [ ] Callback webhooks cuando terminen
- **Prioridad:** Baja (no pedagógico)
- **Estimación:** 6-8 hs

### Educación Avanzada

#### 2.6 Explicabilidad Expandida
- [ ] Endpoint `/api/v1/explain/prediction` — por qué esta magnitud es carga X
- [ ] Exportar datos de entrenamiento DBSCAN (centroides, densidad)
- [ ] Visualización de decision boundary en 2D (PCA)
- **Prioridad:** Media (educativo)
- **Estimación:** 3-4 hs

#### 2.7 Laboratorio Interactivo
- [ ] Página web con formulario para tuning de DBSCAN (eps, min_samples)
- [ ] Preview de clustering en tiempo real
- [ ] Exportar parámetros óptimos
- **Prioridad:** Media
- **Estimación:** 4-6 hs

#### 2.8 Nuevos Casos de Estudio
- [ ] Agregar datasets adicionales (planta fotovoltaica, climatización)
- [ ] Expandir mapeo lección-a-código en proyecto-integrador
- **Prioridad:** Baja (scope creep)
- **Estimación:** TBD por proyecto-integrador

### Infraestructura y Deployment

#### 2.9 Containerización
- [ ] Dockerfile (multi-stage: dev + prod)
- [ ] docker-compose (app + MySQL mock)
- [ ] GitHub Actions: build + push a registry
- **Prioridad:** Alta (devops)
- **Estimación:** 3-4 hs

#### 2.10 Persistencia de Resultados
- [ ] PostgreSQL o SQLite para historial de análisis
- [ ] Tabla: medidor, timestamp_analisis, cargas_detectadas, timestamp_ultima_descarga
- [ ] Endpoint `/api/v1/historico/<medidor>` para auditar cambios
- **Prioridad:** Media
- **Estimación:** 4-5 hs

#### 2.11 Sincronización Incremental (SSH)
- [ ] En lugar de descargar todo, traer solo datos nuevos (WHERE recorded_at > última_sincronización)
- [ ] Reducir tiempo de descarga en modo prod
- **Prioridad:** Media
- **Estimación:** 2-3 hs
- **Nota:** Validar que DBSCAN no se rompe con datos incremental

### Testing Avanzado

#### 2.12 Load Testing
- [ ] Benchmarks: cuántos requests/s aguanta el endpoint identify-loads
- [ ] Profiling de memoria (descarga SSH, caching)
- **Prioridad:** Baja (no crítico aún)
- **Estimación:** 2-3 hs

#### 2.13 Smoke Tests en Producción
- [ ] Script de verificación post-deploy
- [ ] Valida: SSH accesible, MySQL accesible, última descarga < 5 min
- **Prioridad:** Alta
- **Estimación:** 1 h

---

## 🚦 Priorización (para Fase 2)

### 🔴 Crítica (P0) — Bloquea uso en producción

1. **2.1 Métricas Prometheus** — Observabilidad obligatoria
2. **2.2 Health Checks Mejorados** — Fail-fast confiable
3. **2.13 Smoke Tests** — Validar deployment

### 🟡 Alta (P1) — Mejora experiencia dev/prod

4. **2.9 Containerización** — Portabilidad, CI/CD
5. **2.10 Persistencia** — Auditoría + historia
6. **2.3 Logging Estructurado** — Debugging en prod

### 🟢 Media (P2) — Nice to have

7. **2.4 Streaming** — Escalabilidad (opcional si no hay demanda)
8. **2.6 Explicabilidad Expandida** — Educación avanzada
9. **2.7 Laboratorio Interactivo** — Engagement estudiantes
10. **2.11 Sincronización Incremental** — Performance

### ⚪ Baja (P3) — Depende de stakeholders

11. **2.5 Batch Processing** — Si hay demanda
12. **2.8 Nuevos Casos de Estudio** — Coordinación con proyecto-integrador

---

## 🎓 Roadmap Pedagógico

### Corto Plazo (Oct-Nov 2026)

- [ ] Integración con dinámica de clases ISFT N° 199
- [ ] Feedback de docentes sobre actividades
- [ ] Actualización de cuaderno alumno si cambios en API

### Mediano Plazo (Dic 2026 - Ene 2027)

- [ ] Nuevos datasets pedagógicos (si proyecto-integrador pide)
- [ ] Documentación de casos edge (clusters con baja densidad)

### Largo Plazo (2027+)

- [ ] Integración con proyectos finales de estudiantes
- [ ] Publicación de casos en GitHub/Kaggle (anonimizado)

---

## 🐛 Bugs Conocidos

Ninguno identificado. Suite de pruebas en verde. El sistema es estable en Fase 1.

---

## 📋 Checklist para Fase 2 — Planning

Antes de comenzar Fase 2, validar:

- [ ] Presupuesto / horas disponibles
- [ ] Stakeholders clarificaron qué características de P2 son prioritarias
- [ ] proyecto-integrador tiene feedback sobre pedagogía
- [ ] Infraestructura de producción (VPS, Tailscale) está validada y estable
- [ ] No hay cambios breaking en dependencias (scikit-learn, FastAPI, Python)

---

## 📞 Responsabilidades Futuras

### Energy-ML

- Mantener Clean Architecture (no business logic en infraestructura)
- Tests al 85%+ de cobertura
- Commits atómicos, especialmente si cambios afectan rutas pedagógicas
- Changelog actualizado

### Proyecto-Integrador

- Coordinar si cambios en energy-ml rompen ejemplos de clase
- Aportar feedback de estudiantes para mejoras
- Proponer nuevos casos pedagógicos

### DataMaq (Orquestador)

- Priorizar entre P0, P1, P2, P3
- Validar que new features no rompen integración con otros repos
- Gestionar deployment a producción

---

## 📊 Métricas de Éxito (Fase 1 → Fase 2)

| Métrica | Fase 1 | Fase 2 (Objetivo) |
|---------|--------|-------------------|
| Tests que pasan | 130 | 160+ |
| Cobertura | 85%+ | 90%+ |
| Latencia GET /mediciones/fuente | <100ms | <50ms |
| Tiempo descarga SSH (prod) | 2-3s | <1s (incremental) |
| Uptime (prod) | N/A | 99.5%+ |
| Estudiantes usando repo | ~30 (ISFT N° 199) | 100+ (si se expande) |

---

## 🔗 Referencias Útiles

- **Especificación datamaq:** https://github.com/datamaq-automation/spec
- **Curso ISFT N° 199:** https://isftn199.com.ar/cursos/procesamiento-aprendizaje-automatico
- **Proyecto-Integrador:** https://github.com/solareco86-ai/proyecto-integrador
- **Este repo:** https://github.com/solareco86-ai/energy-ml
