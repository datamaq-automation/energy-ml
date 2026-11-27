# Cuaderno de trabajo — Identificar equipos a partir del consumo total

En este cuaderno vas a descubrir **qué equipos funcionan en una fábrica** mirando solamente el consumo total de un tablero eléctrico. Vas a usar un algoritmo de **aprendizaje no supervisado**, vas a medir qué tan bien funciona y vas a ver dónde falla.

> **Este cuaderno es parte del curso "Procesamiento de Aprendizaje Automático"** de https://isftn199.com.ar/cursos/procesamiento-aprendizaje-automatico  
> Aplica conceptos de **Unidad 2 (Machine Learning)** y **Unidad 3 (Programación Lógica)**: clustering DBSCAN, evaluación de modelos, y árboles de decisión para clasificación.

> **Cómo trabajar.** Casi todas las actividades siguen tres pasos:
> 1. **Predecí**: antes de correr nada, escribí qué esperás que pase y por qué.
> 2. **Corré**: ejecutá el comando o mirá la página.
> 3. **Explicá**: compará con tu predicción. Si no coincide, ahí está lo interesante: ¿qué no estabas teniendo en cuenta?
>
> Anotá tus respuestas en un archivo propio. No hay respuestas en este cuaderno: se discuten en clase.

**Qué necesitás saber:** usar la terminal, leer un poco de Python y conceptos básicos de estadística (promedio, mediana). Lo demás se explica acá.

---

## 1. El problema

Una fábrica tiene **un medidor por tablero**, no uno por equipo. Ese medidor registra cada 5 minutos la **potencia total** (en kW): la suma de todo lo que está funcionando.

La idea: si un equipo de 90 kW arranca, el consumo total **salta** unos 90 kW de golpe. Si ese salto se repite cientos de veces, probablemente sea siempre el mismo equipo.

```
potencia
 (kW)       +------+         +------+
 350 -      |      |         |      |      <- equipo de ~90 kW encendido
            |      |         |      |
 260 - -----+      +---------+      +----  <- consumo de base (con ruido)
              ^ +90    v -90   ^ +90   v -90
                         tiempo ->
```

Esto se llama **NILM** (*Non-Intrusive Load Monitoring*, monitoreo no intrusivo de cargas).

---

## 2. Puesta en marcha

```bash
git clone https://github.com/datamaq-automation/energy-ml.git
cd energy-ml
./run.sh start
```

Abrí `http://localhost:8000`. No hace falta base de datos ni configurar nada.

Vas a trabajar con tres medidores:

| Medidor | Qué es |
| :--- | :--- |
| `planta_2_a` | Tablero real de una planta papelera (datos anonimizados) |
| `planta_2_b` | Otro tablero de la misma planta |
| `sintetico` | Tablero **simulado**: sabemos exactamente qué equipos tiene. Sirve para medir errores. |

---

## 3. Actividad 1 — Mirar la señal

Elegí `planta_2_a` y presioná **Identificar**. En el paso 1 está el gráfico de la potencia en el tiempo. Después presioná **Ver un día**.

1. **Predecí**: antes de mirar el día, ¿cuántos equipos distintos esperás ver prenderse y apagarse en un día de fábrica?
2. En la vista de un día: ¿cuánto vale aproximadamente el consumo de base? ¿De qué tamaño son los escalones que se repiten?
3. ¿Cada cuánto aparece un escalón? ¿Es regular?
4. ¿Hay algún salto que no se parezca a los demás? Describilo.
5. Volvé al mes completo. ¿Por qué ahí no se distinguen los escalones?

---

## 4. Del salto al evento

Para cada par de mediciones consecutivas se calcula el tamaño del salto:

**|ΔP| = |P(ahora) − P(antes)|**

- Los saltos **chicos** son **ruido**: equipos que varían de a poco, motores que regulan, error de medición.
- Los saltos **grandes** son **eventos**: algo se encendió (↑, salto positivo) o se apagó (↓, salto negativo).

El problema es decidir **dónde termina lo chico y empieza lo grande**: ese número es el **umbral**.

### Ejemplo resuelto: elegir el umbral con el método de Otsu

Tenemos estos 10 saltos (en kW): `2, 3, 1, 4, 2, 88, 91, 3, 90, 2`.

