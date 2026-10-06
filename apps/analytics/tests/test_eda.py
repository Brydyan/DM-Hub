import pandas as pd
from src.eda import (
    build_eda_figure,
    filter_outliers,
    generate_server_metrics,
)

def test_generate_server_metrics_shape_and_columns():
    """El dataset replica el del notebook: 1000 filas, 3 columnas."""
    df = generate_server_metrics()
    assert len(df) == 1000
    assert set(df.columns) == {
        "tiempo_respuesta", "fecha", "usuarios_concurrentes"
    }

def test_generate_server_metrics_deterministic():
    """Misma semilla → mismos datos (clase reproducible)."""
    pd.testing.assert_frame_equal(
        generate_server_metrics(), generate_server_metrics()
    )

def test_filter_outliers_captures_injected():
    """Los outliers inyectados (>250 ms) son capturados por el filtro."""
    df = filter_outliers(generate_server_metrics(), threshold=250.0)
    assert len(df) >= 6
    assert (df["tiempo_respuesta"] > 250).all()

def test_build_eda_figure_returns_png():
    """La figura se renderiza como PNG válido en memoria."""
    png = build_eda_figure(bins=10, panel_b="scatter", hue_server=True)
    assert png[:4] == b"\x89PNG"
    assert len(png) > 10000
