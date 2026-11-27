# Guía de Andamiaje Pedagógico y Metacognición para la Formulación de Proyectos de Software

> *"El andamiaje no consiste en simplificar la tarea, sino en hacer que el aprendiz sea capaz de dominar una tarea que de otro modo estaría más allá de su capacidad actual."*  
> — **Jerome Bruner**, *The Role of Tutoring in Problem Solving*

---

## 1. Fundamentación Epistemológica: Por qué esta Guía

En la era del desarrollo asistido por Inteligencia Artificial y agentes autónomos, la habilidad más valiosa de un ingeniero de software o líder de producto ya **no es memorizar sintaxis**, sino la **capacidad de formular problemas con rigor, anticipar fallas sistémicas y definir restricciones innegociables**.

Cuando nos enfrentamos a una plantilla técnica vacía (como las especificaciones SSOT de backend o frontend), solemos experimentar dos fenómenos cognitivos estudiados por las ciencias de la educación:

1. **La Ilusión de Competencia por Relleno Formal:** Creemos que hemos diseñado un sistema robusto simplemente porque reemplazamos todos los `{placeholders}` con texto verosímil, aunque carezca de viabilidad operativa o métricas verificables.
2. **El Sesgo de Solución Prematura (*Einstellung Effect*):** La mente humana tiende a saltar de inmediato a *"cómo lo voy a programar"* (tecnologías, frameworks, librerías) antes de comprender el problema raíz, el mapa de incentivos y los casos de borde.

Esta guía constituye un **dispositivo de andamiaje cognitivo** (Bruner/Vygotsky) basado en la **mayéutica socrática** y la **metacognición** (Flavell). Su propósito no es decirte qué escribir, sino hacerte las preguntas incómodas y reflexivas que transformarán tu borrador intuitivo en una especificación de grado de producción.

---

## 2. Cómo Utilizar esta Guía

Esta guía acompaña paso a paso las **5 Secciones Modulares** de las plantillas SSOT:

```
┌────────────────────────────────────────────────────────────────────────┐
│                      Flujo Reflexivo por Sección                       │
│                                                                        │
│ 1. Sentido Formativo       --> ¿Qué capacidad analítica desarrollamos? │
│ 2. Trampas Cognitivas      --> ¿Qué errores ingenuos solemos cometer?  │
│ 3. Preguntas Mayéuticas    --> Disparadores para pensar antes de tipear│
│ 4. Rúbrica de Autocontrol  --> ¿Alcancé nivel novato o profesional?    │
└────────────────────────────────────────────────────────────────────────┘
```

**Regla de oro:** No copies y pegues estas preguntas en el documento de especificación. Respondelas mentalmente o en tus notas de trabajo; el resultado de esa reflexión es lo que debe plasmarse en el SRS definitivo.

---

## Módulo 1: Contexto Estratégico & Propuesta de Valor

### 🎯 Sentido Formativo
Comprender la diferencia entre una *idea simpática* y una *solución de valor crítico*. Todo software rentable o útil existe para aliviar un dolor real o habilitar una operación indispensable.

### 🪤 Trampas Cognitivas Frecuentes
- **El síndrome del martillo de oro:** Creer que porque una tecnología es moderna (IA, microservicios, blockchain), el problema automáticamente la necesita.
- **Definir el problema a partir de la solución:** *"El problema es que la empresa no tiene una app móvil"*. (Eso no es un problema; es la ausencia de una solución específica).
- **Confundir características con valor:** Describir *qué botones tiene el sistema* en lugar de *qué fricción elimina*.

### ❓ Batería de Preguntas Mayéuticas (Disparadores de Pensamiento)
1. **La Prueba Analógica:** Si prohibiéramos terminantemente usar computadoras, celulares y software para este problema:  
   *¿Cómo lo resuelve la gente hoy usando papel, llamadas telefónicas, cuadernos o planillas de cálculo?*
2. **El Dolor Cuantificable:**  
   *¿Qué pierde hoy el usuario con su método actual? ¿Pierde 3 horas diarias, dinero en multas, tranquilidad legal, clientes que se van enojados? ¿Podés expresarlo en números?*
3. **El Costo del Statu Quo:**  
   *Si este software nunca se construyera y todo siguiera exactamente como hoy durante los próximos 5 años, ¿qué pasaría realmente? Si la respuesta es "nada grave", el proyecto no tiene urgencia estratégica.*