A ojo, hay dos grupos: unos chicos (1 a 4) y unos grandes (88 a 91). El **método de Otsu** encuentra el corte de forma automática:

1. Ordená los saltos: `1, 2, 2, 2, 3, 3, 4, 88, 90, 91`. La media de todos es 28,6.
2. Probá cada corte posible. Para cada uno, separá en grupo chico y grupo grande y calculá la **varianza entre grupos**:

   **varianza entre = peso del chico × peso del grande × (media del chico − media del grande)²**

   (el *peso* es la fracción de saltos que cae en cada grupo)

| Corte entre | Grupo chico | Media chico | Media grande | Peso chico | Varianza entre |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 y 2 | 1 | 1,0 | 31,7 | 0,1 | 0,1 · 0,9 · (1,0 − 31,7)² = **84,6** |
| 2 y 3 | 1, 2, 2, 2 | 1,8 | 46,5 | 0,4 | 0,4 · 0,6 · (1,8 − 46,5)² = **480,6** |
| 3 y 4 | 1 … 3 | 2,2 | 68,2 | 0,6 | 0,6 · 0,4 · (2,2 − 68,2)² = **1048,1** |
| **4 y 88** | **1 … 4** | **2,4** | **89,7** | **0,7** | 0,7 · 0,3 · (2,4 − 89,7)² = **1598,2** ← máximo |
| 88 y 90 | 1 … 88 | 13,1 | 90,5 | 0,8 | 0,8 · 0,2 · (13,1 − 90,5)² = **957,9** |
| 90 y 91 | 1 … 90 | 21,7 | 91,0 | 0,9 | 0,9 · 0,1 · (21,7 − 91,0)² = **432,6** |

3. Quedate con el corte de **mayor varianza entre grupos**: entre 4 y 88. El umbral es el punto medio: **46 kW**.

**¿Por qué funciona?** La varianza entre grupos es grande cuando los dos grupos son **parejos en tamaño** y sus **medias están lejos**. El mejor corte es el que deja dos grupos "compactos y bien separados".

**La medida de confianza, η.** Si dividís la varianza entre grupos por la varianza total de los datos (1599,2), obtenés **η** (eta), entre 0 y 1. Acá da 1598,2 / 1599,2 = **1,00**: separación perfecta. Con datos reales, η menor a 0,8 significa que **no hay dos grupos claros** y el umbral es dudoso.

### Actividad 2 — Calcular a mano

1. Con los saltos `5, 6, 4, 50, 52, 5, 48, 6` repetí el procedimiento. ¿Dónde queda el umbral? ¿Cuánto da η?
2. Ahora con `5, 15, 25, 35, 45, 55`. ¿Cuánto da η? ¿Por qué es más bajo?
3. Verificá tus cuentas leyendo la función `estimar_umbral` en `src/domain/cargas/services.py`. ¿Qué línea calcula la varianza entre grupos?

### Actividad 3 — El histograma

En la página, el paso 2 muestra el **histograma de los saltos**: cuántos saltos hay de cada tamaño.

1. Mirá `planta_2_a`. ¿Ves dos "montañas"? ¿Dónde está el valle entre ellas? ¿Dónde quedó la línea del umbral?
2. Mirá `planta_2_b`. ¿Qué cambia? ¿Qué dice el aviso?
3. **Predecí**: si en `planta_2_b` fijás el umbral en 60 kW, ¿la carga encontrada va a ser más grande o más chica que con el automático? ¿Por qué?
4. **Corré**: `./run.sh train planta_2_b` y después `./run.sh train planta_2_b --umbral 60`.
5. **Explicá**.

---

## 5. Agrupar eventos: DBSCAN

Ya tenemos eventos. Ahora hay que **agruparlos**: si hay cientos de saltos de ~90 kW, probablemente sean siempre el mismo equipo.

**DBSCAN** es un algoritmo de agrupamiento (*clustering*) que funciona así:
- Dos eventos son **vecinos** si sus tamaños se diferencian en menos que un **radio**.
- Un grupo se forma cuando hay **suficientes vecinos juntos** (un **mínimo de eventos**).
- Los eventos que no tienen suficientes vecinos quedan **sin grupo** (ruido). DBSCAN no los fuerza a un grupo.

Nadie le dice al algoritmo cuántos equipos hay ni de qué tamaño son: los **descubre**. Por eso es **aprendizaje no supervisado**.

