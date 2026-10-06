import pandas as pd
from scripts.seed_synthetic import generate_frame, inject_dirty_data

EXPECTED_COLUMNS = {
    "customer_id", "age", "annual_income", "credit_score",
    "loan_amount", "has_defaulted", "region",
}

def test_generate_frame_shape_and_columns():
    """El generador produce el volumen y esquema esperados."""
    df = generate_frame(n=100)
    assert len(df) == 100
    assert set(df.columns) == EXPECTED_COLUMNS
    assert df["customer_id"].is_unique

def test_generate_frame_is_deterministic():
    """Misma semilla → mismo dataset (reproducibilidad en clase)."""
    pd.testing.assert_frame_equal(generate_frame(50), generate_frame(50))

def test_inject_dirty_data_adds_defects():
    """La inyección crea nulos, outliers, categorías sucias y duplicados."""
    df = inject_dirty_data(generate_frame(n=500))

    assert df["age"].isna().sum() > 0
    assert df["annual_income"].isna().sum() > 0
    assert (df["annual_income"] > 150000).any() or (df["age"] > 80).any()
    assert df["region"].nunique() > 4  # variantes sucias presentes
    assert df["region"].str.strip().str.lower().nunique() == 4  # normalizables
    assert df.duplicated().sum() >= 8

def test_default_rate_has_signal():
    """El default correlaciona con credit_score (aprendible en U3)."""
    df = generate_frame(n=2000)
    low = df[df["credit_score"] < 600]["has_defaulted"].mean()
    high = df[df["credit_score"] > 750]["has_defaulted"].mean()
    assert low > high