4. **Empatía Situacional:**  
   *Pensá en la persona concreta que usará el sistema un martes a las 17:50 hs tras un día agotador. ¿Tu software le hace el trabajo más fácil en un clic, o le agrega burocracia de carga de datos que odiará completar?*

### 📊 Rúbrica Metacognitiva de Autoevaluación
| Criterio | Nivel 1: Novato / Superficial | Nivel 2: Intermedio | Nivel 3: Profesional / Riguroso |
| :--- | :--- | :--- | :--- |
| **Definición del Problema** | Dice "falta automatización" o "el proceso es lento". | Describe el flujo manual actual pero sin cuantificar su impacto. | Identifica el dolor con métricas (horas perdidas, % de error, costos) y actores específicos. |
| **Propuesta de Valor** | Enumera funciones ("tendrá login, reportes y dashboards"). | Explica qué hace el sistema por el usuario. | Expresa el diferencial respecto a las alternativas actuales (incluyendo Excel y papel). |

---

## Módulo 2: Modelo de Negocio Canvas & Agentes IA

### 🎯 Sentido Formativo
Desarrollar pensamiento sistémico. Ningún software opera en el vacío: vive dentro de una red de incentivos económicos, legales y humanos.

### 🪤 Trampas Cognitivas Frecuentes
- **La ilusión del usuario homogéneo:** Tratar a todos los usuarios como un único actor genérico (*"el usuario"*).
- **El sesgo del agente mágico:** Suponer que incorporar un agente de IA resuelve cualquier problema sin definir sus entradas, herramientas, límites, supervisión humana ni plan de contingencia ante alucinaciones.
- **Ignorar al que paga:** Diseñar un sistema que le encanta al usuario operativo pero que no le genera ningún retorno tangible a quien firma el cheque.

### ❓ Batería de Preguntas Mayéuticas (Disparadores de Pensamiento)
1. **Doble Actor (Usuario vs. Comprador):**  
   *¿La persona que utiliza la pantalla día a día es la misma que decide pagar por el desarrollo o la licencia? Si son personas distintas: ¿qué gana cada una?*
2. **La Responsabilidad de la Decisión del Agente:**  
   *Cuando asignás una tarea a un agente de IA en el organigrama: ¿el agente solo ejecuta trabajo mecánico (clasificar, extraer datos) o toma decisiones con impacto legal o económico? Si el agente alucina o comete un error grave, ¿quién da la cara ante el cliente o la justicia?*
3. **El Bucle de Retroalimentación Humana (*Human-in-the-Loop*):**  
   *¿En qué punto exacto un humano con criterio revisa o aprueba las acciones de la IA antes de que afecten la base de datos de producción o envíen un mensaje real a un cliente?*
4. **Sostenibilidad Económica:**  
   *Si el sistema procesa 100.000 operaciones al mes con llamadas a modelos LLM y servicios cloud: ¿cuánto cuesta la infraestructura por transacción y cuánto cobrás o ahorrás por ella? ¿El margen es positivo?*

### 📊 Rúbrica Metacognitiva de Autoevaluación
| Criterio | Nivel 1: Novato / Superficial | Nivel 2: Intermedio | Nivel 3: Profesional / Riguroso |
| :--- | :--- | :--- | :--- |
| **Organigrama de Agentes** | "Habrá un agente que hace todo con IA". | Define agentes con nombres pero sin herramientas ni límites claros. | Especifica entrada, herramientas disponibles, rol exacto, supervisor humano y fallback. |
| **Estructura de Costos** | "Costos de hosting mensuales". | Estima hosting básico pero ignora tokens de API y ancho de banda. | Modela costos variables por transacción/operación y proyecta punto de equilibrio. |

---

## Módulo 3: Requisitos del Sistema (SRS - Funcionales y No Funcionales)

### 🎯 Sentido Formativo
Aprender a traducir intenciones ambiguas en especificaciones formales, comprobables y deterministas que un ingeniero o agente IA pueda construir sin ambigüedades.

### 🪤 Trampas Cognitivas Frecuentes
- **Adjetivos trampa en NFRs:** Usar palabras como *"el sistema debe ser rápido, intuitivo, seguro, escalable y robusto"*. Estos no son requisitos; son deseos sin criterio de parada.
- **La trampa del camino feliz (*Happy Path Bias*):** Describir únicamente lo que pasa cuando todo funciona bien (el usuario tipea bien, hay internet, el servidor responde, la tarjeta tiene fondos).
- **Requisitos no testeables:** Redactar algo de modo tal que sea imposible escribir un test automatizado para verificar si se cumple o no.

