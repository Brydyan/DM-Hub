"""U2-T3: Limpieza y calidad de datos sobre el dataset de crédito.

Implementa la "tríada patológica" de la diapositiva del tema:

* **Valores faltantes**: imputación por media, mediana, moda y KNN
  (`sklearn.impute.KNNImputer`).
* **Inconsistencias**: normalización de categóricas (regiones sucias con
  espacios/mayúsculas) y valores fuera de rango de negocio.
* **Outliers**: detección por Z-score (|z| > 3) e IQR, y tratamiento por
  eliminación, acotamiento (capping) o transformación logarítmica.

`run_cleaning_pipeline()` materializa el resultado en la tabla
``customer_credit_clean``, dejando la tabla cruda intacta — el patrón
ETL real: el origen no se destruye, el pipeline escribe a staging.
"""
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.impute import KNNImputer

from src.db_connector import extract_raw_data, get_database_engine

RAW_TABLE = "customer_credit_transactions"
CLEAN_TABLE = "customer_credit_clean"

NUMERIC_COLS = ["age", "annual_income", "credit_score", "loan_amount"]

# Rangos válidos de negocio: lo que esté fuera se convierte en NaN
# (inconsistencia -> faltante -> imputación).
VALID_RANGES = {
    "age": (18, 100),
    "annual_income": (0, 300_000),
    "credit_score": (300, 850),
    "loan_amount": (0, 100_000),
}

IMPUTATION_STRATEGIES = ("mean", "median", "mode", "knn")
DETECTION_METHODS = ("iqr", "zscore")
OUTLIER_ACTIONS = ("drop", "cap", "log")


def load_table(table: str = RAW_TABLE) -> pd.DataFrame:
    """Carga la tabla completa desde PostgreSQL a un DataFrame."""
    return extract_raw_data(f"SELECT * FROM {table} ORDER BY transaction_id")


def _column_stats(series: pd.Series) -> dict:
    """Estadísticas compactas de una columna (numérica o categórica)."""
    s = series.dropna()
    if not pd.api.types.is_numeric_dtype(series):
        return {
            "nulls": int(series.isna().sum()),
            "unique": int(series.nunique(dropna=True)),
        }
    return {
        "nulls": int(series.isna().sum()),
        "mean": round(float(s.mean()), 2) if len(s) else None,
        "median": round(float(s.median()), 2) if len(s) else None,
        "std": round(float(s.std()), 2) if len(s) else None,
        "min": round(float(s.min()), 2) if len(s) else None,
        "max": round(float(s.max()), 2) if len(s) else None,
    }


def audit_frame(df: pd.DataFrame) -> dict:
    """Reporte de calidad de datos: nulos, duplicados, inconsistencias
    y outliers potenciales por columna."""
    columns = []
    for col in df.columns:
        entry = {
            "column": col,
            "dtype": str(df[col].dtype),
            "nulls": int(df[col].isna().sum()),
            "null_pct": round(float(df[col].isna().mean() * 100), 2),
            "unique": int(df[col].nunique(dropna=True)),
        }
        if col in NUMERIC_COLS:
            entry["stats"] = _column_stats(df[col])
            entry["outliers_iqr"] = int(
                detect_outlier_mask(df, col, "iqr").sum()
            )
            lo, hi = VALID_RANGES[col]
            valid = df[col].dropna()
            entry["out_of_range"] = int(
                ((valid < lo) | (valid > hi)).sum()
            )
        if col == "region":
            entry["variants"] = (
                df[col].fillna("(nulo)").value_counts().to_dict()
            )
        columns.append(entry)

    return {
        "rows": int(len(df)),
        "duplicates": int(
            df.duplicated(subset=_dedup_columns(df)).sum()
        ),
        "columns": columns,
    }


def _dedup_columns(df: pd.DataFrame) -> list[str]:
    """Columnas relevantes para deduplicar: excluye PK y timestamps."""
    return [
        c
        for c in df.columns
        if c not in ("transaction_id", "created_at")
    ]


