# Decisión de Arquitectura: Descubrimiento de Máquinas Inferidas (Fase 2)

**Fecha:** 2026-10-04  
**Estado:** Aceptada  
**Impacto:** Backend API v1 + Frontend  

---

## Contexto

Energy-ML Live necesita exponer las máquinas/cargas detectadas por el NILM a través de una API REST, con UI para visualizar, detallar y dar feedback sobre las inferencias.

## Decisión

### D1: Endpoint RESTful + Cache en Memoria (MVP)

**Opción elegida:** `GET /api/v1/dispositivos/{id}/maquinas/inferidas`

**Por qué:**
- ✅ Sigue convención REST (recurso = dispositivo, sub-recurso = máquinas inferidas)
- ✅ Compatible con rutas pedagógicas existentes (Clean Architecture)
- ✅ Cache LRU en memoria es suficiente para MVP
- ✅ Escalable a DB en Fase 3 sin cambiar API

**Rechazadas:**
- ❌ GraphQL — Overhead para MVP; Clean Arch es más simple
- ❌ WebSocket — No hay pushing de cambios en tiempo real
- ❌ PostgreSQL inmediato — Cache LRU + cron son MVP válidos

### D2: Scoring de Confianza (Inline en UseCase)

**Reglas:**
- Alta: `dispersion_kw < 2.0 AND ciclos >= 10 AND encendidos >= 50`
- Media: `dispersion_kw < 5.0 AND ciclos >= 5 AND encendidos >= 20`
- Baja: Resto

**Por qué:**
- ✅ Cálculo simple, determinístico, auditeable
- ✅ No requiere ML adicional
- ✅ Educativamente transparente (estudiantes entienden las reglas)
- ✅ Fácil de ajustar en Fase 2.1

### D3: Feedback en localStorage (MVP)

**Datos guardados:**
```json
{
  "feedback": {
    "carga_001": "accepted",
    "carga_002": "review_later",
    "carga_003": "rejected"
  }
}
```

**Por qué:**
- ✅ MVP: sin backend POST endpoint
- ✅ Datos no se pierden en SPA
- ✅ Privacidad: feedback local, no se envía al server
- ✅ Fase 3 → POST endpoint + auditoría en DB

### D4: DTOs Separadas para Máquinas Inferidas

**Por qué:**
- ✅ Separación de responsabilidades: `Carga` (dominio) ≠ `MaquinaInferida` (API)
- ✅ DTO de API puede evolucionar sin tocar dominio
- ✅ Facilita testing: mocking DTOs es independiente

### D5: Clean Architecture - Rutas Pedagógicas

**Mapeo clase → código (para ISFT N° 199):**

| Lección | Concepto | Nueva ruta |
|---------|----------|-----------|
| Cap 4.3 | "API Gateway + Feedback" | `GET /api/v1/dispositivos/{id}/maquinas/inferidas` |
| Cap 6.1 | "UX + Decisión diseño" | Modal + Confianza badges |

**Documentación:** Actualizar `docs/conexion-curso-isftn199.md` en Fase 2.1

---

## Consecuencias

### ✅ Positivas

1. **API versionada:** v1 congelada + MIT for v2
2. **Pedagogía clara:** Estudiantes ven cómo API expone dominio
3. **MVP rápido:** Cache + localStorage = <1 semana
4. **Escalabilidad:** fácil migrar a DB sin romper API

### ⚠️ Trade-offs

1. **Escalabilidad limitada:** LRU cache en memoria (1 máquina)
   - Mitigation: Fase 3 → PostgreSQL
2. **Sin auditoría:** Feedback local, no grabado
   - Mitigation: localStorage + future POST endpoint
3. **Sincronización manual:** Cron fijo 3:30 AM UTC
   - Mitigation: Suficiente para MVP educativo

---

## Alternativas Rechazadas

### ❌ A1: Incluir scoring en Fase 1

**Por qué NO:**
- Ya Fase 1 está completa y estable
- Scoring es nueva lógica de negocio → Fase 2 es lugar correcto

### ❌ A2: GraphQL desde el inicio

**Por qué NO:**
- Clean Architecture es simpler para MVP educativo
- REST es lo que estudiantes aprenden en Cap 4

### ❌ A3: Feedback síncrono (POST /feedback)

**Por qué NO:**
- Requiere backend + DB antes de Fase 2.1
- localStorage es suficiente para recopilar datos

---

## Validación

### Tests Críticos

- [x] DTOs validan confianza ∈ {alta, media, baja}
- [x] UseCase calcula scoring correcto
- [x] Endpoint retorna JSON schema correcto
- [x] Cache persiste entre requests
- [x] Frontend guarda feedback en localStorage

### Gauntlet de Arquitectura

- Clean Architecture: Domain sin infraestructura ✓
- Puertos: RepositorioCacheMaquinas es abstracción ✓
- Adaptadores: LRU cache implementa puerto ✓
- Tests: ≥15 casos, cobertura ≥85% ✓

---

## Próximos Pasos (Fase 2.1+)

1. **Auditoría de feedback** — Endpoint POST + tabla `feedback_maquinas`
2. **Escalabilidad** — PostgreSQL reemplaza LRU cache
3. **Predicción humana** — Entrenar modelo si aceptaciones > rechazos
4. **Integración con SCADA** — Validar scoring contra sensores físicos

---

## Referencias

- Spec: `specs/descubrimiento-firmas-energy-ml.md`
- ADR template: https://adr.github.io/
- Fase 1: Commit 61e1213
