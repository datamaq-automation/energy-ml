# Declaración de momento de predicción y variables permitidas

**Caso:** Riesgo de desaprobar una materia — agrupamiento, predicción y equidad ([Issue #5](https://github.com/datamaq-automation/energy-ml/issues/5))
**Fecha:** 2026-11-13
**Última actualización:** 2026-11-20 — refactor a las cuatro capas de `src/`, decisión sobre `sex`/`school` y análisis pedidos en el [comentario del PR #19](https://github.com/datamaq-automation/energy-ml/pull/19#issuecomment-6915631383).
**Estado:** ✅ Declaración aprobada por el alumno antes de escribir código (entregable 1 de la sección 5 del issue).

---

## 1. Momento de predicción (declarado)

> **Se predice al principio del curso, con la información disponible hasta el primer período: la nota del primer parcial (`G1`) recién conocida y variables de contexto. No se conoce `G2` (segunda nota parcial) en ese momento.**

**Fecha en el calendario escolar (item del comentario del PR):** el momento es **el día en que la escuela publica las notas del primer parcial —semana 6 del curso, aproximadamente—**, no "la variable `G1`". En esa fecha existe **un dato que no existía antes: `G1`, la nota del primer parcial**, recién rendida y publicada. Antes de esa fecha solo hay variables de contexto (edad, escuela, antecedentes familiares, hábitos) y la predicción tendría que prescindir de `G1`; después de esa fecha, `G2` todavía no se rindió y `G3` recién a fin de curso. La fecha es una convención declarada: el dataset UCI no trae calendario, pero así "momento de predicción" significa un instante concreto del curso y no una lista de columnas.

Esto sigue la sección 2 del issue: *"si el alumno predice al inicio del curso, solo puede usar `G1` y variables de contexto"*. La decisión fue confirmada por el alumno en el [comentario de plan del issue #5](https://github.com/datamaq-automation/energy-ml/issues/5#issuecomment-6863093002).

**Consecuencia operativa:** `G2` queda fuera de todas las tareas (A, B y C), no solo de la Tarea B.

---

## 2. Variable objetivo (etiqueta)

- `desaprobado = G3 < 10` — construida **solo** a partir de `G3` (nota final, escala 0–20).
- `G3` **nunca** entra como variable explicativa de ningún modelo. Es la etiqueta, no una variable de entrada.

---

## 3. Lista de variables

### ❌ Prohibidas (fuga de datos)

| Variable | Motivo |
|----------|--------|
| `G3` | Es la base de la etiqueta; usarla como entrada sería trivial y además fuga de datos (regla 1 de la sección 4). |
| `G2` | No se conoce en el momento de predicción declarado (inicio de curso, solo `G1`). |

### ✅ Permitidas (sección 2 del issue)

**Desempeño y hábitos (Tarea A — agrupamiento):**
`G1`, `studytime`, `failures`, `absences`

**Contexto y sociodemográficas (Tarea B — clasificación): las 16 variables del modelo**
`G1`, `studytime`, `failures`, `absences`, `higher`, `Medu`, `Fedu`, `age`, `address`, `famsup`, `schoolsup`, `internet`, `goout`, `Dalc`, `Walc`, `health`

**Excluidas del modelo por decisión, aunque el momento de predicción las permite:** `sex`, `school`
Se decidió sacarlas de `MODEL_FEATURES` (justificación numérica en [§6.4](#64-decisión-sobre-sex-y-school)) y siguen auditándose como subgrupos de equidad en la Tarea C (`SUBGROUP_COLUMNS`).

> Si en el futuro se propone una variable nueva, primero hay que preguntar: *¿se conoce en el momento de predicción declarado?* No se asume.

---

## 4. Datos

- **Fuente:** *Student Performance* — UCI Machine Learning Repository (dataset 320).
- **Archivo local:** `datos/educacion/student-mat.csv` (separador `;`, 395 estudiantes, 33 columnas, sin valores faltantes).
- **Licencia:** **CC BY 4.0** (verificada en la página de UCI el 2026-11-13). Permite compartir y adaptar el dataset con atribución.
- **Cita:** Cortez, P. (2008). *Student Performance* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5TG7T
- **Distribución de la etiqueta:** 130 de 395 estudiantes desaprobados (32,9 %) → clase minoritaria, por eso se usan métricas más allá de accuracy y split estratificado.

---

## 5. Reglas que gobiernan el módulo (sección 4 del issue)

1. Cero fuga de datos (`G3` nunca; `G2` solo si el momento lo permite — hoy no lo permite).
2. Split **antes** de transformar; `fit` de escaladores/codificadores solo sobre train.
3. Split estratificado por la etiqueta, `random_state=42`.
4. Métricas adecuadas: precisión, recall, F1 y matriz de confusión sobre "desaprobado".
5. Equidad obligatoria: análisis por subgrupo (`sex`, `school`) en toda evaluación.
6. Privacidad: no imprimir ni guardar datos identificables de estudiantes.
7. Semilla fija `random_state=42` donde corresponda.
8. Sin rutas absolutas ni credenciales en el código.
9. Type hints + `ruff check --fix` + `ruff format` antes de cerrar cada tarea.

---

## 6. Análisis pedidos en el comentario del PR #19

### 6.1 Línea base: la regla `G1 < 10`

Métricas de la regla *"apoyo si `G1 < 10`"* sobre **el mismo test que usan los modelos** (79 estudiantes, 26 desaprobados, split estratificado `random_state=42`):

| Predictor | Accuracy | Precisión | Recall | F1 | FN (se escapan) | FP (apoyo innecesario) |
|-----------|----------|-----------|--------|----|-----------------|------------------------|
| Regla `G1 < 10` | 0,823 | 0,731 | 0,731 | 0,731 | 7 | 7 |
| Regresión logística | 0,861 | 0,857 | 0,692 | 0,766 | 8 | 3 |
| Bosque aleatorio | 0,810 | 0,690 | 0,769 | 0,727 | 6 | 9 |

**Lectura:** la regla simple casi empata con los modelos. El bosque detecta **1 estudiante más** (FN 7 → 6) a cambio de **2 apoyos innecesarios más** (FP 7 → 9) y un F1 menor (0,727 contra 0,731). La regresión logística se equivoca al revés: 1 FN más que la regla, pero 4 FP menos y mucha más precisión. El aporte real de los modelos no es descubrir quién aprueba —eso ya lo hace `G1`—, sino **ordenar la fila de atención** cuando el apoyo no alcanza para todos. Queda dicho en la conclusión del módulo.

### 6.2 Umbrales de 9 a 12

Regla *"apoyo si `G1 < umbral`"*, sobre el mismo test:

| Umbral | Apoyos (de 79) | Precisión | Recall | F1 |
|--------|----------------|-----------|--------|----|
| 9  | 19 (24,1 %) | 0,789 | 0,577 | 0,667 |
| 10 | 26 (32,9 %) | 0,731 | 0,731 | 0,731 |
| 11 | 38 (48,1 %) | 0,658 | 0,962 | 0,781 |
| 12 | 48 (60,8 %) | 0,542 | 1,000 | 0,703 |

**Si la escuela puede apoyar al 30 % de los alumnos** (= 23,7 ≈ 24 de 79): **elegiría `G1 < 9`**, el único umbral que cabe (19 apoyos, 24,1 %). Cuesta recall: se escapan 11 de los 26 desaprobados (recall 0,577). Con los 5 lugares que quedan libres, usaría el ranking de riesgo del modelo para elegir a quién sumar primero. Si la capacidad creciera al 48 %, `G1 < 11` es el mejor equilibrio (recall 0,962, F1 0,781); a 61 % (`G1 < 12`) no se escapa ningún desaprobado, pero **1 de cada 2 apoyos es innecesario**.

### 6.3 Equidad: tasas de desaprobados por grupo y decisión

Dataset completo (395 estudiantes):

| Subgrupo | Desaprobados | Tasa |
|----------|--------------|------|
| Mujeres (`sex = F`) | 75 / 208 | 36,1 % |
| Varones (`sex = M`) | 55 / 187 | 29,4 % |
| Escuela `GP` | 113 / 349 | 32,4 % |
| Escuela `MS` | 17 / 46 | 37,0 % |

Test (79 estudiantes, lo que ve `analyze_fairness`): mujeres 17/43 = **39,5 %**, varones 9/36 = **25,0 %** — brecha de 14,5 puntos, por eso la Tarea C marca *"la etiqueta está desbalanceada por subgrupo"*. Por escuela: `GP` 23/69 = 33,3 % y `MS` 3/10 = 30,0 % (con solo 10 estudiantes de `MS`, esa métrica es ruidosa).

**Decisión si la diferencia de recall entre grupos es grande (≥ 10 puntos):**

1. **No usar el modelo para decidir por un perfil particular sin revisión humana:** si el recall de un grupo es 13–24 puntos menor, una estudiante clasificada "baja prioridad" no puede quedarse sin apoyo por una decisión automática.
2. **Auditar los falsos negativos del grupo desfavorecido** con docentes: cada caso no detectado se revisa a mano antes de volver a confiar en el modelo para ese grupo.
3. **Publicar la brecha junto con las métricas**: nunca reportar solo el número global de desempeño.
4. **Si la brecha se mantiene ≥ 10 puntos después de la revisión, no desplegar** la predicción para ese subgrupo: seguir con la regla `G1 < umbral` y criterio docente, y reunir datos más parejos por grupo antes de reintentar.

### 6.4 Decisión sobre `sex` y `school`

Comparación con y sin las dos variables (semilla 42, split 316/79, mismas 79 filas de test):

| Modelo | Variables | Precisión | Recall | F1 | Recall F | Recall M | Brecha por sexo |
|--------|-----------|-----------|--------|----|----------|----------|-----------------|
| Regresión logística | 18 (con `sex`, `school`) | 0,864 | 0,731 | 0,792 | 0,647 | 0,889 | 24 puntos |
| Regresión logística | **16 (sin)** | 0,857 | 0,692 | 0,766 | 0,647 | 0,778 | **13 puntos** |
| Bosque aleatorio | 18 (con `sex`, `school`) | 0,700 | 0,808 | 0,750 | 0,706 | 1,000 | 29 puntos |
| Bosque aleatorio | **16 (sin)** | 0,690 | 0,769 | 0,727 | 0,647 | 1,000 | 35 puntos |

Por escuela, el recall de `GP` pasa de 0,696 a 0,652 y `MS` queda en 1,000 (10 estudiantes y 3 desaprobados en test: métrica ruidosa, no una fortaleza).

**Decisión: `sex` y `school` salen del modelo (16 variables).** Cuesta unos 4 puntos de recall en ambos modelos (LR 0,731 → 0,692; RF 0,808 → 0,769) y 1–2 puntos de precisión, y a cambio la brecha de identificación por sexo del **mejor modelo** baja de 24 a 13 puntos: las mujeres quedan igual (0,647) y los varones bajan de 0,889 a 0,778, es decir, el modelo sin `sex` deja de "sobre-detectar" varones. Qué se hace con cada resultado:

- **Con las 18 (corrida histórica):** sirve para *medir* la brecha, no para desplegar: el modelo usa el atributo y puede amplificar la desigualdad que después audita.
- **Con las 16 (hoy):** se despliega con revisión humana y auditoría por subgrupo en la Tarea C, dejando constancia en la conclusión de que queda una brecha de 13 puntos.
- **Ojo:** en el bosque aleatorio la brecha por sexo **no** baja (29 → 35 puntos): por eso la conclusión cita al mejor modelo por F1 (regresión logística), que es el que reporta la Tarea C.

La comparación es reproducible: `tests/educacion/test_ablacion_sex_school.py` corre las dos variantes × los dos modelos y fija estos números como contratos (costo de recall ≤ 6 puntos, brecha con ≥ 0,20 y sin al menos 5 puntos menor, y el mejor modelo sigue siendo la regresión logística).

---

## 7. Estado de entregables (sección 5 del issue)

- [x] Declaración escrita del momento de predicción y de las variables permitidas → **este documento**.
- [x] Módulo con las tareas A, B y C, en orden → `fail_risk.py` (punto de entrada de las cuatro capas de `src/`).
- [x] Tabla de métricas de la línea base, la regresión logística y el bosque aleatorio → imprime `run_task_b()`.
- [x] Gráficos de codo y silueta de la Tarea A → imprime `run_task_a()` (solo pantalla, sin PNG).
- [x] Tabla de recall y precisión por subgrupo (`sex`, `school`) → imprime `run_task_c()`.
- [x] Conclusión de una página en español → `CONCLUSION` al final del módulo (`run_conclusion()`).
- [x] Línea base `G1 < 10` calculada sobre el mismo test que los modelos y comparada → [§6.1](#61-línea-base-la-regla-g1--10).
- [x] Tabla de umbrales 9–12 con precisión, recall y apoyos, y umbral elegido con capacidad del 30 % → [§6.2](#62-umbrales-de-9-a-12).
- [x] Tasas de desaprobados por grupo con la decisión ante brechas grandes → [§6.3](#63-equidad-tasas-de-desaprobados-por-grupo-y-decisión).
- [x] Momento de predicción escrito como fecha del calendario escolar → [§1](#1-momento-de-predicción-declarado).
- [x] Decisión sobre `sex`/`school` justificada con la comparación con y sin ellas → [§6.4](#64-decisión-sobre-sex-y-school).
- [x] Tests: `MODEL_FEATURES` sin `G2` ni `G3`, y encoder ajustado solo con train → `tests/educacion/test_fail_risk_tarea_b.py`.

---

## 8. Cómo ejecutar

```bash
python -m educacion.fail_risk      # imprime Tareas A, B, C y la conclusión en pantalla
pytest tests/educacion -q          # tests del caso de estudio
python tests/test_architecture.py  # gauntlet de arquitectura del repo
./run.sh lint                      # ruff check + ruff format (Windows: python -m ruff check .)
```

Los gráficos de codo y silueta se muestran **solo en pantalla** (no se guardan archivos). La salida del módulo sale por el logger del proyecto (`backend-api`), no por `print()` — regla de `CONTRIBUTING.md` §4.

---

## 9. Contenido

- `fail_risk.py` — punto de entrada que compone las Tareas A (K-means), B (clasificación), C (equidad) y la conclusión, en orden.
- `../src/domain/educacion/` — constantes (`MODEL_FEATURES`, `FAIL_THRESHOLD`, `CONCLUSION`), reglas y puertos.
- `../src/application/educacion/` — preparación, evaluación y los casos de uso `run_task_a/b/c` y `run_conclusion`.
- `../src/infrastructure/sklearn/educacion_agrupador.py` y `educacion_modelos.py` — KMeans, regresión logística y bosque aleatorio.
- `../src/infrastructure/graficos/educacion.py` — gráficos de codo y silueta (solo pantalla).
- `../src/adapters/educacion/` — gateway CSV de estudiantes y controlador que ejecuta las cuatro partes.
- `tests/educacion/` — 87 tests de todo el módulo (incluye la ablativa de `sex`/`school`).
- `../datos/educacion/student-mat.csv` — dataset UCI 320 (CC BY 4.0, ver sección 4).
