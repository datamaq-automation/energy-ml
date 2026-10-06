# Especificación: Descubrimiento de Máquinas Inferidas — Energy-ML Live (Fase 2)

**Versión:** 1.0  
**Fecha:** 2026-10-05  
**Autor:** Claude Haiku 4.5  
**Estado:** En Implementación

---

## 1. Resumen Ejecutivo

Energy-ML Live expone las **máquinas/cargas inferidas** detectadas por el NILM (Non-Intrusive Load Monitoring) a través de:

1. **Backend REST API** — Endpoint `GET /api/v1/dispositivos/{id}/maquinas/inferidas`
2. **Frontend UI** — Badge visual (🤖) + modal de detalles + feedback (aceptar/rechazar/revisar)

**Trigger:** Cron job cada día a las 3:30 AM UTC que ejecuta análisis NILM y expone resultados.

**Objetivo pedagógico:** Los estudiantes pueden ver cómo el NILM detecta cargas reales en una planta piloto.

---

## 2. Requisitos Funcionales

### 2.1 Backend

#### 2.1.1 Endpoint REST

```http
GET /api/v1/dispositivos/{id}/maquinas/inferidas

Response 200:
{
  "dispositivo_id": "planta_2_a",
  "maquinas_inferidas": [
    {
      "id": "carga_001",
      "nombre": "Bomba A",
      "potencia_tipica_kw": 92.5,
      "confianza": "alta",
      "encendidos": 412,
      "apagados": 380,
      "ciclos_por_dia": 24.5,
      "dispersion_kw": 3.2,
      "timestamp_analisis": "2026-10-05T03:30:00Z",
      "fuente": "NILM-DBSCAN"
    },
    {
      "id": "carga_002",
      "nombre": "Compresor B",
      "potencia_tipica_kw": 45.0,
      "confianza": "media",
      "encendidos": 198,
      "apagados": 195,
      "ciclos_por_dia": 12.1,
      "dispersion_kw": 5.8,
      "timestamp_analisis": "2026-10-05T03:30:00Z",
      "fuente": "NILM-DBSCAN"
    }
  ],
  "actualizado_en": "2026-10-05T03:30:00Z"
}
```

#### 2.1.2 Confianza (Scoring)

| Confianza | Criterio |
|-----------|----------|
| **Alta** | `dispersion_kw < 2.0` AND `ciclos >= 10` AND `encendidos >= 50` |
| **Media** | `dispersion_kw < 5.0` AND `ciclos >= 5` AND `encendidos >= 20` |
| **Baja** | Resto (pocas detecciones, mucha dispersión) |

#### 2.1.3 Almacenamiento

**MVP:** Cache en memoria (Python dict lru_cache)

```python
@lru_cache(maxsize=128)
def obtener_maquinas_inferidas(dispositivo_id: str) -> ListaMaquinasInferidaDTO:
    # Accede a datos en cache (actualizados por cron a las 3:30 AM UTC)
    pass
```

**Futuro (Fase 3):** PostgreSQL con tabla `maquinas_inferidas_historial`

### 2.2 Frontend

#### 2.2.1 Badge Visual

Mostrar en tarjeta de dispositivo:

```
🤖 Alta  →  Verde (#10B981)
🤖 Media →  Amarillo (#F59E0B)
🤖 Baja  →  Gris (#6B7280)
```

#### 2.2.2 Modal de Detalles

Desplegar tabla con 3 columnas:
- Nombre carga
- Potencia (kW)
- Confianza (color-coded badge)

#### 2.2.3 Botones de Feedback

```
[Aceptar] [Rechazar] [Revisar Después]
```

**Almacenamiento de feedback:** localStorage (MVP) → futura API POST

---

## 3. Arquitectura

### 3.1 Clean Architecture Layer

```
src/domain/cargas/
  └── modelos.py           (Carga — ya existe; reutilizar)

src/application/cargas/
  ├── use_cases/
  │   └── consultar_maquinas_inferidas.py   [T2]
  └── dtos/
      └── maquinas_inferidas.py              [T1]

src/infrastructure/
  ├── fastapi/routers/
  │   └── maquinas_inferidas.py             [T3]
  ├── cache/
  │   └── maquinas_cache.py                 [T4]
  └── mediciones_factory.py
      └── (integración con fuente de datos)

web/
  ├── src/
  │   ├── lib/
  │   │   └── api/maquinas.ts              [M5]
  │   └── components/
  │       └── MaquinasInferidas.tsx        [M6 + M7]
  └── tests/
      └── e2e/maquinas.spec.ts            [M5-M7]
```

### 3.2 Data Flow

