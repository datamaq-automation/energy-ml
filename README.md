# energy-ml (antes DiabetesAI-ML)

Identificador de cargas energéticas por **NILM** (*Non-Intrusive Load Monitoring*): a partir del consumo total de un transformador, detecta qué equipos se encienden y se apagan, sin medidores por equipo.

Este repositorio empezó como un clasificador de diabetes (Flask + SVC + Supabase). Se fue **transformando de a poco, con commits atómicos**, para que se pueda seguir la evolución en el historial.

## Cómo funciona

1. **Datos:** potencia activa total cada 5 min de la base `datamaq_telemetry` (MySQL). Se guarda en W y el adaptador la convierte a kW.
2. **Eventos:** cada salto |ΔP| ≥ `NILM_UMBRAL_KW` entre muestras consecutivas es un encendido (↑) o un apagado (↓).
3. **Cargas:** DBSCAN agrupa los eventos por magnitud. Cada grupo es una carga candidata con su potencia típica.

En la planta piloto (UPP, 11-09 a 03-10-2026), con los valores por defecto aparece una carga ON/OFF de **~92 kW** en *Trafo arriba* (412 encendidos y 380 apagados) y otra de **~88 kW** en *Trafo abajo*. El análisis completo está en el informe NILM.

## Arquitectura

Sigue la plantilla [`datamaq-automation/spec`](https://github.com/datamaq-automation/spec): FastAPI + Clean Architecture. La especificación está en [`docs/srs-spec-backend-fastapi.md`](docs/srs-spec-backend-fastapi.md).

```
src/domain/cargas/            Medicion, EventoCarga, Carga · detectar_eventos, resumir_cargas · puertos
src/application/cargas/       IdentificarCargasUseCase + DTOs
src/infrastructure/sqlalchemy SqlMedicionRepository (MySQL)
src/infrastructure/sklearn    DbscanAgrupador
src/infrastructure/fastapi    GET /api/v1/identify-loads
web/energia.html              Vista servida en /
scripts/explore_nilm.py       Ejecución por consola
```

## Uso

```bash
cp .env.example .env              # completar DATABASE_URL
ssh -L 3306:127.0.0.1:3306 vps    # túnel a la base (en otra terminal)
./run.sh dev                      # http://localhost:8000  ·  docs en /api/v1/docs
./run.sh test                     # pytest + Guantelete de Restricciones
.venv/bin/python scripts/explore_nilm.py "Trafo arriba" 2026-09-11 2026-10-03
```

## Evolución (para seguir commit a commit)

| Commit | Qué cambia | Concepto |
| :--- | :--- | :--- |
| `chore: quitar endpoint OCR` | Se borra código ajeno al dominio | Alcance / YAGNI |
| `chore(spec): scaffolding` | Estructura Clean Architecture + validadores | Convivencia de código viejo y nuevo |
| `docs(srs)` | Especificación del nuevo sistema | Spec-Driven Development |
| `feat(domain)` | Entidades y reglas puras, con tests | Dominio sin dependencias |
| `feat(infra): repositorio SQL` | Lectura de MySQL y conversión W→kW | Puertos y adaptadores |
| `feat(application)` | Caso de uso `IdentificarCargas` | Orquestación y DTOs |
| `feat(infra): DBSCAN` | Clustering detrás de un puerto | ML como detalle de infraestructura |
| `feat(api)` | Endpoint REST | Thin controllers, inyección de dependencias |
| `feat(scripts)` / `feat(web)` | Consola y vista web | Varios mecanismos de entrega |
| `refactor: eliminar diabetes` | Se borra el sistema viejo | Strangler fig: reemplazo gradual |

Para ver el código en un punto del historial: `git log --oneline` y `git checkout <hash>`.

**Ejercicio sugerido:** bajar `NILM_UMBRAL_KW` a 20 y ver cómo DBSCAN une todo en un solo grupo. ¿Por qué pasa? ¿Qué feature agregarías (corriente por fase, FP, hora) para separar las cargas?
