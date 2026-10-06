"""API REST ligera para exponer los datos del warehouse al frontend.

Alineada con la Unidad 4, Tema 4 del silabo (Integración con el Ecosistema
Frontend): APIs ligeras consumidas desde interfaces modernas (React + Vite).

Los endpoints se apoyan en `src.db_connector` para reutilizar el motor
SQLAlchemy y el pool de conexiones ya configurados.
"""
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import text

from src.cleaning import (
    CLEAN_TABLE,
    RAW_TABLE,
    IMPUTATION_STRATEGIES,
    NUMERIC_COLS,
    OUTLIER_ACTIONS,
    DETECTION_METHODS,
    audit_frame,
    impute_column,
    load_table,
    normalize_frame,
    run_cleaning_pipeline,
    treat_outliers,
)
from src.db_connector import extract_raw_data, get_database_engine
from src.eda import (
    build_eda_figure,
    filter_outliers,
    generate_server_metrics,
)


class TransactionIn(BaseModel):
    """Esquema de entrada para crear/actualizar una transacción de crédito."""

    customer_id: str = Field(min_length=1, max_length=15)
    age: Optional[int] = Field(default=None, ge=18, le=120)
    annual_income: Optional[float] = Field(default=None, ge=0)
    credit_score: Optional[int] = Field(default=None, ge=300, le=900)
    loan_amount: Optional[float] = Field(default=None, ge=0)
    has_defaulted: bool = False
    region: str = Field(min_length=1, max_length=50)

app = FastAPI(
    title="Data Mining Hub API",
    description="Expone los datos crudos del warehouse y agregados analíticos para el frontend.",
    version="0.1.0",
)

# El frontend de Vite corre en localhost:5173 desde el navegador del host
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    """Verifica conectividad con PostgreSQL (equivalente al SELECT 1 de la Demo 1)."""
    engine = get_database_engine()
    with engine.connect() as connection:
        ok = connection.execute(text("SELECT 1")).scalar() == 1
    return {"status": "ok" if ok else "error", "database": "enterprise_warehouse"}


@app.get("/api/transactions")
def list_transactions(
    region: Optional[str] = None,
    order_by_income: bool = False,
    limit: int = Query(default=100, ge=1, le=5000),
) -> list[dict]:
    """Devuelve transacciones con filtro opcional por región y orden por ingreso."""
    query = "SELECT * FROM customer_credit_transactions"
    params: dict = {"limit": limit}
    if region:
        query += " WHERE region = :region"
        params["region"] = region
    order_col = "annual_income DESC" if order_by_income else "transaction_id"
    query += f" ORDER BY {order_col} LIMIT :limit"
    df = extract_raw_data(query, params=params)
    return df.to_dict(orient="records")


@app.post("/api/transactions", status_code=201)
def create_transaction(payload: TransactionIn) -> dict:
    """Inserta una transacción nueva (equivalente a un INSERT parametrizado)."""
    engine = get_database_engine()
    with engine.begin() as connection:
        result = connection.execute(
            text(
                """
                INSERT INTO customer_credit_transactions
                    (customer_id, age, annual_income, credit_score,
                     loan_amount, has_defaulted, region)
                VALUES
                    (:customer_id, :age, :annual_income, :credit_score,
                     :loan_amount, :has_defaulted, :region)
                RETURNING transaction_id
                """
            ),
            payload.model_dump(),
        )
        new_id = result.scalar_one()
    return {"transaction_id": new_id, **payload.model_dump()}