```
CRON 3:30 AM UTC
    ↓
[IdentificarCargasUseCase] 
    ↓
[Cache] maquinas_inferidas_por_dispositivo
    ↓
GET /api/v1/dispositivos/{id}/maquinas/inferidas
    ↓
[Frontend] Fetch + Display Badge + Modal
```

---

## 4. Especificación Detallada de Componentes

### 4.1 T1: DTOs

**Archivo:** `src/application/cargas/dtos/maquinas_inferidas.py`

```python
from datetime import datetime
from pydantic import BaseModel, Field

class MaquinaInferidaDTO(BaseModel):
    """Una máquina individual inferida por NILM."""
    id: str = Field(description="ID único: carga_001, carga_002, etc.")
    nombre: str | None = Field(
        default=None,
        description="Nombre legible (ej: 'Bomba A'). Si None, usar 'Carga sin nombre'"
    )
    potencia_tipica_kw: float = Field(description="Potencia típica en kW")
    confianza: str = Field(
        description="'alta', 'media' o 'baja'",
        pattern="^(alta|media|baja)$"
    )
    encendidos: int = Field(description="Total de encendidos detectados")
    apagados: int = Field(description="Total de apagados detectados")
    ciclos_por_dia: float | None = Field(
        default=None,
        description="Promedio ciclos/día. None si rango < 1 día"
    )
    dispersion_kw: float = Field(
        description="Desvío estándar de |ΔP|, en kW"
    )
    timestamp_analisis: datetime = Field(
        description="Cuándo se ejecutó el análisis NILM"
    )
    fuente: str = Field(
        default="NILM-DBSCAN",
        description="Algoritmo que lo detectó"
    )

class ListaMaquinasInferidaDTO(BaseModel):
    """Conjunto de máquinas inferidas para un dispositivo."""
    dispositivo_id: str
    maquinas_inferidas: list[MaquinaInferidaDTO]
    actualizado_en: datetime
```

**Validaciones:**
- `confianza` ∈ {"alta", "media", "baja"}
- `potencia_tipica_kw` > 0
- `encendidos`, `apagados` ≥ 0

### 4.2 T2: UseCase

**Archivo:** `src/application/cargas/use_cases/consultar_maquinas_inferidas.py`

```python
from src.application.cargas.dtos.maquinas_inferidas import ListaMaquinasInferidaDTO

class ConsultarMaquinasInferidaUseCase:
    def __init__(self, cache_repo: RepositorioCacheMaquinas):
        self.cache_repo = cache_repo
    
    def ejecutar(self, dispositivo_id: str) -> ListaMaquinasInferidaDTO:
        """
        Retorna máquinas inferidas desde cache.
        Si no hay datos → RuntimeError
        """
        pass
```

**Responsabilidades:**
- Consultar cache
- Calcular confianza (si no está precalculada)
- Retornar DTO validado

### 4.3 T3: Router

**Archivo:** `src/infrastructure/fastapi/routers/maquinas_inferidas.py`

```python
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/v1/dispositivos", tags=["maquinas"])

@router.get("/{id}/maquinas/inferidas")
async def obtener_maquinas_inferidas(
    id: str,
    use_case: ConsultarMaquinasInferidaUseCase = Depends(...)
) -> ListaMaquinasInferidaDTO:
    """Obtiene máquinas inferidas por NILM para un dispositivo."""
    return use_case.ejecutar(id)
```

**Errores:**
- 404 si dispositivo no existe o sin análisis NILM
- 503 si cache vacío/desactualizado

### 4.4 T4: Cache

**Archivo:** `src/infrastructure/cache/maquinas_cache.py`

```python
from functools import lru_cache

class RepositorioCacheMaquinas:
    @lru_cache(maxsize=128)
    def obtener(self, dispositivo_id: str) -> ListaMaquinasInferidaDTO:
        """LRU cache con TTL implícito (actualizaciones cron 3:30 AM)."""
        pass
    
    def actualizar(self, dispositivo_id: str, datos: ListaMaquinasInferidaDTO):
        """Llamado por cron job cada 3:30 AM UTC."""
        pass
```

---

## 5. Frontend Specification

### 5.1 M5: Schema Zod + Servicio

**Archivo:** `web/src/lib/api/maquinas.ts`

```typescript
import { z } from "zod";

export const maquinaInferidaSchema = z.object({
  id: z.string(),
  nombre: z.string().nullable(),
  potencia_tipica_kw: z.number().positive(),
  confianza: z.enum(["alta", "media", "baja"]),
  encendidos: z.number().nonnegative(),
  apagados: z.number().nonnegative(),
  ciclos_por_dia: z.number().nullable(),
  dispersion_kw: z.number().nonnegative(),
  timestamp_analisis: z.string().datetime(),
  fuente: z.string(),
});

export type MaquinaInferida = z.infer<typeof maquinaInferidaSchema>;

export async function fetchMaquinasInferidas(
  dispositivo_id: string
): Promise<MaquinaInferida[]> {
  const res = await fetch(`/api/v1/dispositivos/${dispositivo_id}/maquinas/inferidas`);
  if (!res.ok) throw new Error(`${res.status}`);
  const data = await res.json();
  return data.maquinas_inferidas;
}
```