### Ejemplo resuelto: el radio con la regla de Freedman–Diaconis

¿Qué tan cerca tienen que estar dos saltos para ser "el mismo equipo"? Tomemos 12 eventos de un mismo equipo: `88, 91, 90, 89, 92, 87, 90, 91, 89, 93, 88, 90`.

1. Ordenados: `87, 88, 88, 89, 89, 90, 90, 90, 91, 91, 92, 93`.
2. **Rango intercuartil (IQR)**: la distancia entre el valor que deja un 25 % por debajo (88) y el que deja un 75 % por debajo (91). IQR = 91 − 88 = **3 kW**.
3. **Regla de Freedman–Diaconis**: radio = 2 × IQR × n^(−1/3) = 2 × 3 × 12^(−1/3) = 2 × 3 × 0,437 = **2,6 kW**.

**Intuición**: si los saltos están muy dispersos (IQR grande), el radio crece; si hay muchos datos (n grande), el radio se achica porque hay más evidencia.

El sistema además pone un **piso**: el radio nunca es menor que **2 × el ruido** de la señal, porque el encendido y el apagado de un mismo equipo nunca miden exactamente lo mismo.

### Actividad 4 — Radio y mínimo

1. Corré `./run.sh train planta_2_a` y buscá en la salida las líneas `Radio automático` y `Mínimo automático`. ¿Cuánto valen? ¿Cuál de los dos términos ganó en el radio?
2. **Predecí**: si achicás mucho el radio (`--radio 2`), ¿qué va a pasar con los eventos sin grupo? ¿Y con la carga de ~91 kW?
3. **Corré** y **explicá**.
4. El mínimo automático es "un evento por día analizado". Corré con `--desde 2026-09-15 --hasta 2026-09-22`. ¿Cuánto vale ahora el mínimo? ¿Por qué tiene sentido que cambie?

---

## 6. Validar sin respuestas correctas

En `planta_2_a` y `planta_2_b` **nadie sabe qué equipos hay**: no hay etiquetas. ¿Cómo sabemos si el resultado es bueno? Con **sentido físico**:

- **Un equipo que se prende y se apaga** tiene una cantidad **parecida** de encendidos y apagados. Si una "carga" tiene 2 encendidos y 18 apagados, es sospechosa.
- **Una carga real es estable**: debería aparecer parecida si mirás una semana o el mes.

El sistema usa dos **reglas de decisión** que no se calculan con los datos, sino que **se eligen**:

| Regla | Valor | Qué decide |
| :--- | :--- | :--- |
| Separación mínima | 0,8 | Cuánta evidencia de "dos montañas" pedir antes de confiar en el umbral |
| Balance mínimo | 0,5 | Qué tan parejos tienen que ser encendidos y apagados para ser un equipo ON/OFF |

### Actividad 5 — Reglas de decisión

1. Corré `./run.sh train planta_2_a --min-eventos 10`. Aparece una carga de ~222 kW. ¿Cuántos encendidos y apagados tiene? ¿Qué dice el sistema de ella?
2. Proponé **dos explicaciones físicas** de por qué una carga tendría muchos más apagados que encendidos. ¿Cómo las verificarías mirando el CSV?
3. **Predecí**: con `--balance-minimo 0.95`, ¿la carga de ~91 kW sigue siendo "confiable"? Calculá su proporción (ciclos / el mayor de encendidos y apagados) antes de correr.
4. ¿Qué valor de balance mínimo elegirías si analizaras **un solo día**? Justificá.

---

## 7. Medir el error con el tablero simulado

En el medidor `sintetico` **sí sabemos la verdad**: lo generó un simulador con **tres equipos**:

| Equipo | Potencia | Veces por día (medidas) | Duración |
| :--- | :--- | :--- | :--- |
| A | 90 kW | ~18 | ~25 min |
| B | 40 kW | ~5 | ~60 min |
| C | 15 kW | ~28 | ~10 min |

más un consumo de base que sube y baja durante el día, y ruido de 3 kW. Los eventos reales están en `data/verdad/sintetico.csv`.

Con la verdad se pueden calcular dos medidas:
- **Sensibilidad** (por equipo): de los eventos que **realmente ocurrieron**, ¿qué fracción detectó el algoritmo y asignó al equipo correcto?
- **Precisión** (global): de los eventos que el algoritmo **detectó**, ¿qué fracción corresponde a algo que realmente pasó?

