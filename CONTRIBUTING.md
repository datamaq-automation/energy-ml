# Cómo contribuir a energy-ml

Este repo es un caso de estudio real del curso de Aprendizaje Automático (ISFT N° 199, Tigre). Contribuir acá es la forma de practicar lo que aprendés **y** la forma en que evaluamos tu participación.

## 1. Qué cuenta como contribución

| Tipo | Ejemplos |
|---|---|
| **Pull Request (PR)** | Resolver un issue, agregar un caso de estudio, corregir un error, mejorar la documentación |
| **Issue** | Proponer un caso nuevo, plantear una duda concreta con contexto, reportar un error |
| **Comentario** | Responder una duda de un compañero, revisar un PR, aportar un dato o una fuente, plantear un bloqueo |

Cada aporte cuenta, aunque sea chico. Se mira la **calidad**, no la cantidad: un comentario que hace avanzar la discusión vale más que diez que dicen "buen trabajo".

### Qué va en cada lugar

Un issue es un espacio **público y compartido**: lo lee todo el curso. Para que sea útil, cada cosa va en su lugar:

| Qué | Dónde |
|---|---|
| Notas, plan y reportes de cada paso | Un archivo local o el README de tu rama |
| La historia de lo que hiciste | Commits con mensajes claros |
| Mostrar tu trabajo y recibir revisión | Un PR a `develop`; puede ser en borrador (*Draft*) |
| Una duda, un bloqueo o una decisión a confirmar | Un comentario en el issue |
| El resultado final y sus limitaciones | La descripción del PR |

**Regla práctica:** un reporte de avance en un issue sirve cuando enlaza a trabajo que los demás pueden verificar (un commit, una rama o un PR). Si tu trabajo está solo en tu computadora, el reporte va a tu cuaderno. Y apenas tengas tu primer commit, abrí un PR en borrador: es el lugar natural para mostrar el avance.

**Si usás un agente de IA:** los issues le piden que proponga un plan y que reporte al terminar cada tarea. Ese reporte es para tu conversación con el agente y, al final, para la descripción del PR. No hace falta publicarlo paso a paso en el issue. Vos decidís qué se hace público.

## 2. Las ramas: por qué existe `develop`

```
tu fork / rama de trabajo  ──PR──►  develop  ──(release)──►  main
```

- **`main`**: la versión estable. Es lo que se usa en clase y en producción. Nadie hace PRs directos acá.
- **`develop`**: la rama de integración. **Todos los PRs apuntan a `develop`.** Acá se juntan y se prueban los aportes de todos antes de llegar a `main`.
- **Ramas de trabajo**: las creás vos, siempre desde `develop`.

**¿Por qué?** Si cada aporte entrara directo a `main`, un PR con un test roto o una dependencia sin declarar rompería lo que está funcionando para todos. Con `develop`, los problemas se descubren y se arreglan en un lugar seguro, y recién cuando el conjunto anda bien se pasa a `main`. El docente es quien promueve `develop` a `main`.

## 3. Paso a paso para abrir un PR

1. **Hacé un fork** del repo (botón *Fork* en GitHub) y clonalo.
2. **Agregá el repo original** como remoto y traé `develop`:
   ```bash
   git remote add upstream https://github.com/datamaq-automation/energy-ml
   git fetch upstream
   git checkout -b feat/issue-12-sibo upstream/develop
   ```
3. **Nombrá la rama** así: `feat/issue-N-tema`, `fix/tema` o `docs/tema`.
4. **Trabajá en commits chicos** con mensajes claros (`feat(sibo): registro diario de comidas`).
5. **Verificá antes de subir** (sección 5).
6. **Subí tu rama a tu fork** y abrí el PR en GitHub con **base: `develop`**. Revisá que diga `base: develop` antes de crearlo.
7. **Completá la plantilla del PR** (se carga sola). Incluí `Closes #N` si resolvés un issue completo, o `Refs #N` si es parcial.
8. **Respondé a las revisiones.** Es parte del trabajo: mejorar a partir del feedback.