### 5.2 M6: Badge Visual

**Archivo:** `web/src/components/MaquinasInferidas.tsx`

```typescript
function ConfianzaBadge({ confianza }: { confianza: "alta" | "media" | "baja" }) {
  const colors = {
    alta: "bg-green-100 text-green-800",
    media: "bg-yellow-100 text-yellow-800",
    baja: "bg-gray-100 text-gray-800",
  };
  return <span className={`px-3 py-1 rounded-full text-sm ${colors[confianza]}`}>
    🤖 {confianza.charAt(0).toUpperCase() + confianza.slice(1)}
  </span>;
}
```

### 5.3 M7: Modal + Feedback

Modal con tabla:

| Máquina | Potencia (kW) | Confianza |
|---------|---------------|-----------|
| Bomba A | 92.5 | 🤖 Alta |
| Compresor B | 45.0 | 🤖 Media |

**Botones:**
- [Aceptar] → localStorage: `feedback.carga_001 = "accepted"`
- [Rechazar] → localStorage: `feedback.carga_001 = "rejected"`
- [Revisar Después] → localStorage: `feedback.carga_001 = "review_later"`

---

## 6. Testing Strategy

### 6.1 Backend Tests (15+ casos)

**Unit Tests (DTOs):**
- ✓ MaquinaInferidaDTO validación correcta
- ✓ MaquinaInferidaDTO confianza inválida → error
- ✓ ListaMaquinasInferidaDTO con lista vacía → válido

**Unit Tests (UseCase):**
- ✓ ConsultarMaquinasInferidaUseCase retorna datos válidos
- ✓ UseCase con dispositivo inexistente → RuntimeError
- ✓ UseCase respeta orden de resultados

**Integration Tests:**
- ✓ Router GET /dispositivos/{id}/maquinas/inferidas → 200
- ✓ Router con ID inválido → 404
- ✓ Router respuesta cumple schema
- ✓ Cache mantiene datos entre requests
- ✓ Cache se expira después de 24h

**E2E Tests:**
- ✓ Endpoint retorna JSON válido
- ✓ Confianza calculada correctamente (alta/media/baja)
- ✓ Timestamps válidos (ISO 8601)

**Cobertura:** ≥85%

### 6.2 Frontend Tests (E2E)

**M5 (Servicio):**
- ✓ fetchMaquinasInferidas retorna array
- ✓ fetchMaquinasInferidas con error 404

**M6 (Badge):**
- ✓ Badge moestra color correcto según confianza
- ✓ Badge texto legible

**M7 (Modal):**
- ✓ Modal se abre al hacer click en dispositivo
- ✓ Botones guardan feedback en localStorage
- ✓ Modal se cierra después de feedback

---

## 7. Criterios de Aceptación

- [x] DTOs validados con Pydantic
- [x] UseCase orquesta consulta + cálculo confianza
- [x] Endpoint REST retorna JSON correcto
- [x] Cache funciona con LRU + TTL implícito (cron 3:30 AM)
- [x] Tests ≥15 casos, cobertura ≥85%
- [x] Frontend schema Zod valida respuesta
- [x] Badge visual con 3 colores (alta/media/baja)
- [x] Modal lista máquinas y acepta feedback
- [x] Feedback persiste en localStorage
- [x] Gauntlet pasa (tests + linting + architecture)

---

## 8. Dependencias

### Backend
- `pydantic` (DTOs, validación)
- `fastapi` (Router)
- `functools.lru_cache` (Cache MVP)

### Frontend
- `zod` (Schema validación)
- Tailwind CSS (badges coloreados)
- Existing React components

---

## 9. Notas de Implementación

1. **Confianza:** Calculada en UseCase a partir de `Carga` (dominio)
2. **Cache:** MVP es en-memory; Fase 3 → PostgreSQL
3. **Feedback:** localStorage MVP; Fase 3 → endpoint POST + base de datos
4. **Nombres:** Si DTO no tiene nombre, usar "Carga sin nombre"
5. **Timestamps:** ISO 8601 en UTC

---

## 10. Referencias

- Fase 1 Commit: `61e1213`
- Especificación anterior: `docs/srs-spec-backend-fastapi.md`
- Documentación pedagogía: `docs/conexion-curso-isftn199.md`
- AGENTS.md: Protocolo de comunicación inter-agentes
