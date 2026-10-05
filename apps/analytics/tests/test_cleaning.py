"""Pruebas unitarias e integrales para el módulo de limpieza y calidad de datos."""
import numpy as np
import pandas as pd
import pytest
from sqlalchemy import text

from src.cleaning import (
    clean_inconsistencies,
    handle_outliers,
    impute_column,
    run_cleaning_pipeline,
)
from src.db_connector import extract_raw_data, get_database_engine


@pytest.fixture
def sample_dirty_data() -> pd.DataFrame:
    """Fixture con inconsistencias, nulos y valores atípicos representativos."""
    return pd.DataFrame(
        {
            "customer_id": [f"CUST-{i}" for i in range(1, 11)],
            "age": [34, 45, np.nan, 29, 120, 15, 41, 60, 38, 50],
            "annual_income": [
                45000.0,
                82000.0,
                15000.0,
                32000.0,
                np.nan,
                18500.0,
                62000.0,
                95000.0,
                51000.0,
                500000.0,  # Outlier
            ],
            "credit_score": [710, 680, 520, 615, 790, 580, 740, np.nan, 645, 700],
            "loan_amount": [
                12000.0,
                25000.0,
                5000.0,
                8500.0,
                40000.0,
                3500.0,
                18000.0,
                15000.0,
                11000.0,
                200000.0,  # Outlier
            ],
            "region": [
                "  costa  ",
                "Sierra",
                "Costa",
                " oriente ",
                "sierra",
                "Costa",
                np.nan,
                "Insular",
                "sierra ",
                "Costa",
            ],
        }
    )


def test_clean_inconsistencies_region(sample_dirty_data: pd.DataFrame):
    """Valida strip y Title Case en la columna 'region'."""
    df_result = clean_inconsistencies(sample_dirty_data)
    assert df_result.loc[0, "region"] == "Costa"
    assert df_result.loc[3, "region"] == "Oriente"
    assert df_result.loc[4, "region"] == "Sierra"
    assert df_result.loc[8, "region"] == "Sierra"
    assert pd.isna(df_result.loc[6, "region"])


def test_clean_inconsistencies_age_business_rules(sample_dirty_data: pd.DataFrame):
    """Valida reemplazo por NaN en edades fuera de [18, 100]."""
    df_result = clean_inconsistencies(sample_dirty_data)
    # 120 > 100 -> NaN
    assert pd.isna(df_result.loc[4, "age"])
    # 15 < 18 -> NaN
    assert pd.isna(df_result.loc[5, "age"])
    # Edad válida 34 intacta
    assert df_result.loc[0, "age"] == 34


def test_impute_column_mean():
    """Valida imputación por media en variables continuas."""
    df = pd.DataFrame({"salary": [10.0, 20.0, 30.0, np.nan]})
    df_imputed = impute_column(df, "salary", strategy="mean")
    assert df_imputed["salary"].isna().sum() == 0
    assert df_imputed.loc[3, "salary"] == 20.0


def test_impute_column_median():
    """Valida imputación por mediana."""
    df = pd.DataFrame({"salary": [10.0, 20.0, 100.0, np.nan]})
    df_imputed = impute_column(df, "salary", strategy="median")
    assert df_imputed.loc[3, "salary"] == 20.0


def test_impute_column_mode():
    """Valida imputación por moda en variables categóricas."""
    df = pd.DataFrame({"region": ["Costa", "Costa", "Sierra", None]})
    df_imputed = impute_column(df, "region", strategy="mode")
    assert df_imputed.loc[3, "region"] == "Costa"


def test_impute_column_knn():
    """Valida imputación multivariable avanzada con KNNImputer."""
    df = pd.DataFrame(
        {
            "feature1": [1.0, 2.0, 3.0, 10.0, 11.0, 12.0],
            "feature2": [2.0, 4.0, np.nan, 20.0, 22.0, 24.0],
        }
    )
    df_imputed = impute_column(df, "feature2", strategy="knn")
    assert df_imputed["feature2"].isna().sum() == 0
    # Imputación debe ser cercana a los vecinos más cercanos (1.0, 2.0 -> 2.0, 4.0)
    assert 4.0 <= df_imputed.loc[2, "feature2"] <= 15.0


def test_handle_outliers_iqr():
    """Valida acotamiento (capping) por IQR preservando longitud del dataset."""
    df = pd.DataFrame({"annual_income": [10, 12, 11, 13, 12, 1000]})
    initial_len = len(df)
    df_capped = handle_outliers(df, columns=["annual_income"], method="iqr")
    assert len(df_capped) == initial_len
    # El valor 1000 debe quedar acotado al umbral superior
    assert df_capped["annual_income"].max() < 1000
    assert df_capped["annual_income"].var() < df["annual_income"].var()


def test_handle_outliers_empirical():
    """Valida acotamiento por regla empírica 3-sigma."""
    df = pd.DataFrame({"loan_amount": [100.0] * 20 + [50000.0]})
    df_capped = handle_outliers(df, columns=["loan_amount"], method="empirical")
    assert len(df_capped) == 21
    assert df_capped["loan_amount"].max() < 50000.0


def test_run_cleaning_pipeline_memory(sample_dirty_data: pd.DataFrame):
    """Valida la ejecución secuencial completa del pipeline en memoria."""
    df_clean = run_cleaning_pipeline(
        df=sample_dirty_data,
        save_to_db=False,
        verbose=False,
    )
    assert not df_clean.empty
    assert len(df_clean) == len(sample_dirty_data)
    # Ningún nulo remanente
    assert df_clean.isna().sum().sum() == 0
    # Región normalizada
    assert set(df_clean["region"].unique()).issubset({"Costa", "Sierra", "Oriente", "Insular"})
    # Edades válidas
    assert (df_clean["age"] >= 18).all() and (df_clean["age"] <= 100).all()


def test_run_cleaning_pipeline_db_integration():
    """Valida la ejecución del pipeline con persistencia en PostgreSQL."""
    engine = get_database_engine()
    df_clean = run_cleaning_pipeline(
        save_to_db=True,
        engine=engine,
        verbose=False,
    )
    assert not df_clean.empty

    # Verificar que la tabla 'customer_credit_clean' fue creada y contiene registros
    with engine.connect() as conn:
        clean_count = conn.execute(
            text("SELECT COUNT(*) FROM customer_credit_clean;")
        ).scalar()
    assert clean_count > 0
    assert clean_count == len(df_clean)
