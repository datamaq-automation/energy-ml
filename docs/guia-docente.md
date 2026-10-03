# Guía docente — energy-ml

Esta guía acompaña el repositorio para usarlo en clase. El código muestra **qué** hace el sistema; acá está **por qué** quedó así, qué se encontró en los datos y qué ejercicios proponer.

> Para ver el código en cualquier punto: `git log --oneline` y `git checkout <hash>`. Volvé al presente con `git checkout main`.

## 1. El problema

Una planta tiene un medidor por tablero, no uno por equipo. **NILM** (*Non-Intrusive Load Monitoring*) intenta deducir qué equipos se encienden y se apagan mirando solo el consumo total.

La idea central es simple: cuando un equipo de 90 kW arranca, el consumo total sube de golpe unos 90 kW. Si ese salto se repite cientos de veces, probablemente sea siempre el mismo equipo.

## 2. Cómo correrlo

```bash
./run.sh start                                   # página en http://localhost:8000 (esta guía en /guia)
./run.sh train                                   # identifica cargas de data/input/ → data/output/
./run.sh train planta_2_a --desde 2026-09-15     # un medidor, desde una fecha
NILM_UMBRAL_KW=60 ./run.sh train                 # mismo proceso con umbral fijo, para comparar
./run.sh test                                    # tests, incluidos los de arquitectura
```

No hace falta base de datos ni `.env`: los datos están versionados en `data/input/`.

## 3. Los datos

| Archivo | Qué es |
| :--- | :--- |
| `data/input/planta_2_a.csv` | Tablero "arriba" de una planta papelera (fuerza motriz, preparación de pasta) |
| `data/input/planta_2_b.csv` | Tablero "abajo" de la misma planta (máquina papelera continua) |

- Dos columnas: `instante` y `potencia_kw` (potencia activa total, ya en kW).
- Una medición cada ~5 minutos, del 11-09 al 03-10-2026 (~6150 filas por archivo).
- Están **anonimizados**: no figuran los nombres reales de los medidores ni de la cooperativa.

## 4. El algoritmo, paso a paso

Es lo mismo que muestran los logs (`Paso 1/4` … `Paso 4/4`):

1. **Leer** las mediciones del rango pedido.
2. **Detectar eventos**: cada salto |ΔP| entre dos mediciones consecutivas que supera un **umbral** es un encendido (↑) o un apagado (↓).
3. **Agrupar** los eventos por magnitud con **DBSCAN**: saltos de tamaño parecido caen en el mismo grupo.
4. **Resumir**: cada grupo es una *carga candidata* con su potencia típica, encendidos, apagados y ciclos.

### ¿Esto es *machine learning*?

| Paso | ¿Aprende de los datos? |
| :--- | :--- |
| Detectar eventos | Solo el umbral, si es automático (ver §5). La detección en sí es una regla. |
| Agrupar con DBSCAN | **Sí: aprendizaje no supervisado.** Nadie le dice qué cargas existen; encuentra los grupos solo. |
| Resumir | No: es estadística descriptiva. |

Dos consecuencias para discutir en clase:

- **No hay "respuesta correcta"**: sin etiquetas no se puede medir un error como en un problema supervisado. Hay que validar con sentido físico (ver la carga de 227 kW en §6).
- **`./run.sh train` no guarda un modelo**: DBSCAN agrupa desde cero cada vez. Lo que queda en `data/output/` es el resultado del agrupamiento.

El camino natural del curso: **no supervisado** (descubrir cargas) → **etiquetado** por alguien de planta ("esto es el compresor 2") → **supervisado** (un clasificador que reconozca cada equipo, y ahí sí un modelo para guardar).

## 5. El umbral: de un número arbitrario a uno estimado

Al principio el umbral era **60 kW fijo**. Funcionaba, pero ¿por qué 60 y no 40 u 80? La página muestra el **histograma de |ΔP|**, que responde la pregunta:

- **`planta_2_a`** tiene **dos montañas**: el ruido (cargas que varían de a poco) a la izquierda y los eventos (~90 kW) a la derecha, con un **valle vacío entre 30 y 70 kW**. Cualquier umbral en el valle da el mismo resultado; por eso 60 "andaba".
- **`planta_2_b`** **no tiene valle**: el ruido baja de a poco y se mezcla con los eventos.

Se probaron tres ideas antes de elegir una:

| Método | Resultado |
| :--- | :--- |
| Umbral = mediana + k·MAD del ruido | Ningún *k* sirve para los dos tableros: con k=5, en `planta_2_b` el umbral sube a 103 kW y se pierde la carga de 88 kW. Cambia un número arbitrario por otro. |
| **Valle del histograma (método de Otsu)** | **Elegido.** Busca el corte que mejor separa dos grupos y además mide qué tan buena es esa separación. |
| Sin umbral: DBSCAN sobre todos los saltos | Más limpio en teoría, pero DBSCAN pasa a depender todavía más de su `eps`, que también es arbitrario. |

**Otsu** prueba cada corte posible y se queda con el que maximiza la varianza *entre* los dos grupos. Su medida de calidad, **η** (entre 0 y 1), dice qué tan claras son las dos montañas:

| Caso | Umbral | η | Lectura |
| :--- | :--- | :--- | :--- |
| `planta_2_a` | 51,3 kW | **0,87** | Valle claro: el resultado coincide con el de 60 kW (carga de ~91 kW, ≈18 ciclos/día) |
| `planta_2_b` | 45,6 kW | **0,71** | Sin valle: `WARNING` de umbral poco confiable |
| Una sola montaña (simulado) | — | ~0,68 | Nivel base: no hay nada que separar |

Por eso el corte de confianza es `NILM_SEPARACION_MINIMA = 0.8`.

