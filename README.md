# Minería de Datos

Stack de apoyo para la cátedra de Minería de Datos: PostgreSQL + API de analítica
(FastAPI) + frontend (React/Vite), todo orquestado con Docker Compose.

## Servicios

| Servicio      | Contenedor     | Puerto  | Descripción                          |
| ------------- | -------------- | ------- | ------------------------------------ |
| `postgres_db` | `dm_postgres2` | 5437    | PostgreSQL 16 con `enterprise_warehouse` |
| `analytics`   | `dm_analytics2`| 8000    | API FastAPI (EDA, limpieza, pipeline)|
| `web`         | `dm_web2`      | 5173    | Frontend React/Vite                  |

## Puesta en marcha (después de clonar)

```bash
git clone https://github.com/software-cemm/mineria
cd mineria

# Construir imágenes y levantar los tres servicios
docker compose up --build -d
```

Al primer arranque, `init-db/01_init.sql` crea la tabla
`customer_credit_transactions` y carga 9 registros base.

Verificar que todo esté arriba:

```bash
docker compose ps
```

- API: http://localhost:8000
- Frontend: http://localhost:5173
- Postgres: `localhost:5437` (user `dm_user`, pass `dm_password`, db `enterprise_warehouse`)

## Seeders

El script `apps/analytics/scripts/seed_synthetic.py` puebla
`customer_credit_transactions` con datos sintéticos e inyecta defectos
deliberados (nulos, outliers, duplicados, categorías inconsistentes) para los
ejercicios de EDA y limpieza.

```bash
# Opción 1: por nombre de servicio (recomendado)
docker compose exec analytics python scripts/seed_synthetic.py --n 2000

# Opción 2: por nombre de contenedor
docker exec dm_analytics2 python scripts/seed_synthetic.py --n 2000
```

Parámetros: `--n` registros base (default 2000), `--seed` semilla RNG
(default 42). El script es reejecutable: cada corrida agrega un lote nuevo.

## Actualización de contenedores

### Código Python / frontend (hot reload)

`analytics` corre uvicorn con `--reload` y `web` monta el código con volúmenes,
así que los cambios en `apps/analytics` y `apps/web` se reflejan sin rebuild.

Si el cambio no se refleja:

```bash
docker compose restart analytics web
```

### Cambios en dependencias o Dockerfile

```bash
# Reconstruir solo un servicio
docker compose up -d --build analytics

# Reconstruir todo
docker compose up -d --build
```

### Cambios en docker-compose.yml

```bash
docker compose up -d   # recrea solo los servicios que cambiaron
```

### Cambios en init-db (01_init.sql)

Los scripts de `init-db/` solo corren cuando el volumen está vacío. Para
reaplicarlos hay que reiniciar la base desde cero (**borra todos los datos**):

```bash
docker compose down -v
docker compose up -d --build
docker compose exec analytics python scripts/seed_synthetic.py --n 2000
```

## Comandos útiles

```bash
# Logs en vivo
docker compose logs -f analytics
docker compose logs -f postgres_db

# Shell dentro del contenedor de analítica
docker compose exec analytics bash

# psql dentro del contenedor de Postgres
docker exec -it dm_postgres2 psql -U dm_user -d enterprise_warehouse

# Detener todo (conserva datos)
docker compose down

# Detener todo y borrar el volumen de datos
docker compose down -v
```

## Estructura

```
mineria/
├── apps/
│   ├── analytics/          # API FastAPI + scripts
│   │   ├── scripts/seed_synthetic.py
│   │   └── src/            # api.py, eda.py, cleaning.py, pipeline.py, db_connector.py
│   └── web/                # Frontend React/Vite
├── init-db/01_init.sql     # Esquema y datos base
└── docker-compose.yml
```
