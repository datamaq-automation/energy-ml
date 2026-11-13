# Especificación: Modelo predictivo de crecidas de ríos y precipitaciones (Issue #9)

**Versión:** 0.1 (borrador para validar)
**Fecha:** 2026-11-06
**Estado:** Borrador — dominio y cliente INA implementados en la rama; decisiones de datos parciales (sección 7)

**Progreso:**
- ✅ Dominio puro: `src/domain/crecidas/modelos.py` (`Escenario`, `Umbrales`, `AlertaTemprana`) y `reglas.py` (`clasificar_escenario`, `generar_alerta`).
- ✅ Tests unitarios: `tests/unit/crecidas/test_reglas_crecidas.py` (límites inclusivos, orden de umbrales, horizonte).
- ✅ Niveles oficiales Tigre en `src/domain/crecidas/modelos.py` (`NIVELES_OFICIALES_TIGRE`, `NivelesOficiales.a_umbrales`): alerta 3,30 m; evacuación 3,80 m, mapeada a crecida.
- ✅ Cliente de series INA y parser CSV: `src/infrastructure/crecidas/ina_serie.py` (tests con descargador inyectado, sin red).
- 🟡 Dudas de diseño en #10: enfoque temporal y horizonte propuestos (comentario del 2026-11-07). Siguen abiertas vigilancia, notificación y material pedagógico.
- ⏳ Pendiente: repositorio de observaciones, pronosticador, casos de uso, API y CLI (dependen de la fuente de datos).
**Origen:** Issue #9 — "modelo predictivo de crecida de rios y precipitaciones"

---

## 1. Resumen

Desarrollar un modelo de aprendizaje automático que, a partir del historial de
**precipitaciones** y **niveles de río**, anticipe su evolución a corto plazo para
identificar escenarios de **inundación** y generar **alertas tempranas**.

Relación con el resto del proyecto: el repo hoy modela consumo eléctrico (NILM).
Este issue introduce un dominio nuevo (hidrología). Se respeta la misma arquitectura
(Clean Architecture: dominio puro → aplicación → infraestructura) y el mismo estilo
pedagógico (reglas explícitas y auditables junto al modelo estadístico).

---

## 2. Alcance

### Incluido
- Ingesta de series de nivel de río (m): Tigre con paso diario, San Fernando agregado a diario. La precipitación queda fuera de la primera versión (sección 7).
- Ingeniería de variables: rezagos (lags), acumulados de lluvia en ventanas (1h, 6h, 24h),
  tendencia del nivel, estacionalidad horaria.
- Modelo de **pronóstico** diario del nivel de río en Tigre, a horizontes de 1, 2 y 3 días,
  con línea base de persistencia para comparar.
- Clasificación de **escenario** según umbrales de nivel (normal / vigilancia / alerta / crecida),
  con reglas explícitas.
- Generación de **alertas tempranas** (estructura de alerta + endpoint REST de lectura).
- Evaluación con partición temporal (sin mezclar futuro en entrenamiento) y métricas de error
  y de detección de eventos (precisión / recall de crecidas).

### Excluido (por ahora)
- Modelos hidrológicos físicos (HEC-RAS, SWAT) o modelos de lluvia-escorrentía complejos.
- Envío de alertas por SMS/email/WhatsApp (solo se registran y se exponen por API).
- Pronóstico meteorológico externo (solo se usan observaciones pasadas; ver sección 7).
- Frontend nuevo: se reutiliza la estructura estática de `web/` si hace falta, en fase posterior.

---

## 3. Requisitos funcionales

| ID | Requisito |
|----|-----------|
| RF-1 | Cargar mediciones de precipitación y nivel de río desde CSV (mismo patrón que `CsvMedicionRepository`). |
| RF-2 | Validar la serie: timestamps monótonos, paso uniforme, valores no negativos para lluvia, detección de huecos. |
| RF-3 | Construir variables a partir de la serie sin fuga de información (solo datos ≤ t para predecir t+H). |
| RF-4 | Entrenar un regresor para el nivel en t+H (H = 1, 2 o 3 días) y compararlo contra persistencia (último valor observado). |
| RF-5 | Clasificar el escenario por umbrales de nivel configurables (ver RF-7). |
| RF-6 | Emitir una `AlertaTemprana` cuando el escenario previsto sea de alerta o crecida, con hora de emisión, horizonte y nivel previsto. |
| RF-7 | Umbrales de nivel por estación en configuración (no hardcodeados), con valores por defecto documentados. |
| RF-8 | Exponer `GET /api/v1/crecidas/pronostico` y `GET /api/v1/crecidas/alertas` (versionado v1). |
| RF-9 | CLI: `./run.sh train-crecidas` y `./run.sh evaluate-crecidas`. |
| RF-10 | Reporte de evaluación: MAE/RMSE del pronóstico, mejora frente a persistencia, precisión y recall de eventos de crecida. |