### ❓ Batería de Preguntas Mayéuticas (Disparadores de Pensamiento)
1. **La Pregunta del Notario / Juez:**  
   *Si le das tu requisito a dos desarrolladores independientes en habitaciones separadas: ¿construirían exactamente el mismo flujo, o tendrían que venir a preguntarte qué quisiste decir?*
2. **Definición Operativa de "Rápido":**  
   *En vez de decir "será rápido": ¿cuántos milisegundos como máximo puede tardar el percentil 95 (p95) de las solicitudes en el momento de mayor carga del día? ¿100 ms? ¿500 ms? ¿2 segundos?*
3. **El Escenario Catastrófico de Concurrencia:**  
   *¿Qué ocurre si dos usuarios o procesos intentan modificar el mismo recurso (comprar la última entrada, cambiar el mismo estado, retirar el mismo saldo) exactamente en el mismo milisegundo? ¿Tu especificación exige transacciones atómicas, bloqueos o idempotencia?*
4. **Desconexión y Fallo Parcial:**  
   *Si a mitad de una operación de guardado se corta la conexión a internet o el servicio externo de pagos se cae: ¿en qué estado queda la base de datos? ¿Quedan datos huérfanos o inconsistentes?*

### 📊 Rúbrica Metacognitiva de Autoevaluación
| Criterio | Nivel 1: Novato / Superficial | Nivel 2: Intermedio | Nivel 3: Profesional / Riguroso |
| :--- | :--- | :--- | :--- |
| **Requisitos Funcionales** | "El usuario podrá gestionar clientes". | Detalla casos de uso pero omite validaciones y casos de error. | Define precondiciones, entradas, salidas, reglas de negocio y respuestas ante error. |
| **Requisitos No Funcionales** | "El sistema será seguro y rápido". | Pone números arbitrarios ("menos de 1 segundo"). | Especifica latencia percentil p95, throughput (RPS), RPO/RTO y estándares de cifrado. |

---

## Módulo 4: Arquitectura, Stack & Convenciones

### 🎯 Sentido Formativo
Adquirir criterio arquitectónico: entender que toda decisión técnica es un **trade-off** (compromiso) entre simplicidad, desacople, costo de mantenimiento y velocidad de entrega.

### 🪤 Trampas Cognitivas Frecuentes
- **Sobreingeniería y complejidad accidental:** Crear 5 capas de abstracción, interfaces vacías y patrones Factory para un CRUD sencillo de 2 tablas (violación de YAGNI/KISS).
- **Arquitectura de caja negra:** Adoptar Clean Architecture o FSD porque *"es lo que dice la plantilla"* sin entender qué problema de dependencias resuelve cada carpeta.
- **Cero consideración del ciclo de vida:** Pensar solo en el momento de creación del código y olvidar el mantenimiento, la depuración y los logs en producción.

### ❓ Batería de Preguntas Mayéuticas (Disparadores de Pensamiento)
1. **La Justificación de la Indirección:**  
   *¿Por qué separar Domain, Application e Infrastructure en vez de poner la consulta a la base de datos directamente en el router de FastAPI? ¿Qué ganas con esa separación y cuánto te cuesta en esfuerzo?*
2. **La Regla de la Dependencia:**  
   *Si mañana decidís cambiar la base de datos de PostgreSQL a SQLite para tests, o migrar de FastAPI a otro framework: ¿cuántas líneas de tu lógica de negocio tendrías que reescribir? (Si la respuesta es más de cero, tu dominio está acoplado a la infraestructura).*