def normalize_frame(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Estandariza inconsistencias: regiones y rangos de negocio.

    Devuelve el frame corregido y un reporte de cuántos valores
    se normalizaron o convirtieron a NaN.
    """
    out = df.copy()
    report: dict = {"region": {}, "range_violations": {}}

    if "region" in out.columns:
        before = out["region"].copy()
        out["region"] = out["region"].astype("string").str.strip().str.title()
        changed = int((before != out["region"]).sum())
        report["region"] = {
            "normalized": changed,
            "variants_after": out["region"].fillna("(nulo)")
            .value_counts()
            .to_dict(),
        }

    for col, (lo, hi) in VALID_RANGES.items():
        if col not in out.columns:
            continue
        invalid = out[col].notna() & ((out[col] < lo) | (out[col] > hi))
        report["range_violations"][col] = int(invalid.sum())
        out.loc[invalid, col] = np.nan

    return out, report


def impute_column(
    df: pd.DataFrame, column: str, strategy: str
) -> tuple[pd.DataFrame, dict]:
    """Imputa los NaN de `column` sin mutar el frame original.

    Estrategias: ``mean``, ``median``, ``mode`` y ``knn`` (KNNImputer
    sobre las columnas numéricas — imputación algorítmica avanzada).
    """
    if strategy not in IMPUTATION_STRATEGIES:
        raise ValueError(f"Estrategia no soportada: {strategy}")
    numeric = pd.api.types.is_numeric_dtype(df[column])
    if not numeric and strategy != "mode":
        raise ValueError(
            f"La columna '{column}' es categórica: solo admite 'mode'"
        )
    out = df.copy()
    series = out[column]
    imputed = int(series.isna().sum())
    before = _column_stats(series)

    if strategy == "knn":
        numeric = out[NUMERIC_COLS]
        out[NUMERIC_COLS] = KNNImputer(n_neighbors=5).fit_transform(numeric)
    elif strategy == "mode":
        out[column] = series.fillna(series.mode(dropna=True).iloc[0])
    elif strategy == "median":
        out[column] = series.fillna(series.median())
    else:  # mean
        out[column] = series.fillna(series.mean())

    return out, {
        "imputed": imputed,
        "before": before,
        "after": _column_stats(out[column]),
    }


def detect_outlier_mask(
    df: pd.DataFrame, column: str, method: str
) -> pd.Series:
    """Máscara booleana de outliers: ``iqr`` (1.5·IQR) o ``zscore`` (|z|>3)."""
    s = df[column].dropna()
    if method == "zscore":
        std = s.std()
        if std == 0 or pd.isna(std):
            return pd.Series(False, index=df.index)
        z = (df[column] - s.mean()) / std
        return z.abs() > 3
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    return (df[column] < q1 - 1.5 * iqr) | (df[column] > q3 + 1.5 * iqr)


def treat_outliers(
    df: pd.DataFrame, column: str, method: str, action: str
) -> tuple[pd.DataFrame, dict]:
    """Aplica un tratamiento de outliers y reporta su efecto.

    Acciones: ``drop`` (eliminar filas), ``cap`` (acotar al límite
    del criterio) y ``log`` (transformación logarítmica suavizada).
    """
    if method not in DETECTION_METHODS or action not in OUTLIER_ACTIONS:
        raise ValueError("Método o acción de outliers no soportada")
    mask = detect_outlier_mask(df, column, method)
    detected = int(mask.sum())
    before = _column_stats(df[column])
    out = df.copy()

    if action == "drop":
        out = out.loc[~mask]
    elif action == "cap":
        s = df[column].dropna()
        if method == "zscore":
            lo, hi = s.mean() - 3 * s.std(), s.mean() + 3 * s.std()
        else:
            q1, q3, iqr = s.quantile(0.25), s.quantile(0.75), (
                s.quantile(0.75) - s.quantile(0.25)
            )
            lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        out[column] = out[column].clip(lower=lo, upper=hi)
    else:  # log: solo valores positivos (log1p protege ceros)
        out[column] = np.where(out[column] > 0, np.log1p(out[column]), np.nan)

    return out, {
        "detected": detected,
        "before": before,
        "after": _column_stats(out[column]),
        "rows_after": int(len(out)),
    }


def run_cleaning_pipeline() -> dict:
    """Ejecuta el pipeline completo raw -> clean y escribe CLEAN_TABLE.

    Pasos (documentados para la clase):
      1. Normalización de inconsistencias (regiones, rangos inválidos).
      2. Eliminación de duplicados exactos.
      3. Imputación por mediana en numéricas (robusta ante outliers)
         y por moda en `region`.
      4. Acotamiento (capping IQR) de outliers en ingresos y préstamos.
    """
    raw = load_table(RAW_TABLE)
    steps = []

    clean, report = normalize_frame(raw)
    steps.append({"step": "normalización", "detail": report})

    dup = clean.duplicated(subset=_dedup_columns(clean))
    clean = clean.loc[~dup]
    steps.append({"step": "deduplicación", "detail": {"removed": int(dup.sum())}})

    for col in NUMERIC_COLS:
        clean, rep = impute_column(clean, col, "median")
        steps.append({"step": f"imputación mediana `{col}`", "detail": rep})
    clean, rep = impute_column(clean, "region", "mode")
    steps.append({"step": "imputación moda `region`", "detail": rep})

    for col in ("annual_income", "loan_amount"):
        clean, rep = treat_outliers(clean, col, "iqr", "cap")
        steps.append({"step": f"capping IQR `{col}`", "detail": rep})

    engine = get_database_engine()
    clean.to_sql(CLEAN_TABLE, engine, if_exists="replace", index=False)

    return {
        "clean_table": CLEAN_TABLE,
        "rows_in": int(len(raw)),
        "rows_out": int(len(clean)),
        "steps": steps,
        "audit_clean": audit_frame(clean),
    }


def main() -> None:
    """Ejecuta el pipeline completo e imprime el resumen por pasos.

    Uso (desde el host, contra el contenedor):
        docker compose exec analytics python -m src.cleaning
    """
    summary = run_cleaning_pipeline()
    print(
        f"Pipeline completado: {summary['rows_in']} filas crudas "
        f"-> {summary['rows_out']} filas en '{summary['clean_table']}'"
    )
    for step in summary["steps"]:
        print(f"  - {step['step']}: {step['detail']}")


if __name__ == "__main__":
    main()
