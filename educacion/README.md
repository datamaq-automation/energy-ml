# Declaración de momento de predicción y variables permitidas

**Caso:** Riesgo de desaprobar una materia — agrupamiento, predicción y equidad ([Issue #5](https://github.com/datamaq-automation/energy-ml/issues/5))
**Fecha:** 2026-11-13
**Estado:** ✅ Declaración aprobada por el alumno antes de escribir código (entregable 1 de la sección 5 del issue).

---

## 1. Momento de predicción (declarado)

> **Se predice al principio del curso, con la información disponible hasta el primer período: la nota del primer parcial (`G1`) recién conocida y variables de contexto. No se conoce `G2` (segunda nota parcial) en ese momento.**

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

**Contexto y sociodemográficas (Tarea B — clasificación):**
`G1`, `studytime`, `failures`, `absences`, `higher`, `Medu`, `Fedu`, `school`, `sex`, `age`, `address`, `famsup`, `schoolsup`, `internet`, `goout`, `Dalc`, `Walc`, `health`

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