3. **El Principio YAGNI (*You Aren't Gonna Need It*):**  
   *¿Esa interfaz genérica o clase base que creaste tiene más de una implementación real hoy? Si solo tiene una y no la vas a cambiar en los próximos 6 meses, ¿no es una sobreingeniería que solo agrega saltos cognitivos?*
4. **Imports Absolutos y Trazabilidad:**  
   *¿Por qué el Guantelete de Restricciones prohíbe los imports relativos (`../`) y exige `@/` o `from src...`? ¿Cómo ayuda eso a un agente IA o a un colega a entender dónde está parado cada módulo sin adivinar la jerarquía relativa?*

### 📊 Rúbrica Metacognitiva de Autoevaluación
| Criterio | Nivel 1: Novato / Superficial | Nivel 2: Intermedio | Nivel 3: Profesional / Riguroso |
| :--- | :--- | :--- | :--- |
| **Justificación del Stack** | "Usamos Vue porque es popular y fácil". | Lista librerías conocidas sin contrastar con requerimientos. | Justifica cada tecnología frente a las restricciones de latencia, tipado y mantenibilidad. |
| **Cumplimiento de Capas** | Mezcla consultas SQL en componentes visuales o routers. | Conoce las capas pero tolera acoplamientos sutiles. | Respeta estrictamente la inversión de dependencias verificada por análisis AST determinista. |

---

## Módulo 5: Gobernanza Normativa, Calidad & Matriz de Pruebas

### 🎯 Sentido Formativo
Internalizar la filosofía de la **verificabilidad determinista**. No confiamos en intenciones ni en promesas de agentes: confiamos en pruebas automatizadas y restricciones extremas.

### 🪤 Trampas Cognitivas Frecuentes
- **Tests tautológicos o "de confirmación":** Escribir tests que solo verifican lo obvio (`assert True == True` o probar que un getter devuelve lo que le diste) en vez de intentar activamente romper el código.
- **Commits bolsa de gatos (*"Mega Commits"*):** Hacer un commit de 80 archivos con el mensaje *"avances del viernes y fix login y además estilos"*, destruyendo la trazabilidad de Git.
- **Delegación ciega al agente:** Aceptar una solución generada por LLM simplemente porque no arrojó error de sintaxis en el editor.

### ❓ Batería de Preguntas Mayéuticas (Disparadores de Pensamiento)
1. **El Paradigma de Uncle Bob:**  
   *Si un agente IA autónomo escribe 3.000 líneas de código y te dice que terminó: ¿cómo demostrás matemáticamente que no introdujo vulnerabilidades, código muerto o efectos secundarios sin tener que leer manualmente cada línea?*
2. **La Prueba del Adversario:**  
   *Si contrataras a un hacker o tester malicioso cuyo único objetivo es hacer crashear tu sistema con datos absurdos (textos de 1 millón de caracteres, números negativos donde van cantidades, caracteres chinos o inyecciones SQL): ¿tu código falla controladamente con un error 400 claro o explota con un 500 no capturado?*
3. **La Prueba del Bisect:**  
   *Si dentro de 3 meses descubrís un bug silencioso en producción: ¿podrías encontrar el commit exacto que lo introdujo en menos de 5 minutos gracias a commits atómicos e independientes, o tendrías que revisar un mega-commit de 50 archivos mezclados?*
4. **La Regla del "Y Además":**  
   *Mirá el mensaje de tu último commit: ¿contiene la palabra "y", "además" o "también"? Si es así, no hiciste un commit atómico; mezclaste dos intenciones lógicas distintas.*

### 📊 Rúbrica Metacognitiva de Autoevaluación
| Criterio | Nivel 1: Novato / Superficial | Nivel 2: Intermedio | Nivel 3: Profesional / Riguroso |
| :--- | :--- | :--- | :--- |
| **Estrategia de Testing** | "Probamos manualmente haciendo clics". | Tiene tests unitarios básicos del camino feliz. | Combina guantelete de arquitectura (AST), tests unitarios, cobertura y detector de antipatrones. |
| **Disciplina de Git** | Commits gigantescos sin convención (`update`, `fix`). | Usa conventional commits pero agrupa cambios dispares. | Commits atómicos estrictos con una sola unidad lógica verificada en verde. |

---

## 3. Lista de Chequeo Metacognitiva Final (El Test del Espejo)

Antes de considerar que tu especificación SRS está lista para ser consumida por ingenieros o agentes de IA, pasala por este filtro de honestidad intelectual:

- [ ] **Desaparición del Pensamiento Mágico:** ¿Eliminaste todo adjetivo vago (*"fácil"*, *"rápido"*, *"seguro"*, *"escalable"*) y lo reemplazaste por un número, protocolo o restricción formal?
- [ ] **Sobrevivencia a los Bordes:** ¿Describiste qué pasa cuando la red se corta, la base de datos se satura o la entrada del usuario es maliciosa?
- [ ] **Anti-Bloat:** ¿Revisaste que no haya capas intermedias, interfaces vacías ni componentes pasamanos que solo existen por *"posible uso futuro"*?
- [ ] **Verificabilidad Autónoma:** ¿Un agente autónomo de IA puede ejecutar `pytest`, `test_architecture` y `test_clean_design` y saber exactamente si su trabajo fue aprobado sin pedir opinión humana?

> Si tu documento supera este examen, tu proyecto ha dejado de ser un conjunto de deseos para convertirse en un **verdadero instrumento de ingeniería**.
