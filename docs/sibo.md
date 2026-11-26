# SIBO Balance — módulo de ML nutricional

Herramienta de apoyo para personas con SIBO (sobrecrecimiento bacteriano en el intestino
delgado). Permite registrar comidas, estimar una curva de gases y recibir recomendaciones
de alimentos desinflamatorios.

> **Aviso clínico:** es una herramienta educativa y de apoyo. No reemplaza la evaluación,
> el diagnóstico ni el tratamiento de un profesional de la salud.

> **Estado de los datos:** el modelo se entrena con etiquetas reales autoinformadas de
> malestar a las 2 h, y solo se activa si supera a la heurística en una validación temporal.
> Sin muestras suficientes se usa la heurística y la banda es plana. La banda resume errores
> observados, no es un intervalo de confianza clínico.

## Qué incluye

- **Base nutricional semilla** (`src/infrastructure/sibo/data/alimentos.csv`): 57 alimentos
  con macros, fibra, categoría FODMAP y scores de potencial inflamatorio/desinflamatorio.
  Es un punto de partida editable, no una tabla clínica validada.
- **Registro de comidas** (alimento, porción, fecha/hora, síntomas y notas) y su
  **seguimiento de síntomas a las 2 h** en SQLite local.
- **Modelo híbrido explicable**: `RandomForestRegressor` entrenado con etiquetas reales
  + heurística nutricional transparente. Devuelve el pico estimado de gases (0-100).
- **Curva de gases** por día, semana o mes, con banda derivada de los errores de validación.
- **Recomendaciones** de alimentos desinflamatorios según FODMAP, scores y consumo reciente.
- **Frontend** vanilla HTML/CSS/JS con paleta verde/azul institucional.

## Arquitectura

```
src/
├── domain/sibo/                     Entidades, puertos, eventos y reglas puras
├── application/sibo/                DTOs, mappers y casos de uso
├── adapters/sibo/
│   ├── controllers/                 Orquestación HTTP sin FastAPI
│   ├── presenters/                  Esquemas de respuesta HTTP
│   └── gateways/                    Adaptadores SQLite con conexión inyectada
└── infrastructure/sibo/
    ├── database.py                  Conexión, esquema y migración SQLite
    ├── seed.py                      Carga del dataset semilla
    ├── ml/                          Features, entrenamiento y modelo híbrido (sklearn)
    ├── fastapi/                     Routers y composición de la app
    ├── data/alimentos.csv           Dataset semilla
    └── web/                         Interfaz de usuario
```

El dominio no importa FastAPI, SQLite ni scikit-learn. La conexión SQLite se crea en
infraestructura y se inyecta en los gateways por parámetro. La estructura es verificada por
`tests/test_estructura_canonica.py`; las dependencias, por `tests/test_architecture.py`.

## Cómo ejecutarlo

Desde la raíz del repositorio:

```bash
./run.sh install          # crea/actualiza .venv
./run.sh sibo             # http://localhost:8001
```

La base SQLite se crea en `src/infrastructure/sibo/data/sibo.db` (ignorada por git). Las
columnas `sintomas_2h` y `fecha_sintomas_2h` se migran automáticamente si la base ya existía.

## API

Prefijo: `/api/sibo`

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/salud` | Estado del módulo |
| GET | `/alimentos?busqueda=` | Lista/busca alimentos |
| POST | `/registros` | Registra una comida |
| PATCH | `/registros/{id}/sintomas-2h` | Guarda la etiqueta real de malestar a las 2 h |
| GET | `/registros?desde=&hasta=` | Lista registros con su seguimiento |
| DELETE | `/registros/{id}` | Elimina un registro |
| GET | `/gases?rango=dia\|semana\|mes&fecha=` | Curva estimada de gases |
| GET | `/recomendaciones?limite=` | Alimentos desinflamatorios sugeridos |
| GET | `/modelo` | Estado actual del predictor |
| POST | `/modelo/reentrenar` | Reentrena con todas las etiquetas reales disponibles |

El `PATCH` acepta `{"sintomas": 0-10, "fecha": "ISO opcional"}`. Si se omite la fecha se usa
la hora actual. Solo se aceptan mediciones entre 1,5 y 4 h después de la comida: una
medición inmediata sería una fuga porque repetiría el `sintomas` ya usado como feature.

Documentación interactiva: `http://localhost:8001/docs`.

## Modelo

1. Al registrar la comida se guardan las features disponibles en ese momento: alimento,
   porción, hora y síntomas previos (0-10).
2. Entre 1,5 y 4 h después se registra el malestar real; esa etiqueta se escala a 0-100.
3. `cargar_muestras` descarta seguimientos fuera de ventana y construye el vector con
   `caracteristicas()`, que no incluye la etiqueta ni su fecha.
4. Las muestras se ordenan por fecha y se parten 80/20. El `RandomForest` entrena con el
   pasado y se evalúa solo con el futuro.
5. Se comparan los MAE del modelo y de la heurística en esa validación. Si el modelo no
   mejora, se usa la heurística sola y no se muestra banda.
6. `PoliticaModelo` (`src/domain/sibo/value_objects.py`) define los pesos 70/30 y los
   percentiles 10/90. Está en el dominio porque regula el problema, no sklearn. Los pesos
   solo se aplican cuando el modelo superó a la heurística.
7. La banda son los percentiles de los residuos de la validación, desplazados desde el pico.
   Sin residuos, bajo = pico = alto.
8. Sobre cada comida se aplica una curva de absorción con pico a las 2 h y ventana de 8 h
   para construir la serie temporal.

### Qué falta para el seguimiento personal

El objetivo de producto es un seguimiento de 30 días con comidas compuestas, detección de
patrones personales (alimentos y combinaciones asociadas a síntomas), predicción de síntomas
y aprendizaje continuo. Eso requiere:

- comidas con varios alimentos (`Comida` + `ItemComida`) y entidad `Sintoma`;
- suficientes etiquetas reales por persona y métricas antes de mostrar predicciones;
- consentimiento explícito, control de acceso y borrado/exportación de datos de salud;
- validación por un profesional antes de cualquier uso clínico.

## Privacidad

El prototipo guarda los registros en un archivo SQLite local. No incluye autenticación,
cifrado ni consentimiento explícito, por lo que no debe usarse con datos de pacientes.
Las etiquetas autoinformadas se descartan si no cumplen la ventana temporal.

## Pruebas

```bash
./run.sh test -q tests/sibo
.venv/bin/python tests/test_estructura_canonica.py
.venv/bin/python tests/test_architecture.py
.venv/bin/python tests/test_clean_design.py --strict
.venv/bin/python tests/test_god_components.py
./run.sh lint
```
