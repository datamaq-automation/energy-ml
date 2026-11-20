# Pronóstico diario de viajes en bicicletas públicas

## Qué se predice y por qué

Se estima cuántos viajes de bicicletas públicas comenzarán en cada día. Un pronóstico diario puede servir para explorar la demanda y comparar métodos sencillos con un modelo de aprendizaje automático. Este ejercicio es una evaluación histórica; no constituye un sistema de operación.

## Fuente y licencia

Los datos provienen de [BA Data, conjunto «Bicicletas Públicas»](https://data.buenosaires.gob.ar/dataset/bicicletas-publicas), en particular de los recursos [Recorridos Realizados 2024](https://cdn.buenosaires.gob.ar/datosabiertos/datasets/transporte-y-obras-publicas/bicicletas-publicas/recorridos-realizados-2024.zip) y [Recorridos Realizados 2025](https://cdn.buenosaires.gob.ar/datosabiertos/datasets/transporte-y-obras-publicas/bicicletas-publicas/recorridos-realizados-2025.zip). Para cada viaje se utiliza su identificador y fecha de inicio; los viajes se cuentan por día.

La ficha oficial del conjunto declara la licencia **CC-BY-2.5-AR** en sus [metadatos](https://data.buenosaires.gob.ar/api/3/action/package_show?id=bicicletas-publicas). Los metadatos individuales de los recursos no son uniformes: el recurso 2024 informa `cc-by` y el de 2025 no informa una licencia individual. Por eso aquí se consigna la licencia declarada por la ficha del conjunto, sin inferir una licencia diferente para cada archivo.

**Atribución:** Gobierno de la Ciudad de Buenos Aires, conjunto de datos «Bicicletas Públicas» (BA Data), recorridos realizados de 2024 y 2025.

## Cómo ejecutar desde cero

Desde la raíz del repositorio, con Python 3.10 o superior:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m src.infrastructure.cli.pronosticar_bicis
```

En macOS o Linux, la activación del entorno virtual es `source .venv/bin/activate`; los otros comandos son iguales.

En la primera ejecución, el comando descarga los ZIP oficiales de 2024 y 2025 a `datos/bicis/` y luego ejecuta la preparación y evaluación. Si ya hay ZIP válidos en esa carpeta, los reutiliza. `datos/` está ignorada por Git: los ZIP no se versionan. El comando informa la cobertura y las métricas en la salida; no guarda resultados generados.

## Método de evaluación

Se agregan los viajes por fecha de inicio. Se entrena con muestras utilizables de 2024 y se evalúa cronológicamente, un día a la vez, con las fechas de 2025.

Se comparan:

- **Referencia:** viajes del mismo día de la semana anterior (`t-7`).
- **Random Forest:** regresor con 300 árboles; usa día de la semana, mes y viajes observados en `t-1` y `t-7`.

Para cada fecha objetivo, las variables se construyen solo con información observada antes de esa fecha. El valor real del día objetivo se usa para medir el error, no como entrada. Al avanzar día por día, los rezagos pueden incluir los viajes ya observados de días anteriores de 2025; no se usan datos futuros.

## Resultados

| Método | MAE (viajes/día) | RMSE (viajes/día) |
|---|---:|---:|
| Mismo día de la semana anterior | 2.158,04 | 3.119,80 |
| Random Forest | 1.874,39 | 2.700,51 |

| Cobertura | Resultado |
|---|---:|
| Días evaluados en 2025 | 365 |
| Días de prueba excluidos por falta de rezagos | 0 |
| Días de entrenamiento 2024 excluidos por falta de rezagos | 7 |
| Días de entrenamiento 2024 utilizables | 359 |
| Promedio de viajes por día en 2025 | 8.647,07 |

El promedio se calcula sobre 3.156.182 viajes observados en 365 días. Da una referencia de escala para el MAE, pero no es otra métrica de error.

## Limitaciones

- La evaluación usa un solo año de prueba (2025); el resultado puede cambiar en otros períodos.
- No se incorporan clima, feriados ni eventos que puedan afectar la demanda.
- Es una evaluación retrospectiva con rezagos observados día a día; no demuestra que el modelo sea apto para uso operativo ni que mantenga ese desempeño en producción.