@app.put("/api/transactions/{transaction_id}")
def update_transaction(transaction_id: int, payload: TransactionIn) -> dict:
    """Actualiza una transacción existente por su clave primaria."""
    engine = get_database_engine()
    with engine.begin() as connection:
        result = connection.execute(
            text(
                """
                UPDATE customer_credit_transactions
                SET customer_id = :customer_id, age = :age,
                    annual_income = :annual_income, credit_score = :credit_score,
                    loan_amount = :loan_amount, has_defaulted = :has_defaulted,
                    region = :region
                WHERE transaction_id = :transaction_id
                """
            ),
            {**payload.model_dump(), "transaction_id": transaction_id},
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Transacción no encontrada")
    return {"transaction_id": transaction_id, **payload.model_dump()}


@app.delete("/api/transactions/{transaction_id}", status_code=204)
def delete_transaction(transaction_id: int) -> None:
    """Elimina una transacción por su clave primaria."""
    engine = get_database_engine()
    with engine.begin() as connection:
        result = connection.execute(
            text(
                "DELETE FROM customer_credit_transactions "
                "WHERE transaction_id = :transaction_id"
            ),
            {"transaction_id": transaction_id},
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Transacción no encontrada")


@app.get("/api/stats/overview")
def stats_overview() -> dict:
    """KPIs generales: total de clientes, regiones y tasa de default."""
    df = extract_raw_data(
        """
        SELECT
            COUNT(*) AS total_customers,
            COUNT(DISTINCT region) AS total_regions,
            ROUND(AVG(CASE WHEN has_defaulted THEN 1.0 ELSE 0.0 END) * 100, 1)
                AS default_rate_pct
        FROM customer_credit_transactions
        """
    )
    return df.to_dict(orient="records")[0]


@app.get("/api/stats/by-region")
def stats_by_region() -> list[dict]:
    """Conteo de clientes por región (Ejercicio 1 de la hoja de trabajo)."""
    df = extract_raw_data(
        """
        SELECT region, COUNT(*) AS total
        FROM customer_credit_transactions
        GROUP BY region
        ORDER BY total DESC
        """
    )
    return df.to_dict(orient="records")


@app.get("/api/stats/risk-profile")
def stats_risk_profile(
    threshold: int = Query(default=650, ge=300, le=900),
) -> list[dict]:
    """Clientes con credit_score por debajo del umbral (Ejercicio 2)."""
    df = extract_raw_data(
        """
        SELECT customer_id, credit_score, has_defaulted
        FROM customer_credit_transactions
        WHERE credit_score < :threshold
        ORDER BY credit_score
        """,
        params={"threshold": threshold},
    )
    return df.to_dict(orient="records")


@app.get("/api/stats/summary")
def stats_summary() -> list[dict]:
    """Estadísticas descriptivas de las variables numéricas."""
    df = extract_raw_data(
        "SELECT age, annual_income, credit_score, loan_amount FROM customer_credit_transactions"
    )
    desc = df.describe().T.reset_index(names="feature")
    return desc[["feature", "mean", "std", "min", "max"]].to_dict(orient="records")


# ── U2-T2: Análisis Exploratorio de Datos (dataset de métricas de servidor) ──


@app.get("/api/eda/metrics")
def eda_metrics() -> list[dict]:
    """Devuelve el dataset sintético de métricas del servidor (1000 filas)."""
    df = generate_server_metrics()
    df["fecha"] = df["fecha"].astype(str)
    return df.round(3).to_dict(orient="records")


@app.get("/api/eda/summary")
def eda_summary() -> list[dict]:
    """Estadísticas descriptivas del dataset de métricas del servidor."""
    df = generate_server_metrics()
    desc = df[["tiempo_respuesta", "usuarios_concurrentes"]].describe().T
    desc = desc.reset_index(names="feature")
    return desc[["feature", "mean", "std", "min", "max"]].round(3).to_dict(
        orient="records"
    )


@app.get("/api/eda/outliers")
def eda_outliers(
    threshold: float = Query(default=250.0, ge=0),
) -> list[dict]:
    """Reto 3: filas con tiempo_respuesta por encima del umbral."""
    df = filter_outliers(generate_server_metrics(), threshold)
    df["fecha"] = df["fecha"].astype(str)
    return df.round(3).to_dict(orient="records")


@app.get("/api/eda/figure")
def eda_figure(
    bins: int = Query(default=30, ge=1, le=500),
    panel_b: str = Query(default="density", pattern="^(density|scatter)$"),
    hue_server: bool = False,
) -> Response:
    """Figura 2x2 del notebook renderizada a PNG.

    Parametrizable para los retos de la sesión práctica:
    bins (Reto 1), panel_b density/scatter (Reto 2), hue_server (Reto 4).
    """
    png = build_eda_figure(bins=bins, panel_b=panel_b, hue_server=hue_server)
    return Response(content=png, media_type="image/png")


# ── U2-T3: Limpieza y calidad de datos (crudo -> tabla limpia) ────────────────


def _load_or_404(target: str):
    """Carga la tabla cruda o la limpia; 404 si la limpia aún no existe."""
    table = CLEAN_TABLE if target == "clean" else RAW_TABLE
    try:
        return load_table(table)
    except Exception:
        raise HTTPException(
            status_code=404,
            detail=f"Tabla '{table}' no existe: ejecuta el pipeline primero",
        )


@app.get("/api/cleaning/audit")
def cleaning_audit(
    target: str = Query(default="raw", pattern="^(raw|clean)$"),
) -> dict:
    """Reporte de calidad: nulos, duplicados, inconsistencias y outliers."""
    return audit_frame(_load_or_404(target))


@app.get("/api/cleaning/preview/imputation")
def cleaning_preview_imputation(
    column: str = Query(pattern="^(age|annual_income|credit_score|loan_amount|region)$"),
    strategy: str = Query(default="median", pattern="^(mean|median|mode|knn)$"),
) -> dict:
    """Preview de imputación: estadísticas antes/después sin tocar la DB."""
    df = _load_or_404("raw")
    try:
        _, report = impute_column(df, column, strategy)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {"column": column, "strategy": strategy, **report}


@app.get("/api/cleaning/preview/outliers")
def cleaning_preview_outliers(
    column: str = Query(default="annual_income"),
    method: str = Query(default="iqr", pattern="^(iqr|zscore)$"),
    action: str = Query(default="cap", pattern="^(drop|cap|log)$"),
) -> dict:
    """Preview del tratamiento de outliers sobre una columna numérica."""
    df = _load_or_404("raw")
    if column not in NUMERIC_COLS:
        raise HTTPException(422, f"'{column}' no es numérica")
    try:
        _, report = treat_outliers(df, column, method, action)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return {"column": column, "method": method, "action": action, **report}


@app.get("/api/cleaning/preview/normalization")
def cleaning_preview_normalization() -> dict:
    """Preview de la normalización de inconsistencias (regiones, rangos)."""
    _, report = normalize_frame(_load_or_404("raw"))
    return report


@app.post("/api/cleaning/run")
def cleaning_run() -> dict:
    """Ejecuta el pipeline raw -> clean y materializa customer_credit_clean."""
    return run_cleaning_pipeline()


@app.get("/api/cleaning/rows")
def cleaning_rows(
    target: str = Query(default="clean", pattern="^(raw|clean)$"),
    limit: int = Query(default=500, ge=1, le=5000),
) -> list[dict]:
    """Muestra las filas de la tabla elegida (para inspeccionar el resultado)."""
    df = _load_or_404(target).head(limit)
    df["created_at"] = df["created_at"].astype(str)
    return df.to_dict(orient="records")
