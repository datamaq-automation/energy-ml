# SIBO Balance — módulo de ML nutricional

Herramienta de apoyo para personas con SIBO (sobrecrecimiento bacteriano en el intestino
delgado). Permite registrar comidas, estimar una curva de gases y recibir recomendaciones
de alimentos desinflamatorios.

> **Aviso clínico:** es una herramienta educativa y de apoyo. No reemplaza la evaluación,
> el diagnóstico ni el tratamiento de un profesional de la salud.

> **Estado de los datos:** el modelo actual se entrenó con etiquetas simuladas derivadas de
> la heurística nutricional. No fue entrenado ni validado con datos reales de personas.
> La banda de la curva refleja la dispersión entre los árboles del ensamble, no un
> intervalo de confianza clínico.

## Qué incluye

- **Base nutricional semilla** (`src/infrastructure/sibo/data/alimentos.csv`): 57 alimentos
  con macros, fibra, categoría FODMAP y scores de potencial inflamatorio/desinflamatorio.
  Es un punto de partida editable, no una tabla clínica validada.
- **Registro de comidas** (alimento, porción, fecha/hora, síntomas y notas) en SQLite local.
- **Modelo híbrido explicable**: `RandomForestRegressor` entrenado con etiquetas simuladas
  + heurística nutricional transparente. Devuelve el pico estimado de gases (0-100).
- **Curva de gases** por día, semana o mes, con banda derivada de los percentiles del
  ensamble de árboles.
- **Recomendaciones** de alimentos desinflamatorios según FODMAP, scores y consumo reciente.
- **Frontend** vanilla HTML/CSS/JS con paleta verde/azul institucional.

## Arquitectura

```
src/
├── domain/sibo/                     Entidades, puertos y reglas puras
├── application/sibo/                DTOs, política del modelo y casos de uso
├── adapters/
│   ├── controllers/sibo/            Orquestación HTTP sin FastAPI
│   ├── presenters/sibo/             Esquemas de respuesta y mapeo
│   └── gateways/sibo/               Adaptadores SQLite con conexión inyectada
└── infrastructure/sibo/
    ├── database.py                  Conexión y esquema SQLite
    ├── seed.py                      Carga del dataset semilla
    ├── ml/                          Modelo híbrido (sklearn)
    ├── fastapi/                     Routers y composición de la app
    ├── data/alimentos.csv           Dataset semilla
    └── web/                         Interfaz de usuario
```

El dominio no importa FastAPI, SQLite ni scikit-learn. La conexión SQLite se crea en
infraestructura y se inyecta en los gateways por parámetro.

## Cómo ejecutarlo

Desde la raíz del repositorio:

```bash
./run.sh install          # crea/actualiza .venv
./run.sh sibo             # http://localhost:8001
```

La base SQLite se crea en `src/infrastructure/sibo/data/sibo.db` (ignorada por git).

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
   Esto hace que el modelo aprenda la forma de esa regla, no el efecto real de los
   alimentos en una persona.
3. El `RandomForest` aprende interacciones no lineales sobre esas etiquetas simuladas.
4. La predicción final combina modelo y heurística según `PoliticaModelo`
   (`src/domain/sibo/value_objects.py`). Está en el dominio porque define cómo se
   mezclan dos señales del problema, no cómo se entrena sklearn. Los valores por
   defecto son 70/30; son una decisión de diseño explícita, no un resultado
   validado con datos reales.
5. La banda se calcula con los percentiles 10 y 90 de las predicciones de los 120 árboles
   del ensamble. No se usan márgenes fijos.
6. Sobre cada comida se aplica una curva de absorción con pico a las 2 h y ventana de 8 h
   para construir la serie temporal.

### Qué falta para el seguimiento personal

El objetivo de producto es un seguimiento de 30 días con comidas compuestas, registro de
síntomas a las 2 h, detección de patrones personales (alimentos y combinaciones asociadas
a síntomas), predicción de síntomas y aprendizaje continuo. Eso requiere:

- etiqueta real de síntomas en lugar de la etiqueta simulada;
- comidas con varios alimentos (`Comida` + `ItemComida`) y entidad `Sintoma`;
- validación temporal, línea base y métricas antes de mostrar predicciones;
- consentimiento explícito, control de acceso y borrado/exportación de datos de salud;
- validación por un profesional antes de cualquier uso clínico.

## Privacidad

El prototipo guarda los registros en un archivo SQLite local. No incluye autenticación,
cifrado ni consentimiento explícito, por lo que no debe usarse con datos reales de
pacientes todavía.

## Pruebas

```bash
.venv/bin/pytest tests/sibo -v
.venv/bin/python tests/test_architecture.py
.venv/bin/python tests/test_clean_design.py
.venv/bin/python tests/test_god_components.py
.venv/bin/ruff check src tests
```
