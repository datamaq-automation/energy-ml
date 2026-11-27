# Guía docente — energy-ml

> **Material para docentes, con respuestas.** No se publica en la app: los alumnos trabajan con el [cuaderno del alumno](cuaderno-alumno.md), que se sirve en `/guia` y no tiene respuestas. Las respuestas de cada actividad del cuaderno están en la [sección 17](#17-respuestas-del-cuaderno-del-alumno). Como el repositorio es público, un alumno que lo clone puede leer este archivo: si eso importa, conviene guardar una copia fuera del repo.

**Referencia pedagógica:** este proyecto es un caso de estudio del curso **"Procesamiento de Aprendizaje Automático"** (https://isftn199.com.ar/cursos/procesamiento-aprendizaje-automatico). Implementa conceptos de **Unidad 2 (Clasificación y evaluación)** y **Unidad 3 (Árboles de decisión, algoritmos de inducción)**.

Esta guía recorre **todo el repositorio** con mirada de aula: qué hace el sistema, cómo lo hace, por qué quedó así y qué se puede aprender de cada parte. Todos los números salen de correr el sistema sobre los datos de `data/input/`.

> **Cómo leerla.** Si es tu primera vez, seguí el orden. Si vas a dar una clase puntual, usá la [secuencia sugerida](#15-secuencia-sugerida-de-clases) y los [ejercicios](#14-ejercicios). Para ver el código en cualquier punto del historial: `git log --oneline` y `git checkout <hash>` (volvés con `git checkout main`).
>
> Complementa a otras dos guías del repo: la [especificación técnica](srs-spec-backend-fastapi.md) (qué debe cumplir el sistema) y la [guía de andamiaje](guia-andamiaje-proyectos.md) (cómo formular un proyecto de software con preguntas metacognitivas).

---

## 1. Qué vas a aprender

| Eje | Contenidos |
| :--- | :--- |
| **Datos y energía** | Potencia activa, series temporales, ruido vs. eventos, ciclos ON/OFF |
| **Machine learning** | Aprendizaje no supervisado, clustering con DBSCAN, elección automática de parámetros (Otsu, Freedman–Diaconis), validar sin etiquetas |
| **Ingeniería de software** | Clean Architecture, puertos y adaptadores, inyección de dependencias, configuración vs. secretos, logging, tests como guardianes del diseño |
| **Práctica profesional** | Commits atómicos, datos anonimizados y versionados, decisiones justificadas con datos, decir "no sé" cuando el modelo duda |

---

## 2. El problema: NILM

Una planta tiene **un medidor por tablero**, no uno por equipo. **NILM** (*Non-Intrusive Load Monitoring*, monitoreo no intrusivo de cargas) intenta deducir qué equipos se encienden y se apagan mirando **solo el consumo total**.

La intuición: si un equipo de 90 kW arranca, el consumo total **salta** unos 90 kW. Si ese salto se repite cientos de veces, probablemente sea siempre el mismo equipo.

```
potencia
 (kW)       +------+         +------+
 300 -      |      |         |      |      ← equipo de ~90 kW encendido
            |      |         |      |
 210 - -----+      +---------+      +----  ← consumo de base (con ruido)
              ↑ +90    ↓ -90   ↑ +90   ↓ -90
                         tiempo →
```

---

## 3. Puesta en marcha

```bash
git clone https://github.com/datamaq-automation/energy-ml.git && cd energy-ml
./run.sh start          # crea el entorno .venv si falta y levanta http://localhost:8000
```

| Dirección | Qué hay |
| :--- | :--- |
| `http://localhost:8000/` | La herramienta: elegís medidor y fechas, y muestra los 4 pasos del algoritmo |
| `http://localhost:8000/guia` | Esta guía |
| `http://localhost:8000/api/v1/docs` | La API documentada (Swagger), se puede probar desde ahí |

No hace falta base de datos, cuentas ni `.env`: los datos están en el repo.

### Todos los comandos (`run.sh`)

| Comando | Qué hace |
| :--- | :--- |
| `./run.sh start` | Servidor web (API + páginas) |
| `./run.sh dev` | Igual, pero se reinicia solo al editar el código |
| `./run.sh train [medidores] [--desde F] [--hasta F] [parámetros]` | Identifica cargas por consola y guarda los resultados en `data/output/`. Los parámetros NILM se pueden pasar como argumentos (ver §10); `./run.sh train --help` los lista |
| `./run.sh simulate [--nombre N] [--dias D] [--ruido KW] [--semilla S]` | Genera un tablero simulado con equipos conocidos y su verdad (§4) |
| `./run.sh evaluate [medidor] [parámetros]` | Compara lo identificado con la verdad: sensibilidad por equipo, precisión, cargas inventadas |
| `./run.sh test` | Toda la suite de tests |
| `./run.sh gauntlet` | Solo las reglas de arquitectura |
| `./run.sh audit` | Busca código muerto y "componentes Dios" |
| `./run.sh lint` / `format` | Revisa / corrige estilo con ruff |
| `./run.sh install` | Reinstala dependencias |

`run.sh` no tiene lógica propia: **solo lanza herramientas** (uvicorn, pytest, ruff, Python). La lógica está en `src/`, donde se puede testear.

---

## 4. Los datos

| Archivo | Qué es |
| :--- | :--- |
| `data/input/planta_2_a.csv` | Tablero "arriba" de una planta papelera (fuerza motriz, preparación de pasta) |
| `data/input/planta_2_b.csv` | Tablero "abajo" de la misma planta (máquina papelera continua) |
| `data/input/sintetico.csv` | Tablero **simulado** con tres equipos conocidos (90, 40 y 15 kW). Su verdad está en `data/verdad/sintetico.csv` |

```
instante,potencia_kw
2026-09-11T19:20:01,2.332
2026-09-11T19:25:01,5.171
```

- **Potencia activa total** del tablero, en kW, una medición cada ~5 minutos.
- Del 11-09 al 03-10-2026: ~6150 filas y 21 días por archivo.

### De dónde salen (y por qué así)

1. Los medidores envían telemetría a una base MySQL en un servidor.
2. Un script **no versionado** (`tmp/`, ignorado por git) la exportó una vez, filtrando solo datos confiables y pasando de W a kW.
3. Los nombres reales se reemplazaron por `planta_2_a` / `planta_2_b`: los datos son **anonimizados**.
4. Los CSV se versionan para que cualquiera pueda clonar y trabajar **sin acceso a la base**.

`data/output/` también existe en el repo pero está **vacía** (`.gitignore`): ahí cada uno genera sus propios resultados con `./run.sh train`.

> **Para discutir:** ¿qué ganamos y qué perdemos versionando datos? ¿Por qué el script de extracción no está en el repo?

---

## 5. El algoritmo, paso a paso

Es lo mismo que muestran la página web y los logs (`Paso 1/4` … `Paso 4/4`).

### Paso 1 — Leer
Se leen las mediciones del medidor en el rango pedido. La **potencia media** da escala: 91 kW en un tablero de 216 kW de media es casi la mitad del consumo.

### Paso 2 — Detectar eventos (con umbral automático)
Para cada par de mediciones consecutivas se calcula el salto **|ΔP| = |P(t) − P(t−1)|**. Los saltos chicos son **ruido** (equipos que varían de a poco); los grandes son **eventos** (algo se encendió ↑ o se apagó ↓). El **umbral** los separa. Ver §6.

### Paso 3 — Agrupar con DBSCAN (con radio automático)
**DBSCAN** junta eventos de tamaño parecido: si hay cientos de saltos de ~90 kW, probablemente sean el mismo equipo. Dos parámetros:
- **radio** (`eps`): qué tan parecidos deben ser dos saltos para estar en el mismo grupo. Automático, ver §7.
- **mínimo de eventos** (`min_samples`): menos que eso no se considera una carga. También automático, ver §7.

Los eventos que no se parecen a ningún grupo quedan **sin grupo** (etiqueta −1) en vez de forzarlos.

### Paso 4 — Resumir y validar
Cada grupo es una **carga candidata**: potencia típica, encendidos, apagados, ciclos (= el menor de los dos) y ciclos por día. Si encendidos y apagados no son parecidos, la carga se marca **dudosa** (§8).

### ¿Esto es machine learning?

| Paso | ¿Aprende de los datos? |
| :--- | :--- |
| Detectar eventos | El **umbral** sí (Otsu lo estima de los datos). La detección en sí es una regla. |
| Agrupar | **Sí: aprendizaje no supervisado.** Nadie le dice qué cargas existen. El **radio** también se estima de los datos. |
| Resumir | No: estadística descriptiva + una regla física. |

Consecuencias para charlar:
- **No hay "respuesta correcta"**: sin etiquetas no se puede medir un error. Se valida con sentido físico.
- **`./run.sh train` no guarda un modelo**: DBSCAN agrupa desde cero cada vez. `data/output/` guarda el resultado del agrupamiento.
- **Camino natural del curso**: no supervisado (descubrir cargas) → etiquetado por alguien de planta ("esto es el compresor 2") → supervisado (un clasificador que reconozca cada equipo; ahí sí hay un modelo para guardar).

---

## 6. El umbral: de un número mágico a una estimación

Al principio el umbral era **60 kW fijo**. ¿Por qué 60 y no 40 u 80? El **histograma de |ΔP|** (paso 2 de la página) lo responde:

```
planta_2_a  (dos montañas)                planta_2_b  (sin valle)
 ruido ████████████                        ruido ██████████
       ███                                       ████████
       ▌         valle                           ██████
       ▏    ← 30 a 70 kW →    eventos            ████
                         ███████                 ███ ███ ███ ██ ██ ...
```

- **`planta_2_a`**: dos montañas con un valle vacío entre 30 y 70 kW. Cualquier umbral ahí da lo mismo; por eso 60 "andaba".
- **`planta_2_b`**: el ruido baja de a poco y se mezcla con los eventos. No hay valle.

### Tres ideas que se probaron

| Método | Resultado |
| :--- | :--- |
| Mediana + k·MAD del ruido | Ningún *k* sirve para los dos tableros: con k = 5, en `planta_2_b` el umbral sube a 103 kW y se pierde la carga de 88 kW. Cambia un número arbitrario por otro. |
| **Método de Otsu** (elegido) | Prueba todos los cortes y elige el que **maximiza la varianza entre** los dos grupos. Además mide qué tan buena es la separación. |
| Sin umbral, DBSCAN sobre todo | Más limpio en teoría, pero DBSCAN pasaría a depender todavía más de su radio. |

### La medida de confianza: η

**η** = varianza entre grupos / varianza total, entre 0 y 1. Mide qué tan claras son las dos montañas:

| Caso | Umbral | η | Lectura |
| :--- | :--- | :--- | :--- |
| `planta_2_a`, mes | 51,3 kW | **0,87** | Valle claro |
| `planta_2_a`, una semana | 50,8 kW | **0,89** | Valle claro, umbral estable |
| `planta_2_b`, mes | 45,6 kW | **0,71** | Sin valle → `WARNING` |
| Una sola montaña (simulado) | — | ~0,68 | Nivel base: no hay nada que separar |

Por eso el corte de confianza es `NILM_SEPARACION_MINIMA = 0.8`.

#### Cómo se eligió 0,8 (y cómo elegir otro valor)

`NILM_SEPARACION_MINIMA` **no se estima con los datos**: es una **regla de decisión**, la respuesta a "¿cuánta evidencia de dos montañas pido antes de confiar en el umbral?". Para elegirla con criterio hay que saber qué valores de η da una señal **sin** cargas (el "azar") y cuáles **con** cargas.

**1. Qué da el azar.** Se simularon señales con una sola montaña de ruido (200 repeticiones por caso):

| Forma del ruido | n = 300 saltos (≈1 día) | n = 6000 (≈3 semanas) |
| :--- | :--- | :--- |
| Half-normal | mediana 0,68 · máx. 0,73 | mediana 0,68 · máx. 0,69 |
| Exponencial | mediana 0,65 · máx. 0,73 | mediana 0,65 · máx. 0,67 |
| Lognormal | mediana 0,62 · máx. 0,70 | mediana 0,60 · máx. 0,62 |
| Uniforme (el peor caso) | mediana 0,75 · máx. **0,79** | mediana 0,75 · máx. 0,76 |

**Ninguna señal sin cargas llegó a 0,8.** Ese es el criterio: el corte va **apenas por encima del máximo que produce el azar**, para que un "confiable" nunca sea casualidad.

**2. Qué da una carga real.** Ruido de σ = 5 kW más una carga de C kW en el 12 % de los saltos:

| Carga (en múltiplos del ruido) | 3σ | 4σ | 6σ | 9σ | 18σ |
| :--- | :--- | :--- | :--- | :--- | :--- |
| η | 0,71 | 0,78 | **0,89** | 0,95 | 0,99 |

Con 0,8, una carga se distingue con confianza cuando mide **unas 5 veces el ruido** o más.

**3. Una limitación: las cargas poco frecuentes.** Con una carga de 6σ, η cambia según qué proporción de los saltos son eventos:

| Eventos / saltos | 1 % | 3 % | 12 % | 30 % |
| :--- | :--- | :--- | :--- | :--- |
| η | 0,50 | 0,69 | 0,89 | 0,94 |

Una carga clara pero rara (menos del 3 % de los saltos) da η bajo y el sistema **avisa de más**. Es el error menos grave: el contrario (confiar en un umbral que es casualidad) no puede ocurrir con 0,8.

**4. Qué dan los datos reales.** Es estable al cambiar el rango:

| | Semana 1 | Semana 2 | Semana 3 | Días sueltos |
| :--- | :--- | :--- | :--- | :--- |
| `planta_2_a` | 0,91 | 0,85 | 0,86 | 0,77 a 0,96 |
| `planta_2_b` | 0,72 | 0,71 | 0,69 | 0,65 a 0,77 |

`planta_2_b` queda **siempre** en la zona del azar: no es mala suerte de un período, es la forma de esa señal.

**Cómo elegir otro valor:**
- **Más alto (0,85–0,9)** si un umbral equivocado es caro (por ejemplo, si el resultado alimenta una decisión de mantenimiento). Vas a ver más avisos, también en cargas reales poco frecuentes.
- **Más bajo (0,75)** si preferís menos avisos y aceptás que, con ruido de forma uniforme, alguno sea casualidad. Nunca por debajo de ~0,7: ahí cae una sola montaña típica.
- **Para un medidor nuevo**: mirá su η en varias semanas. Si es estable y alto, 0,8 sobra; si oscila alrededor del corte, el problema es la señal, no el número.

**La lección central**: el mismo algoritmo funciona perfecto en un tablero y duda en el otro, **y lo dice**. En `planta_2_b` el umbral deja entrar ruido que se encadena con la carga real: aparece ~75 kW en vez de los ~88 kW que da un umbral de 60 kW. El sistema no puede arreglarlo solo, pero avisa en el log, en el paso 2 de la página y en la tarjeta de la carga.

---

## 7. El radio de DBSCAN: también automático

El radio (`eps`) era **8 kW fijo**, sin relación con la escala de cada medidor. Ahora es **el mayor de dos valores**:

1. **Regla de Freedman–Diaconis**: `2 · IQR · n^(−1/3)`, el ancho "natural" para agrupar valores en una dimensión. Crece si los saltos están dispersos (IQR = rango intercuartil) y se achica con más datos (*n*).
2. **Piso físico: 2 × ruido**. El ruido es la mediana de los saltos que *no* llegan al umbral. Cada evento trae el ruido de dos mediciones, así que el encendido (89 kW) y el apagado (91 kW) de un mismo equipo pueden diferir hasta en 2 × ruido.

| Caso | Ruido | Radio | Resultado |
| :--- | :--- | :--- | :--- |
| `planta_2_a`, mes | 5,4 kW | 10,8 kW | ~91 kW (426 ↑ / 388 ↓) |
| `planta_2_a`, semana | 5,0 kW | 9,9 kW | ~92 kW (135 ↑ / 126 ↓) |
| `planta_2_b`, mes | 14,5 kW | 29,0 kW | ~75 kW (sin cambios: su problema es el umbral) |

### Cómo se llegó a esto (vale contarlo en clase)

| Intento | Problema |
| :--- | :--- |
| Codo de la curva de *k*-distancias (el método "de libro") | En una dimensión con cientos de eventos, los vecinos siempre están cerca: dio 1–2 kW y partió la carga de 91 kW. |
| Solo Freedman–Diaconis | Funciona con datos reales, pero con datos sintéticos limpios (saltos de 89 y 91 exactos) separó encendidos de apagados en dos "cargas". |
| Freedman–Diaconis con piso = ruido | Todavía separaba 89 de 91 con ruido de 1 kW. |
| **Freedman–Diaconis con piso = 2 × ruido** | Elegido: estable en mes y semana, y con sentido físico. |

> Los tests encontraron el problema que los datos reales no mostraban. Un buen dato sintético es un experimento controlado.

### El mínimo de eventos: uno por día

DBSCAN también necesita saber **cuántos eventos** hacen falta para que un grupo sea una carga. Era **10 fijo**, pero 10 eventos no pesan igual en una semana (una carga frecuente) que en tres meses (algo que casi no pasa). Ahora es **uno por día analizado, en promedio, y nunca menos de 3**:

| Rango | Mínimo | Efecto |
| :--- | :--- | :--- |
| Mes (21 días) | 21 | La "carga" de ~222 kW (20 eventos en 21 días) ya no pasa; la de ~91 kW sí |
| Semana (7 días) | 7 | ~92 kW, igual que con 10 |
| Un día | 3 | Se sigue detectando la carga de ~92 kW con pocos datos |

### Cómo se eligió el balance mínimo 0,5 (y cómo elegir otro valor)

`NILM_BALANCE_MINIMO` es la segunda **regla de decisión**: ¿qué tan parejos tienen que ser encendidos y apagados para que un grupo sea "un equipo que se prende y se apaga"? Se mide como **ciclos / el mayor de los dos** (1 = perfectamente parejo, 0 = solo encendidos o solo apagados).

**1. Qué dan las cargas reales y las dudosas.** Todas las cargas encontradas, analizando el mes, cada semana y cada día:

| | Proporción |
| :--- | :--- |
| Cargas ON/OFF (~75 a ~93 kW) | **0,59 a 0,98** (casi todas por encima de 0,76) |
| "Cargas" dudosas (~139, ~212, ~222 kW) | **0,00 a 0,12** |

Hay un **hueco** entre 0,12 y 0,59. El criterio es poner el corte **en el medio del hueco**: 0,5 separa los dos grupos con margen hacia ambos lados.

**2. Por qué una carga real no da exactamente 1.** Con una medición cada 5 minutos, algunos eventos no se detectan (un apagado lento puede quedar repartido en dos saltos chicos). En `planta_2_a` la carga principal tiene 426 encendidos y 388 apagados: se pierde ~9 % de los eventos de un tipo. Simulando una carga ON/OFF perfecta a la que se le pierde cada evento con probabilidad *p*:

| Ciclos en el rango | p = 10 % | p = 20 % | p = 30 % |
| :--- | :--- | :--- | :--- |
| 3 | 0,50 | 0,33 | 0,00 |
| 7 | 0,71 | 0,57 | 0,43 |
| 20 | 0,80 | 0,72 | 0,65 |

*(percentil 5 de la proporción: el 95 % de las veces da más que eso)*

Con **20 ciclos o más**, una carga real queda por encima de 0,5 aunque se pierda el 30 % de los eventos. Con **pocos ciclos** (un día, una carga poco frecuente), una carga real **puede** caer por debajo de 0,5 por azar y aparecer como dudosa.

**Cómo elegir otro valor:**
- **Más alto (0,7)** con rangos largos y cargas frecuentes, si querés ser estricto: las cargas reales de este repo siguen pasando.
- **Más bajo (0,3)** si analizás rangos muy cortos y te molestan los falsos "dudosa"; las dudosas de este repo (≤ 0,12) siguen marcadas.
- **Regla práctica**: buscá el hueco entre las proporciones de las cargas que sabés reales y las que sabés dudosas, y poné el corte en el medio.

### Lo que se estima y lo que se decide

Con esto, **los tres parámetros que se estiman de los datos** son el umbral, el radio y el mínimo. Los dos que quedan fijos (`NILM_SEPARACION_MINIMA` y `NILM_BALANCE_MINIMO`) no son parámetros a estimar sino **reglas de decisión**: cuánta confianza exigir y qué se considera un equipo ON/OFF. Por eso son explícitos y están documentados.

---

## 8. Hallazgos en los datos

- **Carga ON/OFF de ~91 kW en `planta_2_a`**: unos 430 encendidos y 390 apagados en 21 días, **≈18 ciclos por día**. Estable al cambiar el rango. Es el hallazgo más sólido.
- **Carga de ~88 kW en `planta_2_b`** con umbral de 60 kW; ~75 kW con el automático (dudoso, §6).
- **"Carga" de ~222 kW con 2 encendidos y 18 apagados** en `planta_2_a`: con el mínimo automático (21) no llega a ser carga; aparece si lo fijás en 10 (`NILM_MIN_EVENTOS=10`). Un equipo real se enciende y apaga parecido: la regla `Carga.es_on_off` (`NILM_BALANCE_MINIMO = 0.5`: uno puede ser a lo sumo el doble del otro) la marca **dudosa**. Puede ser un arranque escalonado, una parada de planta o varios equipos apagándose juntos.
- **Eventos sin grupo**: 37 en `planta_2_a` (incluye los de ~222 kW). DBSCAN prefiere no forzarlos.
- **Más encendidos que apagados** en casi todas las cargas (426 contra 388). Una hipótesis para verificar: con una medición cada 5 minutos, un apagado puede quedar "repartido" en dos saltos chicos que no superan el umbral.

---

## 9. Las tres formas de usarlo

Las tres corren **el mismo caso de uso** sobre los mismos datos: son *mecanismos de entrega* distintos.

### Página web (`/`)
Muestra los 4 pasos con números grandes y una frase cada uno; el detalle está plegado en "¿Qué significa esto?". El histograma usa **escala de raíz cuadrada** para que los eventos (cientos) no queden invisibles al lado del ruido (miles). Las cargas se leen en lenguaje natural: *"Se encendió 429 veces y se apagó 391: unas 18 veces por día"*.

### API (`GET /api/v1/identify-loads?medidor=planta_2_a&desde=2026-09-12&hasta=2026-10-03`)

| Campo | Qué es |
| :--- | :--- |
| `mediciones`, `dias`, `potencia_media_kw` | Paso 1 |
| `umbral` | `{kw, automatico, separacion (η), confiable}` — paso 2 |
| `histograma` | 30 barras `{desde_kw, hasta_kw, cantidad}` de \|ΔP\| (de 0 al percentil 99; la última junta el resto) |
| `eventos`, `encendidos`, `apagados`, `eventos_sin_grupo` | Paso 3 |
| `agrupamiento` | `{radio_kw, radio_automatico, min_eventos, min_eventos_automatico}` — paso 3 |
| `serie` | `[{instante, potencia_kw}]` — la señal, para el gráfico del paso 1 |
| `detalle_eventos` | `[{instante, delta_kw, carga_kw}]` — cada evento con la carga a la que se asignó (`null` si quedó sin grupo) |
| `cargas` | Paso 4: `{potencia_tipica_kw, encendidos, apagados, ciclos, ciclos_por_dia, on_off}` |

Un medidor inexistente responde **404** (y la API nunca lee archivos fuera de `data/input/`: pedir `../.env` también da 404).

### Consola (`./run.sh train`)
Procesa todos los medidores (o los que indiques) y escribe `data/output/cargas_<medidor>.csv`. Es la que conviene para experimentar cambiando parámetros.

### Los logs cuentan el proceso
Solo tres niveles, todos con el formato de uvicorn:

```
INFO:     Umbral automático: 51.3 kW (Otsu, separación ruido/eventos η=0.87)
INFO:     Radio automático: 10.76 kW (mayor entre Freedman–Diaconis y 2 × ruido de la señal, ruido = 5.4 kW)
INFO:     Mínimo automático: 21 eventos por carga (uno por día analizado, al menos 3)
WARNING:  No hay un valle claro entre ruido y eventos (η=0.71 < 0.80): el umbral es poco confiable
ERROR:    Medidores desconocidos: nada (disponibles: planta_2_a, planta_2_b)
```

- `INFO`: cada paso y su resultado.
- `WARNING`: algo sospechoso que conviene mirar (umbral dudoso, eventos sin grupo, carga desbalanceada).
- `ERROR`: no se puede seguir.
- No hay `DEBUG`: la salida está pensada para leerse en clase.

---

## 10. Configuración

Toda la configuración vive en `src/infrastructure/settings/config.py` con su valor por defecto. **`.env` es solo para secretos** (hoy no hay ninguno). Hay dos formas de cambiar un valor sin tocar código:

```bash
./run.sh train planta_2_b --umbral 60                 # argumento: solo para esa corrida
./run.sh train --separacion-minima 0.85 --balance-minimo 0.7
NILM_UMBRAL_KW=60 ./run.sh train planta_2_b            # variable de entorno: también sirve para ./run.sh start
```

Si usás las dos, **gana el argumento**. Los argumentos validan su rango (por ejemplo, `--separacion-minima 2` se rechaza con un mensaje).

| Variable | Argumento de `train` | Por defecto | Qué controla |
| :--- | :--- | :--- | :--- |
| `NILM_UMBRAL_KW` | `--umbral` | automático (Otsu) | Umbral de \|ΔP\| para que un salto sea evento |
| `NILM_SEPARACION_MINIMA` | `--separacion-minima` | 0.8 | η mínimo para confiar en el umbral automático |
| `NILM_EPS_KW` | `--radio` | automático (F–D / 2 × ruido) | Radio de DBSCAN |
| `NILM_MIN_EVENTOS` | `--min-eventos` | automático (uno por día, al menos 3) | Mínimo de eventos para que un grupo sea carga |
| `NILM_BALANCE_MINIMO` | `--balance-minimo` | 0.5 | Proporción encendidos/apagados para ser ON/OFF |
| `MEDICIONES_CSV_DIR` | — | `data/input` | De dónde se leen los CSV |
| `RESULTADOS_DIR` | — | `data/output` | Dónde escribe `./run.sh train` |
| `LOG_LEVEL` | — | `INFO` | Nivel de log |

> **Para discutir:** ¿por qué separar configuración de secretos? ¿Qué pasaba antes, cuando `.env.example` repetía la configuración con valores distintos a los del código?

---

## 11. La arquitectura

El proyecto usa **Clean Architecture**: el centro (las reglas de NILM) no conoce frameworks, archivos ni librerías de ML. Las dependencias apuntan **siempre hacia adentro**.

```
+------------------------ infrastructure ------------------------+
|  fastapi/ (API + páginas)   cli/ (./run.sh train)              |
|  csv/ (leer mediciones, guardar cargas)   sklearn/ (DBSCAN)    |
|  settings/ (config.py, logger.py)                              |
|  +-------------------- application ---------------------+      |
|  | IdentificarCargasUseCase  ·  DTOs (Request/Response) |      |
|  |  +----------------- domain -----------------+        |      |
|  |  | Medicion, EventoCarga, Carga, ...        |        |      |
|  |  | detectar_eventos, estimar_umbral,        |        |      |
|  |  | estimar_radio, resumir_cargas, ...       |        |      |
|  |  | Puertos: MedicionRepository,             |        |      |
|  |  | AgrupadorEventos, CargaRepository,       |        |      |
|  |  | Bitacora                                 |        |      |
|  |  +------------------------------------------+        |      |
|  +------------------------------------------------------+      |
+----------------------------------------------------------------+
```

### Mapa de archivos

| Capa | Archivo | Qué tiene |
| :--- | :--- | :--- |
| Dominio | `src/domain/cargas/simulacion.py` | `simular_tablero`: base + ruido + equipos ON/OFF, reproducible con semilla |
| | `src/domain/cargas/evaluacion.py` | `evaluar`: sensibilidad por equipo, precisión, cargas inventadas |
| | `src/domain/cargas/entities.py` | `Medicion`, `EventoCarga`, `Carga` (con `es_on_off`), `EstimacionUmbral`, `BarraHistograma` |
| | `src/domain/cargas/services.py` | Funciones puras: `saltos_kw`, `detectar_eventos`, `estimar_umbral` (Otsu), `nivel_de_ruido`, `estimar_radio` (F–D), `estimar_min_eventos`, `histograma`, `resumir_cargas` |
| | `src/domain/cargas/repositories.py` | **Puertos** (interfaces): `MedicionRepository`, `AgrupadorEventos`, `CargaRepository`, `Bitacora` |
| Aplicación | `src/application/cargas/use_cases/identificar_cargas.py` | Orquesta los 4 pasos, decide umbral/radio automáticos o fijos, registra en el log |
| | `src/application/cargas/dtos/identificar_cargas.py` | Lo que entra y sale (Pydantic) |
| Infraestructura | `src/infrastructure/csv/medicion_repository.py` | Lee `data/input/<medidor>.csv` (y rechaza nombres que no existan) |
| | `src/infrastructure/csv/carga_repository.py` | Escribe `data/output/cargas_<medidor>.csv` |
| | `src/infrastructure/csv/verdad_repository.py` | Lee y escribe la verdad de los tableros simulados (`data/verdad/`) |
| | `src/infrastructure/sklearn/dbscan_agrupador.py` | DBSCAN detrás del puerto `AgrupadorEventos` |
| | `src/infrastructure/fastapi/` | Endpoint (`routers/cargas.py`) y armado de dependencias (`dependencies.py`) |
| | `src/infrastructure/cli/entrenar_cargas.py` | `./run.sh train` |
| | `src/infrastructure/settings/` | `config.py` (toda la configuración) y `logger.py` (único lugar que importa `logging`) |
| Entrada | `src/main.py` | Crea la app, sirve `/`, `/guia`, `/static` y maneja el 404 de medidor desconocido |
| Web | `web/energia.*`, `web/guia.*` | Páginas (HTML + CSS + JS sin frameworks; la guía usa `marked` + `DOMPurify`) |

### Conceptos y dónde verlos

| Concepto | Ejemplo en este repo |
| :--- | :--- |
| **Dominio puro** | `services.py` no importa nada externo: Otsu y Freedman–Diaconis están escritos a mano, sin numpy. Se testea sin servidor ni archivos. |
| **Puertos y adaptadores** | `MedicionRepository` (puerto) ← `CsvMedicionRepository` (adaptador). Antes había un adaptador MySQL. |
| **Cambiar un adaptador sin tocar el núcleo** | MySQL → CSV (`92a24eb`): dominio y caso de uso no cambiaron. |
| **Un adaptador por capacidad, no por librería** | Se quitó numpy (era un detalle de sklearn, `90f1485`); se agregó `CargaRepository` porque *guardar resultados* es una capacidad (`e5ff774`). |
| **Inyección de dependencias** | El caso de uso recibe repositorio, agrupador y logger por constructor; `dependencies.py` (API) y la CLI los arman. |
| **ML como detalle** | DBSCAN vive en `infrastructure/sklearn/`. Cambiarlo por otro algoritmo no toca el dominio. |
| **Varios mecanismos de entrega** | API, web y consola sobre el mismo caso de uso. |

---

## 12. Tests: guardianes del comportamiento y del diseño

```bash
./run.sh test        # 45 tests
```

| Tipo | Dónde | Qué verifican |
| :--- | :--- | :--- |
| Unitarios | `tests/unit/` | Reglas del dominio (eventos, Otsu, radio, histograma, ON/OFF) y el caso de uso con dobles de prueba |
| Integración | `tests/integration/` | Adaptadores reales: leer/escribir CSV, DBSCAN |
| De punta a punta | `tests/e2e/` | La API, las páginas y `./run.sh train` completos |
| **Arquitectura** | `tests/test_architecture.py` (`./run.sh gauntlet`) | 11 reglas: el dominio no importa frameworks, sin imports relativos, sin `print`, sin SQL armado con strings, sin secretos en el código, tipos en todas las funciones… |
| **Diseño** | `tests/test_god_components.py`, `tests/test_clean_design.py` (`./run.sh audit`) | Funciones o archivos demasiado grandes, código que nadie usa |
| Logging | `tests/test_logging.py` | Solo `logger.py` importa `logging` |

### Cuando los tests frenaron un mal cambio (casos reales)
- **"Función Dios"**: al agregar logs, `execute` llegó a 78 líneas y el test falló. Se dividió en un método por paso; ahora `execute` se lee como el resumen del algoritmo (`d4696c5`).
- **"Código muerto"**: al mover la CLI a `src/`, el test la marcó como inalcanzable… porque no tenía tests. Se agregaron (`d2dc43b`).
- **Datos sintéticos**: el test de la CLI mostró que el radio automático separaba encendidos de apagados; eso llevó al piso de 2 × ruido (§7).
- **Un `try` silencioso**: al cambiar `httpx` por `httpx2`, un import dentro de un `try` hacía que un test se *salteara* sin fallar. Lo delató el "1 skipped" (`470fea6`).

---

## 13. Historia del proyecto, commit a commit

El repo empezó como un clasificador de diabetes y se transformó **con commits atómicos** (un cambio lógico por commit). Algunos hitos:

| Commit | Qué cambió | Concepto |
| :--- | :--- | :--- |
| `e854e17` | Se quita un endpoint ajeno al dominio | Alcance / YAGNI |
| `3685d11` | Entidades y reglas puras, con tests | Dominio sin dependencias |
| `913ca17` | Repositorio SQL | Puertos y adaptadores |
| `c580d2a` | DBSCAN detrás de un puerto | ML como detalle |
| `9a374c9` | Se borra el sistema viejo | *Strangler fig*: reemplazo gradual |
| `a4ca616` | Datos anonimizados en CSV | Datos versionados |
| `92a24eb` | MySQL → CSV | Reemplazar un adaptador sin tocar el núcleo |
| `7c64684` | Logs `info`/`warning`/`error` | Inyección de dependencias (`Bitacora`) |
| `29894e5` | Configuración en `config.py` | Configuración vs. secretos |
| `d4696c5` | Logs explicativos + `execute` dividido | Los tests de diseño frenan malos cambios |
| `d2dc43b` | CLI en `src/` + `./run.sh train` | Mecanismos de entrega en infraestructura |
| `e5ff774` | `CargaRepository` | Un adaptador por capacidad |
| `5d8e90a` | Umbral automático (Otsu) | Del número mágico a la estimación |
| `32f381d` | Histograma en la web | Mostrar el porqué, no solo el resultado |
| `6e0a186` | Página en 4 pasos explicados | Comunicar resultados a no especialistas |
| `9064cd8` | Radio automático (F–D / 2 × ruido) | Parámetros con sentido físico |
| `8ff09b1` | Mínimo de eventos automático (uno por día) | Criterios que no dependen del largo del rango |
| `85addfc` | Parámetros NILM por argumento en `./run.sh train` | Experimentar sin tocar código |
| `c88d64e` | Gráfico de la potencia en el tiempo | Ver la señal antes de abstraerla |
| `76247ac` | Tablero simulado con equipos conocidos | Datos sintéticos como experimento controlado |
| `faed83e` | Evaluación contra la verdad | Medir el error: sensibilidad y precisión |
| `552f33b` | El simulador respeta la frecuencia pedida | Verificar los datos sintéticos también |

### Decisiones y alternativas descartadas

| Se discutió | Se decidió | Por qué |
| :--- | :--- | :--- |
| Leer siempre de MySQL | CSV versionados | Los alumnos no tienen acceso a la base; el núcleo no cambia |
| Un adaptador `numpy/` | Quitar numpy | No es una capacidad del dominio, era un detalle de sklearn |
| `structlog` | `logging` estándar | Logs para leer en clase, no para un agregador; cambiarlo luego es tocar un solo archivo |
| Dos scripts de consola | Uno (`./run.sh train`) | Menos puntos de entrada, menos confusión |
| Lógica en `run.sh` | `run.sh` solo lanza | La lógica en Python se testea |
| Umbral mediana + k·MAD | Otsu | Ningún *k* servía para los dos tableros |
| Radio por codo de *k*-distancias | Freedman–Diaconis + 2 × ruido | El codo da radios diminutos en una dimensión |
| Automatizar todo, incluida la confianza mínima | Estimar umbral, radio y mínimo; dejar fijas las reglas de decisión | Cuánta confianza exigir no se deduce de los datos: es una decisión explícita |

---

## 14. Ejercicios

Ordenados de menor a mayor dificultad. Los resultados esperados se verificaron con los datos del repo.

**1. Recorrer el algoritmo.** Abrí la página, elegí `planta_2_a` y explicá con tus palabras cada uno de los 4 pasos. ¿Qué te dice el histograma?

**2. Umbral fijo vs. automático.** Corré `./run.sh train planta_2_b` y `NILM_UMBRAL_KW=60 ./run.sh train planta_2_b`. ¿Qué carga aparece en cada caso? ¿A cuál le creés?
*Esperado*: automático ~75 kW con `WARNING` (η = 0,71); con 60 kW, ~88 kW. El histograma sin valle explica la duda.

**3. Bajar el umbral.** `NILM_UMBRAL_KW=20 ./run.sh train planta_2_a`. ¿Qué le pasa a la carga principal?
*Esperado*: entran ~1040 eventos (contra ~850) y la carga "baja" a ~79 kW con ≈22 ciclos/día: saltos de ruido de 20–70 kW se encadenan con la carga real y corren el promedio.

**4. Estabilidad en el tiempo.** `./run.sh train planta_2_a --desde 2026-09-15 --hasta 2026-09-22`. ¿Se sostiene la carga?
*Esperado*: sí, ~92 kW y ≈18/día (umbral 50,8 kW, η = 0,89). Una carga real es estable.

**5. El radio importa.** `NILM_EPS_KW=8 ./run.sh train planta_2_a` y comparalo con el automático (10,8 kW). ¿Cuántos eventos quedan sin grupo en cada caso? ¿Cambia la carga principal?
*Esperado*: con 8 kW quedan 44 sin grupo y con el automático 37; la carga principal casi no cambia (~90,5 contra ~90,8 kW). El radio afina, pero no decide el resultado.

**6. La carga sospechosa.** Corré `NILM_MIN_EVENTOS=10 ./run.sh train planta_2_a`: aparece una carga de ~222 kW con 2 encendidos y 18 apagados. ¿Por qué no aparece con el mínimo automático? ¿Por qué tiene tan pocos encendidos? Proponé dos explicaciones físicas y cómo verificarlas mirando los CSV (pista: buscá los instantes de esos saltos).

**7. Leer el código.** En `services.py`, seguí `estimar_umbral` línea por línea. ¿Qué es `varianza_entre`? ¿Por qué se recorren los saltos ordenados?

**8. Arquitectura: otro formato de salida.** Implementá `JsonCargaRepository` (puerto `CargaRepository`) y usalo en la CLI. ¿Qué archivos tocaste? ¿Cambió el dominio?
*Esperado*: un adaptador nuevo, una línea en la CLI y su test. El dominio y el caso de uso no cambian.

**9. Arquitectura: otro algoritmo.** Reemplazá DBSCAN por otro agrupador (por ejemplo, uno hecho a mano que junte saltos a menos de `radio_kw`). ¿Qué tests tuviste que cambiar?

**10. Un test que te frene.** Agregá una función de 80 líneas en el caso de uso y corré `./run.sh test`. ¿Qué test falla y por qué es útil?

**11. Elegir una regla de decisión.** Corré `./run.sh train --balance-minimo 0.9` y `./run.sh train planta_2_a --desde 2026-09-20 --hasta 2026-09-21 --balance-minimo 0.3`. ¿Qué cargas cambian de "confiable" a "dudosa" o al revés? Con lo que viste, ¿qué valor elegirías para analizar un solo día, y por qué?
*Esperado*: con 0,9 nada cambia, pero la carga de ~91 kW (388/426 = 0,91) queda **al límite**: un poco más estricto y una carga real pasaría a "dudosa". En el día del 20-09 la carga de ~93 kW da 16/19 = 0,84 y la de ~212 kW da 0: cualquier corte entre 0,1 y 0,8 da el mismo resultado. Es el "hueco" de la sección 7.

**12. Hacia lo supervisado.** Diseñá cómo etiquetarías eventos ("este salto fue el compresor") y qué clasificador entrenarías. ¿Qué features agregarías además de |ΔP| (hora del día, duración encendido, corriente por fase, factor de potencia)?

---

## 15. Secuencia sugerida de clases

Pensada para nivel terciario, con clases de ~2 horas. Las actividades son las del [cuaderno del alumno](cuaderno-alumno.md); los ejercicios (§14) quedan como práctica adicional o evaluación.

| Clase | Tema | Cuaderno | Esta guía |
| :--- | :--- | :--- | :--- |
| 1 | El problema y la señal | §1–3, actividad 1 | §2, §4, §8 |
| 2 | Del salto al evento: Otsu a mano y el histograma | §4, actividades 2 y 3 | §5, §6 |
| 3 | Agrupar sin etiquetas: DBSCAN, radio y mínimo | §5, actividad 4 | §7 |
| 4 | Validar sin respuestas: reglas de decisión | §6, actividad 5 | §6, §7, §8 |
| 5 | Medir el error con datos simulados | §7, actividades 6 a 9 | §17 |
| 6 | Cómo está construido: arquitectura y tests | §8, actividad 10 | §11, §12, §13 |
| 7 | Cierre y puente al aprendizaje supervisado | §9 | §5 ("¿es ML?") |

--- | :--- | :--- |
| 1 | El problema NILM y los datos | §2, §4, página web; ejercicio 1 |
| 2 | Del salto al evento: umbral, histograma, Otsu | §5, §6; ejercicios 2, 3 y 7 |
| 3 | Clustering no supervisado: DBSCAN y su radio | §5, §7; ejercicios 4 y 5 |
| 4 | Validar sin etiquetas: hallazgos, cargas dudosas y reglas de decisión | §6, §7, §8; ejercicios 6 y 11 |
| 5 | Clean Architecture: capas, puertos y adaptadores | §11, historia (§13); ejercicio 8 |
| 6 | Tests como guardianes del diseño | §12; ejercicios 9 y 10 |
| 7 | Hacia lo supervisado | §5 ("¿es ML?"); ejercicio 12 |

---

## 16. Glosario

| Término | Significado |
| :--- | :--- |
| **NILM** | Deducir qué equipos funcionan a partir del consumo total, sin medidores por equipo |
| **Potencia activa (kW)** | La energía por unidad de tiempo que se convierte en trabajo útil |
| **\|ΔP\|** | Tamaño del salto de potencia entre dos mediciones consecutivas |
| **Evento** | Un salto que supera el umbral: algo se encendió (↑) o se apagó (↓) |
| **Ruido** | Saltos chicos por equipos que varían de a poco; también, eventos que DBSCAN no agrupa |
| **Umbral** | Tamaño mínimo de salto para considerarlo evento |
| **Método de Otsu** | Elige el corte que mejor separa dos grupos (maximiza la varianza entre ellos) |
| **η (separación)** | Calidad de esa separación, de 0 a 1 |
| **DBSCAN** | Algoritmo de clustering por densidad: agrupa puntos cercanos y deja aislados los solitarios |
| **Radio (eps)** | Distancia máxima para que dos saltos estén en el mismo grupo |
| **Freedman–Diaconis** | Regla para el ancho de agrupamiento: 2 · IQR · n^(−1/3) |
| **IQR** | Rango intercuartil: la distancia entre el percentil 25 y el 75 |
| **Carga ON/OFF** | Equipo que se enciende y apaga con potencia parecida y cantidades parecidas |
| **Ciclo** | Un encendido con su apagado |
| **Aprendizaje no supervisado** | Encontrar estructura en datos sin etiquetas |
| **Puerto / adaptador** | Interfaz que define el dominio / implementación concreta en infraestructura |
| **Inyección de dependencias** | Pasarle a un objeto lo que necesita en vez de que lo cree él |
| **Commit atómico** | Un commit = un cambio lógico completo, que se entiende solo |
| **Sensibilidad** | De los eventos que ocurrieron, qué fracción se detectó y se asignó al equipo correcto |
| **Precisión** | De los eventos detectados, qué fracción corresponde a algo que pasó |
| **Verdad (ground truth)** | Lo que realmente pasó; solo se conoce en los datos simulados |

---

## 17. Respuestas del cuaderno del alumno

Todas se obtuvieron corriendo el sistema con los datos del repositorio. Los tiempos son orientativos para nivel terciario.

### Actividad 1 — Mirar la señal (20 min)
- En el 20-09 se ve una base de ~260 kW durante el turno (más baja de noche) con **pulsos de ~92 kW**, unos 19 en el día: más o menos **uno por hora**, bastante regulares.
- El salto distinto es una **caída grande al final del día** (~212 kW): la planta que para. El sistema la agrupa como "carga" de ~212 kW con 0 encendidos y 3 apagados, y la marca dudosa.
- En el mes no se distinguen los escalones porque hay ~800 eventos en el ancho de la pantalla: cada píxel junta varias horas.
- **Error común**: confundir la variación lenta de la base con eventos. Preguntar: "¿eso pasa de una medición a la siguiente o en varias horas?".

### Actividad 2 — Otsu a mano (30 min)
1. `5, 6, 4, 50, 52, 5, 48, 6` → umbral **27 kW** (entre 6 y 48), η = **1,00**.
2. `5, 15, 25, 35, 45, 55` → umbral **30 kW**, η = **0,77**: no hay dos grupos, los valores están repartidos parejo. Es el caso "una sola montaña": η por debajo de 0,8.
3. La línea es `varianza_entre = peso_ruido * (1 - peso_ruido) * (media_ruido - media_eventos) ** 2`.
- **Criterio**: que expliquen *por qué* gana el corte (grupos parejos y medias lejanas), no solo que lleguen al número.

### Actividad 3 — El histograma (20 min)
- `planta_2_a`: dos montañas, valle entre ~30 y ~70 kW, umbral automático 51,3 kW (η = 0,87).
- `planta_2_b`: el ruido baja de a poco, no hay valle; aviso de umbral poco confiable (η = 0,71).
- Predicción con 60 kW: la carga **sube** (de ~75 a ~88 kW), porque se dejan afuera saltos de ruido de 46–60 kW que corrían el promedio para abajo.

### Actividad 4 — Radio y mínimo (20 min)
- `planta_2_a`: radio automático 10,76 kW (ganó el piso de **2 × ruido**, con ruido = 5,4 kW), mínimo 21 eventos.
- Con `--radio 2`: los eventos sin grupo suben de 37 a **121**, y la carga queda en ~92,3 kW con menos ciclos (353 contra 388): el radio chico deja afuera eventos legítimos.
- En una semana el mínimo baja a **7**: con menos días, un equipo real junta menos eventos.

### Actividad 5 — Reglas de decisión (25 min)
1. ~222 kW con **2 encendidos y 18 apagados**; el sistema la marca "probablemente no es una sola carga ON/OFF".
2. Explicaciones aceptables: arranque **escalonado** (se prende en varios saltos chicos que no superan el umbral y se apaga de golpe); **paradas de planta** (varios equipos se apagan juntos); un equipo que se apaga por una protección. Verificación: buscar en el CSV los instantes de esos apagados y mirar qué pasa antes (¿la potencia subió de a poco?).
3. Proporción de la carga de ~91 kW: 388 / 426 = **0,91**. Con `--balance-minimo 0.95` pasa a **dudosa**: una regla demasiado estricta descarta una carga real.
4. Para un día conviene **bajarlo** (0,3–0,4): con pocos ciclos, una carga real puede quedar desbalanceada por azar (ver §7, tabla de la simulación).

### Actividad 6 — ¿Cuántos equipos encuentra? (20 min)
Con el umbral automático (47,6 kW, η = 0,91):

| | 90 kW | 40 kW | 15 kW |
| :--- | :--- | :--- | :--- |
| Sensibilidad | **99 %** (~88,6 kW) | 0 % | 0 % |

Precisión 100 %, sin cargas inventadas. El umbral queda **por encima de 40 kW**: los eventos de los equipos B y C casi no se detectan. Los pocos que sí (33 y 98) son momentos en que dos equipos cambian juntos.

### Actividad 7 — Buscar un umbral (25 min)

| Umbral | 90 kW | 40 kW | 15 kW | Precisión |
| :--- | :--- | :--- | :--- | :--- |
| 30 kW | 99 % (pero estimada en ~81 kW) | 0 % (166 detectados) | 0 % | 100 % |
| 10 kW | **0 %** | 90 % (estimada en ~47 kW) | 0 % (973 detectados) | 96 % |

- Con 30 kW, los eventos de 40 kW **se detectan pero se mezclan** con los de 90 kW en un solo grupo de ~81 kW.
- Con 10 kW, DBSCAN encadena todo: se pierde el equipo de 90 kW.
- **Ningún umbral solo** encuentra los tres (probado de 10 a 40 kW).

### Actividad 8 — Umbral y radio (30 min)

| Umbral | Radio | 90 kW | 40 kW | 15 kW | Precisión |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 30 | 5 | 97 % | **81 %** | 0 % | 100 % |
| 10 | 3 | **96 %** | **79 %** | **74 %** | 96 % |
| 10 | 2 | 95 % | 70 % | 74 % | 96 % |

- Achicar el radio **separa** grupos (corta los "puentes").
- La combinación que encuentra los tres es **umbral 10 + radio 3**. El radio automático (≈ 2 × ruido) es demasiado generoso cuando hay equipos de tamaños cercanos.
- **Lo central de la actividad**: la combinación se encontró **comparando con la verdad**. En `planta_2_a` no se puede hacer: para ajustar hace falta saber la respuesta, es decir, **datos etiquetados**. Es el argumento para pasar a supervisado.

### Actividad 9 — Tu propio tablero (20 min)
- Semilla 7: resultados casi iguales (90 kW al 98 %; 40 y 15 kW no encontradas). El comportamiento no depende de una semilla en particular.
- Ruido de 8 kW: el umbral sube apenas (50 kW, η = 0,87) y el resultado es el mismo: el de 90 kW se sigue encontrando (99 %), los otros no.
- **Hallazgo clave para discutir**: con los parámetros automáticos, el sistema solo encuentra los equipos de **más de la mitad del más grande**. Otsu corta cerca de la mitad del equipo mayor, así que todo lo que esté por debajo queda como "ruido".
  - 150, 60 y 25 kW (ruido 2 kW): solo encuentra el de 150 (97 %), umbral 74 kW. Un tablero "bien separado" **no** alcanza.
  - 90 y 60 kW o 90 y 70 kW (ruido 2 kW): encuentra los dos (88–97 %), umbral ~43 kW.
  - Para que encuentre todo, los equipos tienen que estar entre la mitad y el total del más grande. Si un alumno llega a esta regla por su cuenta, la actividad cumplió su objetivo.

### Actividad 10 — Arquitectura (40 min)
1. `services.py` no importa librerías externas para que las reglas se puedan probar y entender solas, y para poder cambiar sklearn o el formato de archivos sin tocarlas.
2. `JsonCargaRepository`: un archivo nuevo en `src/infrastructure/` (o `json/`), una línea en `entrenar_cargas.py` y su test. **Nada en `src/domain/`**.
3. Falla `tests/test_god_components.py::test_no_critical_god_functions`. Es útil porque frena funciones que nadie va a poder revisar ni testear, antes de que lleguen a `main`.

### Cierre — Hacia lo supervisado (discusión)
- La verdad tiene **etiquetas** (qué equipo produjo cada evento); DBSCAN solo tenía tamaños.
- En una fábrica real las pondría alguien de mantenimiento: anotar cuándo arranca cada equipo, o instalar un medidor temporal en un equipo.
- Features útiles: hora del día, duración encendido, forma del salto (de golpe o en rampa), potencia reactiva, corriente por fase.
- Modelo: un clasificador (árbol de decisión, random forest, k vecinos) que aprenda "evento → equipo".
