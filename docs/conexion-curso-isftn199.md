# Conexión con Curso ISFT N° 199: "Procesamiento de Aprendizaje Automático"

## Bidireccionaldad

Este proyecto está **vinculado bidireccionalmente** con el curso [Procesamiento de Aprendizaje Automático](https://isftn199.com.ar/cursos/procesamiento-aprendizaje-automatico):

- ✅ El **curso referencia a energy-ml** como caso de estudio real en 3 capítulos
- ✅ **energy-ml referencia al curso** explicando cómo cada lección se implementa en código

## Dónde mirar en energy-ml para cada lección

### Unidad 1: Fundamentos

**1.1 Terminal Bash** → `data/input/` contiene CSVs de mediciones reales
**1.2 venv** → `Makefile` con targets; `requirements.txt` aislado
**1.3 .env** → `.env.example` (rutas de datos, thresholds de detección)
**2.1 Git diff** → Historial en `git log` de entrenamientos del modelo
**4.2 FastAPI básico** → `src/infrastructure/fastapi/app.py` + `routes.py`

### Unidad 2: Machine Learning

**1.1 Pydantic** → `src/application/dtos/` contiene esquemas de validación
**1.2 FastAPI lifespan** → `src/infrastructure/fastapi/lifespan.py` carga modelo en memoria
**5.1 Matriz de confusión** → `src/application/cargas/metricas.py` calcula F1, precision, recall
**5.2 pytest + TDD** → `tests/application/cargas/test_identify_use_case.py` con cobertura >= 85%
**5.3 /metrics endpoint** → `GET /api/v1/metrics` expone dashboard de rendimiento

### Unidad 3: Programación Lógica

**3.1 Entropía, Gini** → `src/infrastructure/sklearn/clustering.py` — DBSCAN implementa decisiones de densidad
**3.2 Árboles de regresión** → `src/infrastructure/sklearn/arbol_decision.py` (en desarrollo)
**3.3 Exportación JSON** → `src/adapters/tree_presenter.py` serializa árbol para auditoría de agentes

## Flujo completo: Lectura → Detección → Clustering → Evaluación

```
1. CSV (data/input/mediciones.csv)
   ↓
2. DeteccionEventosUseCase: Cambios en potencia → lista de eventos
   ↓
3. ClusteringUseCase: DBSCAN agrupa eventos por firma
   ↓
4. EvaluacionUseCase: Matriz de confusión vs. etiquetas conocidas
   ↓
5. JSON response: {"cargas": [...], "metricas": {"f1": 0.96, ...}}
```

Cada paso corresponde a una o más lecciones del curso.

## Recursos

- **Curso oficial:** https://isftn199.com.ar/cursos/procesamiento-aprendizaje-automatico
- **Repositorio del curso:** https://github.com/solareco86-ai/proyecto-integrador (proyecto-integrador)
- **Cuaderno de alumno:** `docs/cuaderno-alumno.md` (en este repositorio)

## Objetivo pedagógico

Los estudiantes del ISFT N° 199 usan **energy-ml como laboratorio vivo** para:
- Verificar que entienden cada lección navegando el código real
- Aprender arquitectura hexagonal en un proyecto concreto
- Practicar pair programming con agentes (Aider, OpenCode, AGY CLI)
- Auditar decisiones de ML con explicabilidad JSON

---

## Tabla de navegación: Lecciones → Archivos

| Unidad | Capítulo | Lección | Concepto | Archivo | Elemento |
|--------|----------|---------|----------|---------|----------|
| U1 | 4 | 4.2 | FastAPI: servidor básico | `src/infrastructure/fastapi/routes.py` | POST /api/v1/identify-loads |
| U2 | 5 | 5.1 | Matriz de confusión, F1 | `src/application/cargas/metricas.py` | `confusion_matrix()` |
| U3 | 3 | 3.1 | Gini, decisiones de densidad | `src/infrastructure/sklearn/clustering.py` | DBSCAN |
