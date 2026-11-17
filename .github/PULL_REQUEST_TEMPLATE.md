> **Antes de crear el PR:** verificá que la **base sea `develop`** (no `main`). Leé `CONTRIBUTING.md`.

## Qué cambia

<!-- Explicá en pocas líneas qué hace este PR y por qué. -->

## Issue relacionado

<!-- `Closes #N` si lo resuelve completo, `Refs #N` si es parcial. -->

## Cómo probarlo

<!-- Comandos exactos para reproducir tu resultado. Si necesita un dataset, indicá de dónde se descarga. -->

```bash

```

## Resultados

<!-- Si hay un modelo: tabla de métricas (línea base y modelos) y qué significa. -->

## Limitaciones y lo que no sé

<!-- ¿Qué no funciona o qué no pudiste comprobar? Es la parte más valiosa. -->

## Checklist del repo

- [ ] `./run.sh lint` y `./run.sh test` pasan en mi máquina
- [ ] `python tests/test_architecture.py` pasa (cabecera de ruta en cada `.py`, tipos, imports absolutos, sin `print`)
- [ ] Las librerías nuevas están en `requirements.txt` y `pyproject.toml`
- [ ] No subí datasets pesados, datos personales ni credenciales
- [ ] La base de este PR es `develop`

## Checklist de ML

- [ ] No hay fuga de datos: ninguna variable usa información que no existiría al predecir
- [ ] Si son series de tiempo, el split es temporal
- [ ] Imputé y escalé usando solo datos de entrenamiento
- [ ] Comparé contra una línea base y expliqué por qué elegí esa
- [ ] Reporté métricas adecuadas al problema y mencioné las limitaciones

## Uso de IA

<!-- Completá aunque no hayas usado IA ("No usé"). -->

- **Herramienta usada:**
- **Qué decidí yo:**
- **Qué verifiqué o descarté de lo que me devolvió:**
- **Algo que la IA dijo y que no pude comprobar:**