## 4. Reglas de calidad del repo

Estas reglas las verifican tests automáticos (`tests/test_architecture.py`, `test_clean_design.py`, `test_god_components.py`):

- Todo archivo `.py` empieza con su ruta relativa en un docstring: `"""src/medioambiente/data.py — descripción."""`.
- Los `__init__.py` están vacíos (0 bytes).
- Imports absolutos (`from src...`), sin imports relativos.
- Sin `print()` en `src/`: usá el logger del proyecto.
- Tipos explícitos en parámetros y retornos dentro de `domain` y `application`.
- Sin credenciales ni `os.environ` fuera de `Settings`.
- Sin archivos de menos de 10 líneas de código efectivo, funciones de más de 60 líneas ni archivos de más de 400.
- **Si usás una librería nueva (pandas, matplotlib, etc.), declarala en `requirements.txt` y en `pyproject.toml`.** Que funcione en tu máquina no alcanza.

## 5. Antes de subir tu PR

```bash
./run.sh lint
./run.sh test
python tests/test_architecture.py
```

Si algo falla, el PR no está listo. Si no entendés un error, preguntá en el issue: es una consulta válida y cuenta como aporte.

## 6. Reglas de ML (las mismas de los issues)

- **Cero fuga de datos.** Ninguna variable puede contener información que no existiría al momento de predecir.
- **Series de tiempo: split temporal.** Entrená con el pasado y evaluá con el futuro. Nunca mezcles fechas.
- **Transformaciones después del split.** Imputar y escalar con estadísticas de *train* solamente.
- **Línea base obligatoria.** Todo modelo se compara contra una regla simple. Explicá por qué elegiste esa referencia y si es exigente.
- **Métricas adecuadas.** Con clases desbalanceadas, no alcanza la exactitud. Reportá precisión, recall y F1, o MAE y RMSE según el caso.
- **Semilla fija** (`random_state=42`) donde corresponda.
- **Decí lo que no funciona.** Una conclusión honesta con limitaciones vale más que una prolija y exagerada.

## 7. Datos

- No subas datasets grandes ni con datos personales.
- Documentá la fuente y la **licencia** (por ejemplo, CC0, CC BY 4.0).
- Si el dataset es regenerable, dejá el script para descargarlo en lugar del archivo.

## 8. Uso de IA agéntica

Podés y te conviene usar herramientas como Claude Code. La regla es una sola: **vos sos responsable de lo que subís.**

La clave para dominar la IA agéntica es el criterio humano para distinguir una devolución correcta de una alucinación. En machine learning una alucinación no siempre es una frase falsa: puede ser un componente que parece correcto y no hace lo que su nombre promete, o una conclusión que los números no sostienen. Los tests en verde verifican que el código hace lo que se programó, no que el modelo sepa algo.

Por eso, en la plantilla del PR te pedimos que declares:
- qué herramienta usaste,
- qué decidiste vos,
- qué verificaste o descartaste de lo que te devolvió.

No es un castigo: es lo que más se valora.

## 9. Cómo se revisan y evalúan los aportes

Al revisar un PR miramos:

- **Relevancia:** ¿resuelve un issue o responde una necesidad real del curso?
- **Técnica:** ¿corre, tiene pruebas y respeta las reglas de la sección 4 y 6?
- **Comunicación:** ¿se entiende qué hace, por qué, y qué limitaciones tiene?
- **Revisión:** ¿incorporás el feedback?

Esta sección es la base de la evaluación de la participación. Los PRs, los issues y los comentarios son la forma en que evaluamos.

## 10. ¿Dudas?

Abrí un issue con tu pregunta o comentá en el issue que estás trabajando. Preguntarle a un compañero que ya hizo un aporte también está bien: miralos en los issues y PRs abiertos.
