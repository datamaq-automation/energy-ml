"""src/domain/educacion/modelos.py — Constantes del caso educacion: momento de predicción y límites."""

from __future__ import annotations

#: Semilla fija para todos los estimadores (regla 7 de la sección 4 del issue).
SEED = 42

#: Variables de desempeño y hábitos permitidas para la Tarea A (sección 2 del issue).
#: G2 queda fuera por el momento de predicción; G3 es la etiqueta y jamás entra.
CLUSTER_FEATURES: tuple[str, ...] = ("G1", "studytime", "failures", "absences")

#: Rango de k evaluado en la Tarea A (sección 3, tarea A.3).
K_MIN = 2
K_MAX = 6

#: Umbral de la etiqueta: desaprobado = G3 < 10 (sección 2 del issue).
FAIL_THRESHOLD = 10

#: Variables permitidas para la Tarea B (sección 2 del issue): las 16 coherentes
#: con el momento de predicción declarado — sin G2 (desconocida) ni G3 (etiqueta).
#: Decisión del PR: sex y school quedan FUERA del modelo — costaban ~4 puntos de
#: recall y ampliaban la brecha por sexo del mejor modelo de 24 a 13 puntos —
#: pero siguen auditándose como subgrupos de equidad en la Tarea C.
MODEL_FEATURES: tuple[str, ...] = (
    "G1",
    "studytime",
    "failures",
    "absences",
    "higher",
    "Medu",
    "Fedu",
    "age",
    "address",
    "famsup",
    "schoolsup",
    "internet",
    "goout",
    "Dalc",
    "Walc",
    "health",
)

#: Categóricas del modelo → OneHotEncoder; el resto → StandardScaler (ambos solo sobre train).
#: sex y school también son categóricas del dataset, pero hoy no entran al modelo.
CATEGORICAL_FEATURES: tuple[str, ...] = (
    "address",
    "higher",
    "famsup",
    "schoolsup",
    "internet",
)
NUMERIC_FEATURES: tuple[str, ...] = tuple(
    column for column in MODEL_FEATURES if column not in CATEGORICAL_FEATURES
)

#: Split 80/20 estratificado (reglas 2 y 3), siempre antes de transformar.
TEST_SIZE = 0.2

#: Clases de la etiqueta; DESAPROBADO es la clase positiva de las métricas.
APROBADO = 0
DESAPROBADO = 1

#: Orden de impresión de la tabla comparativa de la Tarea B.
MODEL_LABELS: tuple[tuple[str, str], ...] = (
    ("baseline", "línea base"),
    ("logistic_regression", "regresión logística"),
    ("random_forest", "bosque aleatorio"),
)

#: Subgrupos de equidad exigidos por la Tarea C (sección 3 del issue).
#: Se auditan aunque no sean predictores: la equidad se mide sobre el resultado,
#: no sobre las entradas del modelo.
SUBGROUP_COLUMNS: tuple[str, ...] = ("sex", "school")

#: Brecha máxima tolerada entre subgrupos antes de declarar una diferencia relevante.
FAIRNESS_GAP_THRESHOLD = 0.10

#: Subgrupo con menos casos que esto: la métrica es ruidosa y hay que leerla con cuidado.
MIN_SUBGROUP_N = 30

#: Recomendación de uso (Tarea C.3): qué hacer y qué NO hacer con cada predicción.
RECOMMENDATION: tuple[str, ...] = (
    "SÍ: usar la predicción para priorizar apoyo — tutorías, refuerzo y seguimiento "
    "temprano antes del examen.",
    "SÍ: revisar cada predicción con docentes o tutores: el modelo ordena la fila de "
    "atención, no decide.",
    "SÍ: mirar las métricas por subgrupo antes de confiar en el modelo para un perfil particular.",
    "NO: usar el resultado para decisiones administrativas (sanciones, exclusiones o "
    "mesas de examen) sin revisión humana.",
    "NO: presentar el resultado al estudiante como un destino cerrado: es una señal de "
    "riesgo, no una sentencia.",
    "NO: almacenar ni compartir predicciones con datos identificables de estudiantes.",
)

#: Conclusión de una página: qué se puede predecir, con qué límites y cómo usar
#: el resultado sin perjudicar al estudiante. Los números citados corresponden a
#: la corrida real con el dataset UCI 320 y semilla 42 (el test de integración
#: los contrasta contra los modelos vivos).
CONCLUSION: tuple[str, ...] = (
    "1. Qué se puede predecir. Con la información disponible al inicio del curso "
    "(G1, hábitos de estudio, antecedentes y contexto sociodemográfico) es posible "
    "identificar estudiantes con riesgo de desaprobar y agruparlos en perfiles claros. "
    "El agrupamiento (Tarea A) separó dos perfiles — buen desempeño con buena asistencia, "
    "23,6 % desaprobados, frente a desempeño bajo con ausencias frecuentes, 71,4 % — y los "
    "modelos supervisados (Tarea B) superan con holgura a la línea base: la regresión "
    "logística alcanzó F1 0,77 y recall 0,69, y el bosque aleatorio subió el recall a 0,77, "
    "es decir, detecta a más de 3 de cada 4 estudiantes en riesgo que la línea base ignora "
    "por completo (recall 0,00). Predecir bien a la mayoría no alcanza: lo que importa es no "
    "perder a quien está en riesgo.",
    "2. Con qué límites. El accuracy de la línea base (0,67) mostraba justo el peligro de "
    "conformarse con la mayoría. La regresión logística todavía se pierde 8 de los 26 "
    "desaprobados del test y el bosque aleatorio comete 9 falsos positivos: ningún modelo "
    "está libre de error y cada error tiene consecuencias humanas. La equidad (Tarea C) "
    "mostró brechas relevantes: el recall para mujeres (0,65) es 13 puntos menor que para "
    "varones (0,78), y el resultado aparentemente perfecto de la escuela MS se apoya en solo "
    "10 estudiantes y 3 desaprobados, por lo que es una métrica ruidosa. sex y school salieron "
    "del modelo: costaban unos 4 puntos de recall, y hoy entran solo para auditar la equidad "
    "en la Tarea C, no como predictores. Por último, "
    "el dataset cubre una sola materia, en dos escuelas y 395 estudiantes: los resultados no "
    "se generalizan a otra institución sin volver a validarlos.",
    "3. Cómo usar el resultado sin perjudicar al estudiante. El modelo sirve para priorizar "
    "apoyo —tutorías, refuerzo y seguimiento temprano— con revisión humana de cada caso por "
    "docentes o tutores, y mirando siempre las métricas por subgrupo antes de confiar en él "
    "para un perfil particular. NO debe usarse para decisiones administrativas (sanciones, "
    "exclusiones o mesas de examen) sin revisión humana; NO debe presentarse al estudiante "
    "como un destino cerrado: es una señal de riesgo, no una sentencia; y NO deben almacenarse "
    "ni compartirse predicciones con datos identificables. En resumen: el modelo acompaña la "
    "decisión humana, nunca la reemplaza.",
)
