# U2-T3 · Práctica: Limpieza de datos sobre código existente

> **Escenario:** acabas de incorporarte como Ingeniero/a de Datos a un equipo que
> ya tiene un warehouse en producción. Tu primera tarea parecía sencilla:
> implementar el pipeline de limpieza del dataset de crédito. Al abrir el
> repositorio descubres que **alguien ya lo construyó** — y mejor de lo que
> pedía la especificación.
>
> Esta práctica evalúa lo que la industria realmente exige: leer, entender,
> extender y verificar código heredado. No escribir desde cero.

---

## 1. Antecedente

### 1.1 El sistema existente

- **Warehouse:** PostgreSQL en Docker (`enterprise_warehouse`).
- **Tabla origen (cruda):** `customer_credit_transactions` — contiene los
  defectos de la "tríada patológica": nulos, inconsistencias y outliers.
- **Tabla destino (staging):** `customer_credit_clean`.
- **Módulo de acceso:** `src.db_connector` expone `get_database_engine()` y
  `extract_raw_data(query)`.
- **Módulo de limpieza:** `apps/analytics/src/cleaning.py`.
- **API:** `src/api.py` expone endpoints de auditoría, preview y ejecución.
- **Tests:** `tests/test_cleaning.py` (5 pruebas, todas en verde).

### 1.2 La especificación que se te entregó

| Función | Firma especificada | Requisitos |
|---|---|---|
| `normalize_frame(df)` | → `pd.DataFrame` | `region`: strip + Title Case. `age` fuera de [18, 100] → NaN |
| `impute_column(df, column, strategy)` | → `pd.DataFrame` | `mean`, `median`, `mode` (categóricas), `knn` (`KNNImputer`, `n_neighbors=5`) |
| `treat_outliers(df, column, method, action)` | → `pd.DataFrame` | Detección `zscore` (3σ) e `iqr` (1.5·IQR). Acción `cap` |
| `run_cleaning_pipeline()` | → `dict` | Orquesta todo y escribe `customer_credit_clean` con `to_sql(if_exists="replace", index=False)` |

### 1.3 Lo que encontraste en el repositorio

El módulo **ya implementa toda la especificación**, pero con un diseño
diferente — y más robusto:

| Aspecto | Spec básica | Implementación del repo |
|---|---|---|
| Retorno de funciones | Solo `pd.DataFrame` | `tuple[pd.DataFrame, dict]` — DataFrame **+ reporte** de lo que hizo cada paso |
| Rangos de negocio | Solo `age` ∈ [18, 100] | `VALID_RANGES`: las 4 numéricas (`age`, `annual_income`, `credit_score`, `loan_amount`) |
| Pasos del pipeline | Normalizar → imputar → outliers | + **deduplicación** y **auditoría final** del resultado |
| Acciones de outliers | `cap` | `cap`, `drop`, `log` |
| Extras | — | `audit_frame()`, `detect_outlier_mask()`, endpoints preview en la API, suite de tests |

### 1.4 Evidencia de ejecución

El pipeline ya se corrió contra el warehouse real:

```
Pipeline completado: 2017 filas crudas -> 2009 filas en 'customer_credit_clean'
  - normalización: 75 regiones corregidas, 7 valores fuera de rango -> NaN
  - deduplicación: 8 filas eliminadas
  - imputación mediana: age=63, annual_income=83, credit_score=4 nulos rellenados
  - capping IQR: 89 outliers en annual_income, 110 en loan_amount
```

Cada paso **reporta qué hizo y cómo cambiaron los estadísticos**. Esa es la
diferencia entre un script de tarea y un pipeline de producción.

---

## 2. El giro de la práctica

En ingeniería real **casi nunca empiezas de cero**. Heredas código de otro
equipo, de otro proyecto, o de tu versión de hace seis meses. El 80% del
trabajo de un ingeniero de datos es:

1. **Leer** código que no escribiste.
2. **Entender** por qué está diseñado así antes de juzgarlo.
3. **Verificar** que funciona (tests, ejecución, datos reales).
4. **Extender** sin romper lo que ya consumen otros.

Por eso la asignación cambia: no se trata de demostrar que puedes escribir
`fillna(df.median())`, sino de demostrar que puedes **trabajar sobre un
sistema vivo**.

---

## 3. Asignación

### Parte A — Reimplementación comparativa (obligatoria)

Implementa la spec básica (sección 1.2) en tu propio archivo:

```
apps/analytics/scripts/cleaning_<tu_apellido>.py
```

Reglas:

- Usa las firmas simples de la spec (devuelven solo `pd.DataFrame`).
- Puedes importar `extract_raw_data` y `get_database_engine` de `src.db_connector`.
- Ejecuta tu pipeline sobre la tabla cruda y escribe tu resultado en una tabla
  propia: `customer_credit_clean_<apellido>`.

**Entregable:** un análisis comparativo de tu tabla vs `customer_credit_clean`:

- ¿Coinciden las filas? ¿Por qué difieren?
- ¿Qué hace la versión del repo que la tuya no hace? (pista: deduplicación,
  rangos extra, reportes)
- ¿Qué pasaría en producción si tu versión hubiera reemplazado a la otra?

### Parte B — Elige UNA de las siguientes

**B1. Extensión del módulo (perfil ingeniería).** Implementa una mejora real
sobre `src/cleaning.py`, con su test:

- Nuevo método de detección `mad` (*Median Absolute Deviation*), más robusto
  que zscore ante outliers extremos.