**La lección**: el mismo algoritmo funciona perfecto en un tablero y duda en el otro, **y lo dice** en lugar de inventar un número. En `planta_2_b` el umbral automático deja entrar ruido que DBSCAN encadena con la carga real: aparece una sola carga de ~75 kW en vez de la de ~88 kW que se obtiene con 60 kW fijos.

## 6. Hallazgos en los datos

- **Carga ON/OFF de ~91 kW en `planta_2_a`**: unos 420 encendidos y 390 apagados en tres semanas, ≈18 ciclos por día. Es el hallazgo más sólido.
- **Carga de ~88 kW en `planta_2_b`** (con umbral fijo de 60 kW). Con el umbral automático, ver §5.
- **"Carga" de ~227 kW con 2 encendidos y 10 apagados**: una carga real se enciende y se apaga parecido. El sistema emite `WARNING: probablemente no es una sola carga ON/OFF` (regla `Carga.es_on_off`, `NILM_BALANCE_MINIMO = 0.5`). Puede ser un arranque escalonado, una parada de planta o varias cargas apagándose juntas.
- **Ruido sin grupo**: unos 20 eventos en `planta_2_a` no entran en ningún grupo. DBSCAN los marca como ruido (etiqueta -1) en vez de forzarlos.

## 7. La arquitectura como contenido del curso

El proyecto usa **Clean Architecture**: el dominio (reglas de NILM) no conoce frameworks, archivos ni librerías de ML. Cada cambio del historial ilustra un concepto:

| Concepto | Dónde verlo | Commit |
| :--- | :--- | :--- |
| Dominio sin dependencias | `src/domain/cargas/` (entidades y reglas puras, con tests) | `3685d11` |
| Puertos y adaptadores | `MedicionRepository` (puerto) e implementación SQL | `913ca17` |
| ML como detalle de infraestructura | `DbscanAgrupador` detrás del puerto `AgrupadorEventos` | `c580d2a` |
| Varios mecanismos de entrega | API, página web y consola sobre el mismo caso de uso | `7971770`, `bb927cb`, `d2dc43b` |
| **Reemplazar un adaptador sin tocar el núcleo** | MySQL → CSV: dominio y caso de uso no cambian | `92a24eb` |
| Un adaptador por *capacidad*, no por librería | Se quita numpy (detalle de sklearn); se agrega `CargaRepository` para guardar resultados | `90f1485`, `e5ff774` |
| Inyección de dependencias | El caso de uso recibe el logger por constructor (puerto `Bitacora`) | `7c64684` |
| Configuración vs. secretos | Todo en `config.py`; `.env` solo para secretos (hoy no hay ninguno) | `29894e5` |
| Tests que frenan malos diseños | "Función Dios" obligó a dividir `execute`; "código muerto" pidió tests para la CLI | `d4696c5`, `d2dc43b` |
| Del número mágico a la estimación | Umbral automático con Otsu + histograma | `5d8e90a`, `32f381d` |

### Reglas que el código hace cumplir

- **Capas**: `tests/test_architecture.py` falla si el dominio importa FastAPI, ORMs o infraestructura.
- **Logging**: solo `src/infrastructure/settings/logger.py` importa `logging` (`tests/test_logging.py`). Solo se usan `info`, `warning` y `error`, con el formato de uvicorn, para que la consola cuente el proceso.
- **Diseño**: `tests/test_god_components.py` y `tests/test_clean_design.py` detectan funciones gigantes y archivos que nadie usa.

## 8. Ejercicios

1. **Umbral fijo vs. automático.** Corré `./run.sh train planta_2_b` y `NILM_UMBRAL_KW=60 ./run.sh train planta_2_b`. ¿Qué cargas aparecen en cada caso? ¿A cuál le creés y por qué? Mirá el histograma en la página.
   *Esperado*: con 60 kW aparece ~88 kW; con el automático, ~75 kW y un `WARNING`. El histograma sin valle explica la duda.

2. **Bajar el umbral.** `NILM_UMBRAL_KW=20 ./run.sh train planta_2_a`. ¿Qué le pasa a la carga de ~91 kW?
   *Esperado*: entran ~1040 eventos (contra ~850) y la carga "baja" a ~79 kW con ≈22 ciclos/día: DBSCAN encadena saltos de ruido de 20–70 kW con la carga real y el promedio se corre. El umbral no solo filtra: cambia lo que el modelo cree que es la carga.

3. **Una semana vs. el mes.** `./run.sh train planta_2_a --desde 2026-09-15 --hasta 2026-09-22`. ¿Se sostiene la carga de ~91 kW? ¿Y los ciclos por día?
   *Esperado*: sí, ~92 kW y ≈18/día (umbral automático 50,8 kW, η=0,89). Una carga real es estable en el tiempo.

4. **La carga sospechosa.** ¿Por qué ~227 kW tiene 2 encendidos y 10 apagados? Proponé dos explicaciones físicas y cómo verificarlas con los datos.

5. **`eps` también es arbitrario.** `NILM_EPS_KW = 8` no depende de la escala del medidor. Proponé una forma de calcularlo (pista: en relación con el umbral) e implementala con un test.

6. **Arquitectura.** Agregá un adaptador que guarde los resultados en JSON en vez de CSV implementando `CargaRepository`. ¿Qué archivos tuviste que tocar? ¿Cambió el dominio?
   *Esperado*: un adaptador nuevo y una línea en la CLI; el dominio y el caso de uso no cambian.

7. **Hacia lo supervisado.** Diseñá cómo etiquetarías eventos ("este salto fue el compresor") y qué clasificador entrenarías. ¿Qué features agregarías además de |ΔP| (hora, corriente por fase, factor de potencia)?