### Actividad 6 — ¿Cuántos equipos encuentra?

1. **Predecí**: con el umbral automático, ¿cuáles de los tres equipos va a encontrar? Pista: mirá de qué tamaño es cada uno comparado con el ruido y pensá dónde va a caer el umbral.
2. **Corré**: `./run.sh evaluate`. Completá:

| | Equipo A (90) | Equipo B (40) | Equipo C (15) |
| :--- | :--- | :--- | :--- |
| Umbral automático: sensibilidad | | | |
| ¿Se encontró? ¿Con qué potencia? | | | |

3. ¿Apareció alguna **carga inventada**? ¿De dónde puede salir? (Pista: ¿qué pasa si dos equipos cambian de estado en los mismos 5 minutos?)

### Actividad 7 — Buscar un umbral que encuentre todo

1. **Predecí** qué va a pasar con `--umbral 30` y con `--umbral 10`.
2. **Corré**: `./run.sh evaluate --umbral 30` y `./run.sh evaluate --umbral 10`. Completá la tabla para cada umbral.
3. Con `--umbral 30`, el algoritmo **detecta** la mayoría de los eventos del equipo B (mirá la columna "detectados"), pero no lo encuentra. ¿Dónde fueron a parar esos eventos? Mirá la potencia que reporta para el equipo A.
4. Con `--umbral 10`, ¿qué le pasó al equipo de 90 kW?
5. ¿Existe un umbral que, **solo**, encuentre los tres equipos?

### Actividad 8 — Ajustar dos perillas a la vez

El problema de la actividad 7 no es solo el umbral: DBSCAN une grupos cuando hay eventos "puente" entre ellos (por ejemplo, si el equipo B y el C cambian en los mismos 5 minutos, aparece un salto de 55 kW, a mitad de camino entre 40 y 90).

1. **Predecí**: si achicás el radio, ¿los grupos se van a separar o se van a unir más?
2. **Corré** `./run.sh evaluate --umbral 30 --radio 5`. ¿Apareció el equipo B?
3. Buscá una combinación de `--umbral` y `--radio` que encuentre **los tres** equipos. Anotá todas las que probaste en una tabla con la sensibilidad de cada equipo y la precisión.
4. **Pensá**: para encontrar esa combinación usaste `./run.sh evaluate`, que compara con la **verdad**. En `planta_2_a` no hay verdad. ¿Podrías haber hecho lo mismo ahí? ¿Qué te haría falta?
5. **Conclusión**: escribí en tres líneas cuál es el límite de este enfoque.

### Actividad 9 — Tu propio tablero

1. Generá otro tablero con otra semilla: `./run.sh simulate --nombre prueba --semilla 7` y evaluálo con `./run.sh evaluate prueba`. ¿Los resultados son parecidos?
2. Generá uno con más ruido: `./run.sh simulate --nombre ruidoso --ruido 8`. **Predecí** qué equipos se van a perder. Evaluá.
3. Abrí `src/infrastructure/cli/simular_tablero.py` y cambiá la lista `CARGAS` para inventar tu propio tablero. ¿Podés diseñar uno donde el algoritmo encuentre todo? ¿Y uno donde falle siempre?

---

## 8. Cómo está construido el sistema

El código sigue **Clean Architecture**: las reglas del problema (el *dominio*) no saben nada de páginas web, archivos ni librerías de ML.

```
+------------------------ infraestructura -------------------------+
|  páginas y API     consola (train, simulate, evaluate)           |
|  archivos CSV      DBSCAN (scikit-learn)      configuración      |
|  +----------------------- aplicación ------------------------+   |
|  |  casos de uso: identificar cargas, evaluar                 |   |
|  |  +-------------------- dominio ---------------------+     |   |
|  |  |  mediciones, eventos, cargas                     |     |   |
|  |  |  reglas: saltos, Otsu, radio, resumir, evaluar   |     |   |
|  |  |  puertos: lo que el dominio necesita de afuera   |     |   |
|  |  +--------------------------------------------------+     |   |
|  +------------------------------------------------------------+   |
+-------------------------------------------------------------------+
```

### Recorrido de lectura del código

