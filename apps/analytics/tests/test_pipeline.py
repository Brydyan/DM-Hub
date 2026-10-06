import pytest
import pandas as pd
import numpy as np
from src.pipeline import (
    load_and_preprocess_dataset,
    calculate_feature_metrics,
    scale_features,
)

def test_load_and_preprocess_dataset():
    X, y = load_and_preprocess_dataset()
    assert not X.empty
    assert len(X) == len(y)
    assert X.isna().sum().sum() == 0

def test_calculate_feature_metrics():
    X, _ = load_and_preprocess_dataset()
    metrics = calculate_feature_metrics(X)
    assert isinstance(metrics, pd.DataFrame)
    assert "mean" in metrics.columns
    assert "std" in metrics.columns

def test_scale_features():
    X, _ = load_and_preprocess_dataset()
    scaled = scale_features(X)
    assert isinstance(scaled, pd.DataFrame)
    assert list(scaled.columns) == list(X.columns)
    assert scaled.shape == X.shape
    # Normalización estándar: media 0 y desviación estándar 1 en cada columna.
    # StandardScaler usa ddof=0 (desviación poblacional), igual que std(ddof=0).
    for col in scaled.columns:
        assert scaled[col].mean() == pytest.approx(0.0, abs=1e-9)
        assert scaled[col].std(ddof=0) == pytest.approx(1.0, abs=1e-9)