- Nueva regla de negocio: `region` fuera de la whitelist
  `{Costa, Sierra, Oriente, Insular}` → NaN.
- Parametrizar `run_cleaning_pipeline(strategy=..., action=...)` en lugar de
  valores fijos.
- **Importante:** los 5 tests existentes deben seguir pasando. Romper un
  contrato público sin justificarlo es una regresión.

**B2. Bug hunting (perfil calidad).** El código tiene casos borde que los
tests no cubren. Encuentra al menos uno, escribe el test que lo **expone**,
y arréglalo. Pistas (no son las únicas):

- `KNNImputer` se degrada si una columna es 100% nula.
- `series.mode().iloc[0]` lanza `IndexError` si `region` llega toda vacía.
- ¿Qué pasa con `treat_outliers(action="drop")` cuando la columna tiene NaN?

**B3. Reporte de calidad (perfil análisis).** Usa los endpoints de la API
para auditar la tabla cruda vs la limpia y experimentar con estrategias
sin tocar la base de datos:

```
GET  /api/cleaning/audit?target=raw        # defectos del origen
GET  /api/cleaning/audit?target=clean      # resultado del pipeline
GET  /api/cleaning/preview/imputation?column=age&strategy=knn
GET  /api/cleaning/preview/outliers?column=annual_income&method=zscore&action=log
POST /api/cleaning/run
```

Entrega un informe comparando: mediana vs media vs KNN en `age` e
`annual_income` (¿cuál distorsiona menos la distribución?), e IQR vs zscore
en la detección (¿por qué zscore "no ve" el outlier de 500K? Investiga el
efecto *masking*).

### Entregables

1. Código (`scripts/cleaning_<apellido>.py` y/o modificaciones a `src/`).
2. Documento de análisis (comparativa de la Parte A + hallazgos de B).
3. Los tests deben pasar: `docker compose exec analytics python -m pytest tests/ -v`.

---

## 4. Tips: qué hace un ingeniero cuando encuentra código existente

Esto es lo que separa a un programador de un ingeniero. Cuando aterrices en
un codebase que no escribiste:

### Antes de tocar nada

- **Lee antes de escribir.** El código existente es la documentación más
  honesta del sistema. Entiende *qué* hace y *por qué* antes de cambiarlo.
- **Ejecuta los tests primero.** Si están en verde, tienes una red de
  seguridad. Si están en rojo, ya encontraste tu primer problema.
- **Mapea los consumidores.** ¿Quién importa este módulo? En este repo,
  `api.py` y `test_cleaning.py` dependen de las firmas actuales. Cambiar el
  retorno de una función "para que quede más simple" rompe la API en
  producción. Usa grep/búsqueda de imports *antes* de refactorizar.
- **Haz arqueología de git.** `git log` y `git blame` responden "¿quién
  escribió esto y en qué contexto?". Un diseño extraño suele tener una razón
  olvidada — o un bug disfrazado de intención.

### Al evaluar el diseño

- **Distingue "diferente" de "incorrecto".** Que el código no use tu estilo
  no lo hace malo. Pregunta: ¿qué problema resuelve esta complejidad extra?
  Aquí, devolver `(DataFrame, reporte)` existe porque la API muestra un
  preview al usuario — sin el reporte, ese endpoint es imposible.
- **Un pipeline que no reporta lo que hizo es una caja negra.** La
  observabilidad (cuántos nulos imputó, cuántos outliers acotó) no es un
  lujo: es cómo detectas que los datos de hoy llegaron distintos a los de
  ayer.
- **Los casos borde viven en los extremos.** Columna 100% nula, frame vacío,
  `std = 0`. Pregúntate siempre "¿y si llega lo peor?".

### Al modificar

- **Extiende, no rompas.** Las firmas públicas son contratos. Agrega
  parámetros con defaults en vez de cambiar retornos.
- **Test antes que fix.** El flujo correcto: escribe el test que falla →
  arregla → el test pasa. Si arreglas sin test, no puedes demostrar que el
  bug existió ni que no volverá.
- **Sigue las convenciones del proyecto.** Docstrings en español, type
  hints, nombres de constantes en MAYÚSCULAS, scripts con `main()` +
  `if __name__ == "__main__"`. La consistencia es una forma de respeto al
  próximo lector.
- **Verifica con datos reales.** "Funciona en mi máquina" no cuenta: corre
  el pipeline contra el warehouse y mira el resultado en la tabla destino.

### Mentalidad

- **No reescribas por ego.** Reescribir código que funciona para "hacerlo a
  tu manera" destruye conocimiento acumulado y arriesga regresiones. La
  mejora se gana aportando, no imponiendo.
- **El código que no escribiste también es tu responsabilidad.** Una vez que
  lo tocas, lo mantienes.

---

## 5. Criterios de evaluación

| Criterio | Peso |
|---|---|
| Parte A: pipeline propio funciona y produce tabla comparable | 30% |
| Parte A: análisis comparativo con argumentación técnica | 25% |
| Parte B: extensión/bug/informe según opción elegida | 30% |
| Tests en verde y respeto a las convenciones del proyecto | 15% |

---

## 6. Comandos de referencia

```bash
# Levantar el entorno
docker compose up -d

# Ejecutar el pipeline existente
docker compose exec analytics python -m src.cleaning

# Correr los tests
docker compose exec analytics python -m pytest tests/ -v

# Sembrar más datos sintéticos (si necesitas volumen)
docker compose exec analytics python scripts/seed_synthetic.py --n 2000

# API (con el contenedor corriendo): http://localhost:8000/docs
```