## 4. Requisitos no funcionales

- **Dominio puro:** entidades, reglas de umbral y generación de alertas sin dependencias externas.
- **Reproducibilidad:** semilla fija y datos de ejemplo versionados (sintéticos) para tests.
- **Auditabilidad:** cada alerta guarda los valores de entrada y el umbral que la disparó.
- **Tests:** unitarios para reglas de dominio, integración para CSV y modelo, e2e para endpoints.
  Mantener la regla de arquitectura de `tests/test_architecture.py`.
- **Lint/format:** `ruff` y `pre-commit` sin excepciones.

---

## 5. Diseño propuesto (por capas)

```
src/domain/crecidas/
  ├── modelos.py        Observacion (lluvia_mm, nivel_m), Pronostico, Umbral, Escenario, AlertaTemprana
  ├── reglas.py         clasificar_escenario(nivel, umbrales) -> Escenario  (puro)
  ├── puertos.py        RepositorioObservaciones, Pronosticador, RepositorioAlertas, Bitacora
  └── servicios.py      generar_alerta(pronostico, umbrales) -> AlertaTemprana | None

src/application/crecidas/
  ├── use_cases/entrenar_pronosticador.py
  ├── use_cases/generar_pronostico.py
  └── dtos.py

src/infrastructure/
  ├── csv/              CsvObservacionesRepository
  ├── sklearn/          PronosticadorNivel (p. ej. GradientBoostingRegressor o Ridge con lags)
  └── fastapi/routes/crecidas.py
```

### Escenarios y reglas (propuesta inicial, a validar)

| Escenario | Condición sobre nivel previsto `h_pred` |
|-----------|------------------------------------------|
| normal | `h_pred < umbral_vigilancia` |
| vigilancia | `umbral_vigilancia ≤ h_pred < umbral_alerta` |
| alerta | `umbral_alerta ≤ h_pred < umbral_crecida` |
| crecida | `h_pred ≥ umbral_crecida` |

Se genera `AlertaTemprana` si el escenario es **alerta** o **crecida**.
Regla adicional opcional (fuera de la primera versión, sin datos de lluvia): si la lluvia acumulada en 6 h supera `umbral_lluvia_mm`, se eleva
a vigilancia aunque el nivel previsto aún no lo indique (decisión a confirmar).

---

## 6. Plan de trabajo (commits atómicos)

1. `docs(crecidas)`: esta especificación + decisión de arquitectura.
2. `feat(domain-crecidas)`: entidades, reglas de escenario y alerta, con tests unitarios.
3. `feat(infra-crecidas)`: repositorio CSV + pronosticador sklearn con línea base de persistencia.
4. `feat(application-crecidas)`: casos de uso entrenar y generar pronóstico.
5. `feat(api-crecidas)`: rutas v1 + CLI.
6. `test(crecidas)`: evaluación temporal, e2e y regla de arquitectura.
7. `docs(crecidas)`: README/CHANGELOG y datos de ejemplo.

---

## 7. Decisiones (propuestas y pendientes)

Fuente de las propuestas: comentario de realsol760-ai en #10 (2026-11-07). Todavía no es decisión del responsable del proyecto.

1. **Fuente de datos.** Propuesta: series INA 49 (Tigre) y 52 (San Fernando). Precipitación **fuera de la primera versión** (acceso a INTA o SMN en investigación). Río de la Plata (SHN) en una **segunda etapa**, pendiente de una fuente accesible.
2. **Paso temporal y horizonte.** Propuesta: pronóstico **diario** de Tigre, con San Fernando agregado por día. Horizontes de **1, 2 y 3 días**. Queda descartado el H = 6 h del borrador original.
3. **Umbrales de nivel.** Alerta 3,30 m y evacuación 3,80 m (sección 9.1). La propuesta de #10 los llama referencias *pendientes de verificar* contra la fuente oficial; hay que confirmarlo. **Vigilancia: pendiente**, sin umbral oficial (definir si se usa percentil histórico).
4. **Destino de las alertas.** Propuesta: se guardan en registro, **sin notificaciones** en la primera versión.
5. **Uso en el curso.** Pendiente: ¿entra en `docs/` y en el cuaderno del alumno?

