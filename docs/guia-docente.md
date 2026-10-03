# Guía docente — energy-ml

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
| `./run.sh train [medidores] [--desde F] [--hasta F]` | Identifica cargas por consola y guarda los resultados en `data/output/` |
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
- **mínimo de eventos** (`min_samples` = `NILM_MIN_EVENTOS` = 10): menos que eso no se considera una carga.

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

**La lección central**: el mismo algoritmo funciona perfecto en un tablero y duda en el otro, **y lo dice**. En `planta_2_b` el umbral deja entrar ruido que se encadena con la carga real: aparece ~75 kW en vez de los ~88 kW que da un umbral de 60 kW. El sistema no puede arreglarlo solo, pero avisa en el log, en el paso 2 de la página y en la tarjeta de la carga.

---

## 7. El radio de DBSCAN: también automático

El radio (`eps`) era **8 kW fijo**, sin relación con la escala de cada medidor. Ahora es **el mayor de dos valores**:

1. **Regla de Freedman–Diaconis**: `2 · IQR · n^(−1/3)`, el ancho "natural" para agrupar valores en una dimensión. Crece si los saltos están dispersos (IQR = rango intercuartil) y se achica con más datos (*n*).
2. **Piso físico: 2 × ruido**. El ruido es la mediana de los saltos que *no* llegan al umbral. Cada evento trae el ruido de dos mediciones, así que el encendido (89 kW) y el apagado (91 kW) de un mismo equipo pueden diferir hasta en 2 × ruido.

| Caso | Ruido | Radio | Resultado |
| :--- | :--- | :--- | :--- |
| `planta_2_a`, mes | 5,4 kW | 10,8 kW | ~91 kW (429 ↑ / 391 ↓) + una carga dudosa de ~222 kW |
| `planta_2_a`, semana | 5,0 kW | 9,9 kW | ~92 kW (134 ↑ / 126 ↓) |
| `planta_2_b`, mes | 14,5 kW | 29,0 kW | ~75 kW (sin cambios: su problema es el umbral) |

### Cómo se llegó a esto (vale contarlo en clase)

| Intento | Problema |
| :--- | :--- |
| Codo de la curva de *k*-distancias (el método "de libro") | En una dimensión con cientos de eventos, los vecinos siempre están cerca: dio 1–2 kW y partió la carga de 91 kW. |
| Solo Freedman–Diaconis | Funciona con datos reales, pero con datos sintéticos limpios (saltos de 89 y 91 exactos) separó encendidos de apagados en dos "cargas". |
| Freedman–Diaconis con piso = ruido | Todavía separaba 89 de 91 con ruido de 1 kW. |
| **Freedman–Diaconis con piso = 2 × ruido** | Elegido: estable en mes y semana, y con sentido físico. |

> Los tests encontraron el problema que los datos reales no mostraban. Un buen dato sintético es un experimento controlado.

---

## 8. Hallazgos en los datos

- **Carga ON/OFF de ~91 kW en `planta_2_a`**: unos 430 encendidos y 390 apagados en 21 días, **≈18 ciclos por día**. Estable al cambiar el rango. Es el hallazgo más sólido.
- **Carga de ~88 kW en `planta_2_b`** con umbral de 60 kW; ~75 kW con el automático (dudoso, §6).
- **"Carga" de ~222 kW con 2 encendidos y 18 apagados** en `planta_2_a`: un equipo real se enciende y apaga parecido. La regla `Carga.es_on_off` (`NILM_BALANCE_MINIMO = 0.5`: uno puede ser a lo sumo el doble del otro) la marca **dudosa**. Puede ser un arranque escalonado, una parada de planta o varios equipos apagándose juntos.
- **Eventos sin grupo**: 11 en `planta_2_a`. DBSCAN prefiere no forzarlos.
- **Más encendidos que apagados** en casi todas las cargas (429 contra 391). Una hipótesis para verificar: con una medición cada 5 minutos, un apagado puede quedar "repartido" en dos saltos chicos que no superan el umbral.

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
| `radio` | `{kw, automatico}` — paso 3 |
| `cargas` | Paso 4: `{potencia_tipica_kw, encendidos, apagados, ciclos, ciclos_por_dia, on_off}` |

Un medidor inexistente responde **404** (y la API nunca lee archivos fuera de `data/input/`: pedir `../.env` también da 404).

### Consola (`./run.sh train`)
Procesa todos los medidores (o los que indiques) y escribe `data/output/cargas_<medidor>.csv`. Es la que conviene para experimentar cambiando parámetros.

### Los logs cuentan el proceso
Solo tres niveles, todos con el formato de uvicorn:

```
INFO:     Umbral automático: 51.3 kW (Otsu, separación ruido/eventos η=0.87)
INFO:     Radio automático: 10.76 kW (mayor entre Freedman–Diaconis y 2 × ruido de la señal, ruido = 5.4 kW)
WARNING:  ~222.0 kW tiene 2 ↑ y 18 ↓: probablemente no es una sola carga ON/OFF
ERROR:    Medidores desconocidos: nada (disponibles: planta_2_a, planta_2_b)
```

