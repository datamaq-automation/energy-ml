# SIBO Balance — módulo de ML nutricional

Herramienta de apoyo para personas con SIBO (sobrecrecimiento bacteriano en el intestino
delgado). Permite registrar comidas día a día, estimar una curva de gases y recibir
recomendaciones de alimentos desinflamatorios.

> **Aviso clínico:** es una herramienta educativa y de apoyo. No reemplaza la evaluación,
> el diagnóstico ni el tratamiento de un profesional de la salud.

## Qué incluye

- **Base nutricional semilla** (`data/alimentos.csv`): 57 alimentos con macros, fibra,
  categoría FODMAP y scores de potencial inflamatorio/desinflamatorio. Es un punto de
  partida editable, no una tabla clínica validada.
- **Registro diario** de comidas (alimento, porción, fecha/hora, síntomas y notas) en SQLite.
- **Modelo híbrido explicable**: `RandomForestRegressor` entrenado con datos simulados
  + heurística nutricional transparente. Devuelve el pico estimado de gases (0-100).
- **Curva de gases** por día, semana o mes, con banda de incertidumbre.
- **Recomendaciones** de alimentos desinflamatorios según FODMAP, scores y consumo reciente.
- **Frontend** vanilla HTML/CSS/JS con paleta verde/azul institucional.

## Arquitectura

```
sibo/
├── domain/                  Entidades, puertos y reglas puras
├── application/             DTOs y casos de uso
├── infrastructure/
│   ├── sqlite/              Persistencia local + semilla
│   ├── ml/                  Modelo híbrido (sklearn)
│   └── fastapi/             API REST y composición
├── data/alimentos.csv       Dataset semilla
└── web/                     Interfaz de usuario
```

El módulo es autocontenido y no modifica el código NILM existente en `src/`.

## Cómo ejecutarlo

Desde la raíz del repositorio:

```bash
./run.sh install          # crea/actualiza .venv
./sibo/run.sh             # http://localhost:8001
```

También se puede levantar directamente:

```bash
.venv/bin/uvicorn sibo.main:app --reload --port 8001
```

La base SQLite se crea en `sibo/data/sibo.db` (ignorada por git).

## API

Prefijo: `/api/sibo`

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/salud` | Estado del módulo |
| GET | `/alimentos?busqueda=` | Lista/busca alimentos |
| POST | `/registros` | Registra una comida |
| GET | `/registros?desde=&hasta=` | Lista registros |
| DELETE | `/registros/{id}` | Elimina un registro |
| GET | `/gases?rango=dia\|semana\|mes&fecha=` | Curva estimada de gases |
| GET | `/recomendaciones?limite=` | Alimentos desinflamatorios sugeridos |

Documentación interactiva: `http://localhost:8001/docs`.

## Modelo

1. Se generan 1.500 comidas simuladas combinando FODMAP, fibra, carbohidratos, scores,
   porción, hora y síntomas.
2. La etiqueta simulada sigue la misma fórmula de la heurística nutricional, con ruido.
3. El `RandomForest` aprende interacciones no lineales.
4. La predicción final combina 70% modelo + 30% heurística para mantener explicabilidad.
5. Sobre cada comida se aplica una curva de absorción con pico a las 2 h y ventana de 8 h
   para construir la serie temporal.

## Pruebas

```bash
.venv/bin/pytest tests/sibo -v
.venv/bin/ruff check sibo tests/sibo
```
