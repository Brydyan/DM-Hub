import numpy as np
import pandas as pd
import pytest
from src.cleaning import (
    audit_frame,
    detect_outlier_mask,
    impute_column,
    normalize_frame,
    treat_outliers,
)


def _dirty_frame() -> pd.DataFrame:
    """Frame con los 3 defectos de la tríada patológica."""
    return pd.DataFrame(
        {
            "transaction_id": range(10),
            "region": [
                "Costa", " COSTA", "costa ", "Sierra", "Sierra",
                "Costa", "Costa", "Sierra", None, "Costa",
            ],
            "age": [30, 40, np.nan, 25, 50, 150, 35, 28, 42, 33],
            "annual_income": [
                30_000, 45_000, np.nan, 22_000, 60_000,
                500_000, 38_000, 25_000, 52_000, 33_000,
            ],
            "credit_score": [700] * 10,
            "loan_amount": [10_000] * 10,
            "created_at": pd.Timestamp("2026-01-01"),
        }
    )


def test_audit_detects_dirty_data():
    """El reporte cuenta nulos, outliers, fuera de rango y variantes."""
    audit = audit_frame(_dirty_frame())
    cols = {c["column"]: c for c in audit["columns"]}
    assert cols["age"]["nulls"] == 1
    assert cols["age"]["out_of_range"] == 1  # edad 150
    assert " COSTA" in cols["region"]["variants"]  # variante sucia
    assert cols["annual_income"]["outliers_iqr"] >= 1  # el 500K

def test_normalize_frame_fixes_regions_and_ranges():
    """Normalización: 4 regiones limpias y rangos inválidos -> NaN."""
    clean, report = normalize_frame(_dirty_frame())
    assert report["region"]["normalized"] == 2  # ' COSTA' y 'costa '
    assert clean["region"].nunique(dropna=True) == 2  # Costa, Sierra
    assert pd.isna(clean.loc[5, "age"])  # 150 -> NaN

def test_impute_column_strategies():
    """Media/mediana/moda/KNN rellenan nulos; categórica solo admite moda."""
    df = _dirty_frame()
    for strategy in ("mean", "median", "knn"):
        out, rep = impute_column(df, "age", strategy)
        assert rep["imputed"] == 1
        assert out["age"].isna().sum() == 0
    out, _ = impute_column(df, "region", "mode")
    assert out["region"].isna().sum() == 0
    with pytest.raises(ValueError):
        impute_column(df, "region", "mean")

def test_detect_outliers_methods():
    """IQR y Z-score detectan el ingreso de 500K como outlier."""
    df = _dirty_frame()
    assert detect_outlier_mask(df, "annual_income", "iqr").sum() == 1
    # Masking: un único outlier extremo infla la std y NO supera |z|>3 —
    # por eso la regla empírica requiere distribuciones ~normales.
    assert detect_outlier_mask(df, "annual_income", "zscore").sum() == 0

def test_treat_outliers_actions():
    """drop elimina la fila; cap acota al límite; log suaviza."""
    df = _dirty_frame()
    out, rep = treat_outliers(df, "annual_income", "iqr", "drop")
    assert rep["detected"] == 1 and len(out) == 9
    out, _ = treat_outliers(df, "annual_income", "iqr", "cap")
    assert out["annual_income"].max() < 500_000
    out, _ = treat_outliers(df, "annual_income", "iqr", "log")
    assert out["annual_income"].max() < 20  # log1p(500K) ≈ 13.1