- `INFO`: cada paso y su resultado.
- `WARNING`: algo sospechoso que conviene mirar (umbral dudoso, eventos sin grupo, carga desbalanceada).
- `ERROR`: no se puede seguir.
- No hay `DEBUG`: la salida está pensada para leerse en clase.

---

## 10. Configuración

Toda la configuración vive en `src/infrastructure/settings/config.py` con su valor por defecto. **`.env` es solo para secretos** (hoy no hay ninguno). Cualquier valor se puede cambiar por variable de entorno sin tocar código:

```bash
NILM_UMBRAL_KW=60 ./run.sh train planta_2_b
```

| Variable | Por defecto | Qué controla |
| :--- | :--- | :--- |
| `NILM_UMBRAL_KW` | automático (Otsu) | Umbral de \|ΔP\| para que un salto sea evento |
| `NILM_SEPARACION_MINIMA` | 0.8 | η mínimo para confiar en el umbral automático |
| `NILM_EPS_KW` | automático (F–D / 2 × ruido) | Radio de DBSCAN |
| `NILM_MIN_EVENTOS` | 10 | Mínimo de eventos para que un grupo sea carga |
| `NILM_BALANCE_MINIMO` | 0.5 | Proporción encendidos/apagados para ser ON/OFF |
| `MEDICIONES_CSV_DIR` | `data/input` | De dónde se leen los CSV |
| `RESULTADOS_DIR` | `data/output` | Dónde escribe `./run.sh train` |
| `LOG_LEVEL` | `INFO` | Nivel de log |

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
| Dominio | `src/domain/cargas/entities.py` | `Medicion`, `EventoCarga`, `Carga` (con `es_on_off`), `EstimacionUmbral`, `BarraHistograma` |
| | `src/domain/cargas/services.py` | Funciones puras: `saltos_kw`, `detectar_eventos`, `estimar_umbral` (Otsu), `nivel_de_ruido`, `estimar_radio` (F–D), `histograma`, `resumir_cargas` |
| | `src/domain/cargas/repositories.py` | **Puertos** (interfaces): `MedicionRepository`, `AgrupadorEventos`, `CargaRepository`, `Bitacora` |
| Aplicación | `src/application/cargas/use_cases/identificar_cargas.py` | Orquesta los 4 pasos, decide umbral/radio automáticos o fijos, registra en el log |
| | `src/application/cargas/dtos/identificar_cargas.py` | Lo que entra y sale (Pydantic) |
| Infraestructura | `src/infrastructure/csv/medicion_repository.py` | Lee `data/input/<medidor>.csv` (y rechaza nombres que no existan) |
| | `src/infrastructure/csv/carga_repository.py` | Escribe `data/output/cargas_<medidor>.csv` |
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
*Esperado*: con 8 kW quedan 20 sin grupo y con el automático 11; la carga principal casi no cambia (~91 kW). La carga dudosa pasa de ~227 a ~222 kW.

**6. La carga sospechosa.** ¿Por qué ~222 kW tiene 2 encendidos y 18 apagados? Proponé dos explicaciones físicas y cómo verificarlas mirando los CSV (pista: buscá los instantes de esos saltos).

**7. Leer el código.** En `services.py`, seguí `estimar_umbral` línea por línea. ¿Qué es `varianza_entre`? ¿Por qué se recorren los saltos ordenados?

**8. Arquitectura: otro formato de salida.** Implementá `JsonCargaRepository` (puerto `CargaRepository`) y usalo en la CLI. ¿Qué archivos tocaste? ¿Cambió el dominio?
*Esperado*: un adaptador nuevo, una línea en la CLI y su test. El dominio y el caso de uso no cambian.

**9. Arquitectura: otro algoritmo.** Reemplazá DBSCAN por otro agrupador (por ejemplo, uno hecho a mano que junte saltos a menos de `radio_kw`). ¿Qué tests tuviste que cambiar?

**10. Un test que te frene.** Agregá una función de 80 líneas en el caso de uso y corré `./run.sh test`. ¿Qué test falla y por qué es útil?

**11. Hacia lo supervisado.** Diseñá cómo etiquetarías eventos ("este salto fue el compresor") y qué clasificador entrenarías. ¿Qué features agregarías además de |ΔP| (hora del día, duración encendido, corriente por fase, factor de potencia)?

---

## 15. Secuencia sugerida de clases

| Clase | Tema | Material |
| :--- | :--- | :--- |
| 1 | El problema NILM y los datos | §2, §4, página web; ejercicio 1 |
| 2 | Del salto al evento: umbral, histograma, Otsu | §5, §6; ejercicios 2, 3 y 7 |
| 3 | Clustering no supervisado: DBSCAN y su radio | §5, §7; ejercicios 4 y 5 |
| 4 | Validar sin etiquetas: hallazgos y cargas dudosas | §8; ejercicio 6 |
| 5 | Clean Architecture: capas, puertos y adaptadores | §11, historia (§13); ejercicio 8 |
| 6 | Tests como guardianes del diseño | §12; ejercicios 9 y 10 |
| 7 | Hacia lo supervisado | §5 ("¿es ML?"); ejercicio 11 |

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