---

## 8. Criterios de aceptación

- Con datos sintéticos de prueba, el modelo supera a la persistencia en MAE para cada horizonte (1, 2 y 3 días).
- Dado un nivel previsto por encima del umbral de alerta, se genera exactamente una `AlertaTemprana` con escenario correcto.
- `GET /api/v1/crecidas/alertas` devuelve las alertas con sus entradas y umbrales auditables.
- La suite de tests sigue en verde y la regla de arquitectura pasa sin excepciones.

---

## 9. Datos verificados (área Tigre, consulta 2026-11-06)

Área confirmada por el responsable: **Tigre**.

### 9.1 Umbrales oficiales (Prefectura Naval Argentina, verificados)

Fuente 1: reporte oficial "Registro del estado de los ríos" de Prefectura
(`https://contenidosweb.prefecturanaval.gob.ar/alturas/pdf.php`).
Fuente 2: API de alerta del INA, estación `Tigre` (ver 9.2), que publica los mismos valores.

| Estación | Río | Alerta (m) | Evacuación (m) | Aguas bajas (m) | Cero IGN (m) |
|----------|-----|-----------:|---------------:|----------------:|-------------:|
| Tigre | Luján | **3,30** | **3,80** | 0,30 | -0,099 |
| San Fernando | Delta Paraná | 3,00 | 3,50 | — | — |
| Dique Luján | Delta Paraná | 2,30 | 2,80 | — | — |

Las alturas se miden respecto del cero de la escala de cada puerto. No se pueden comparar entre puertos.

**Consecuencia para el dominio:** Prefectura define solo *alerta* y *evacuación*. No define "vigilancia".
Nuestro `Umbrales` exige `vigilancia < alerta < crecida`. Mapeo propuesto: `alerta_m = 3.30`,
`crecida_m = 3.80` (evacuación). El valor de `vigilancia_m` queda **pendiente** (sección 7).

### 9.2 Series del INA para Tigre (verificadas)

Base: `https://alerta.ina.gob.ar/a5/getObservaciones?tipo=puntual&series_id=<ID>&timestart=<AAAA-MM-DD>&timeend=<AAAA-MM-DD>&format=csv`
(endpoint público, sin token; se verificó desde el propio front de `alerta.ina.gob.ar/a5/secciones`).

| Serie INA | Estación | Variable | Paso observado | Cobertura | Observación |
|----------:|----------|----------|----------------|-----------|-------------|
| **49** | Tigre (id_externo 430, red Prefectura) | Altura hidrométrica (H) | **Diario** (mediana 24 h) | 2006-01-01 → hoy | Máx. hueco 17 días. Es la serie objetivo natural. |
| **52** | San Fernando | Altura hidrométrica (H) | **Horario** (mediana 1 h) | 2011-01-01 → hoy | 127 924 registros. Máx. hueco 61 días. Rango −0,41 a 3,60 m. |

Serie 52 es la candidata a **predictor aguas arriba** del Río de la Plata/Delta; la serie 49 es el objetivo.

### 9.3 Precipitación

- Existe una estación INTA "San Fernando - EEA Delta" (estación id 1600, localidad Tigre) con
  precipitación diaria, horaria y de 3 h en el INA.
- **No es accesible por la API pública**: las series 2463, 3952, 4352 y 5321 devuelven 0 registros
  (la estación figura con `public_his_plata = false`).
- Hay que pedir acceso a INTA o usar SMN (sección 7).

### 9.4 Implicancias para el diseño

1. El **paso de la serie objetivo (49) es diario**, y el horizonte de 6 h del borrador **no es alcanzable
   con esa serie**. Para un pronóstico de horas hace falta la serie horaria de San Fernando (52) como
   entrada, y una serie horaria del objetivo que hoy no existe públicamente. Hay que decidir el enfoque (sección 7).
2. El nivel en el Río de la Plata (aviso SHN por sudestada) no está en esta API. Puede aparecer
   como factor de riesgo no modelado.
3. Los umbrales de la spec original (5 min) quedan desplazados por la realidad de la fuente.
4. Enfoque propuesto en #10: pronóstico diario con horizontes de 1 a 3 días (sección 7, punto 2).
5. Los niveles de 9.1 figuran como verificados, pero el comentario de #10 los marca como pendientes de verificar. Hay que resolver esa discrepancia antes de usarlos como umbral de crecida.