Leé en este orden. En cada archivo, buscá lo que dice la columna de la derecha.

| # | Archivo | Qué buscar |
| :--- | :--- | :--- |
| 1 | `src/domain/cargas/entities.py` | Las "cosas" del problema: `Medicion`, `EventoCarga`, `Carga`. ¿Qué datos tiene cada una? |
| 2 | `src/domain/cargas/services.py` | Las reglas: `detectar_eventos`, `estimar_umbral`, `estimar_radio`. Compará con los ejemplos resueltos. |
| 3 | `src/domain/cargas/repositories.py` | Los **puertos**: qué necesita el dominio de afuera, sin decir cómo. |
| 4 | `src/application/cargas/use_cases/identificar_cargas.py` | El método `execute`: se lee como el resumen del algoritmo en 4 pasos. |
| 5 | `src/infrastructure/csv/medicion_repository.py` | Un **adaptador**: cómo se cumple el puerto `MedicionRepository` leyendo CSV. |
| 6 | `src/infrastructure/sklearn/dbscan_agrupador.py` | Otro adaptador: DBSCAN detrás del puerto `AgrupadorEventos`. |
| 7 | `src/infrastructure/cli/entrenar_cargas.py` | Cómo la consola **arma** las piezas y se las pasa al caso de uso. |
| 8 | `tests/unit/cargas/test_services.py` | Cómo se prueban las reglas sin servidor ni archivos. |

### Actividad 10 — Arquitectura

1. ¿Por qué `services.py` no importa `sklearn` ni `csv`? ¿Qué ganamos con eso?
2. Implementá `JsonCargaRepository` (puerto `CargaRepository`) que guarde los resultados en JSON, y usalo en `entrenar_cargas.py`. ¿Qué archivos tuviste que tocar? ¿Cambió algo en `src/domain/`?
3. Escribí una función de 80 líneas en el caso de uso y corré `./run.sh test`. ¿Qué test falla? ¿Por qué ese test es útil en un equipo de trabajo?

---

## 9. Cierre — Hacia el aprendizaje supervisado

En las actividades 7 y 8 viste que **ningún umbral solo** encuentra los tres equipos, y que la combinación que sí funciona la encontraste **gracias a la verdad**. El algoritmo no supervisado solo mira el **tamaño** de los saltos, y para ajustarlo hace falta saber la respuesta correcta.

1. En `data/verdad/sintetico.csv` cada evento tiene su equipo. ¿En qué se diferencia eso de lo que tenía DBSCAN?
2. Si tuvieras esas etiquetas para una fábrica real, ¿quién las tendría que poner y cómo?
3. Además del tamaño del salto, ¿qué otra información podría ayudar a reconocer cada equipo? (Pensá en la hora del día, cuánto dura encendido, si sube de golpe o de a poco…)
4. ¿Qué tipo de modelo usarías para aprender "este salto es del equipo B"?

Eso es lo que viene: **aprendizaje supervisado**.

---

## Glosario

| Término | Significado |
| :--- | :--- |
| **Potencia (kW)** | Energía por unidad de tiempo que consume un equipo |
| **\|ΔP\|** | Tamaño del salto de potencia entre dos mediciones seguidas |
| **Evento** | Salto mayor al umbral: algo se encendió (↑) o se apagó (↓) |
| **Ruido** | Saltos chicos que no son eventos; también, eventos que DBSCAN no agrupa |
| **Umbral** | Tamaño mínimo de salto para considerarlo evento |
| **Método de Otsu** | Elige el umbral que mejor separa dos grupos |
| **η** | Qué tan bien separados quedan los dos grupos (0 a 1) |
| **DBSCAN** | Algoritmo que agrupa puntos cercanos y deja aislados los solitarios |
| **Radio** | Distancia máxima entre dos eventos para ser vecinos |
| **IQR** | Rango intercuartil: distancia entre el 25 % y el 75 % de los datos |
| **Sensibilidad** | Fracción de los eventos reales que se detectaron bien |
| **Precisión** | Fracción de los eventos detectados que eran reales |
| **No supervisado** | Encontrar estructura en datos sin etiquetas |
| **Supervisado** | Aprender a partir de ejemplos etiquetados con la respuesta correcta |
| **Puerto / adaptador** | Lo que el dominio necesita / cómo se cumple en la práctica |
