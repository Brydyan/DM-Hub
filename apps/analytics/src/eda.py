"""Lógica de EDA (U2-T2): dataset sintético de métricas de servidor.

Porta el ejercicio del notebook U2_T2_EDA a código de producción:
mismos datos, misma semilla y mismos outliers inyectados, pero
parametrizable para los retos de la sesión práctica.
"""
import io

import matplotlib

matplotlib.use("Agg")  # backend sin display: renderiza figuras a PNG en memoria

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

SEED = 42


def generate_server_metrics(n: int = 1000, seed: int = SEED) -> pd.DataFrame:
    """Genera el dataset sintético del notebook (tiempos de respuesta en ms)."""
    np.random.seed(seed)
    df = pd.DataFrame(
        {
            "tiempo_respuesta": np.random.normal(loc=150, scale=20, size=n),
            "fecha": pd.date_range(start="2026-09-01", periods=n, freq="h"),
            "usuarios_concurrentes": np.linspace(10, 500, n)
            + np.random.normal(0, 20, n),
        }
    )
    # Outliers inyectados a mano, igual que en el notebook
    df.loc[100:105, "tiempo_respuesta"] = [280, 295, 310, 305, 320, 290]
    df.loc[500:502, "tiempo_respuesta"] = [20, 15, 25]
    return df


def filter_outliers(df: pd.DataFrame, threshold: float = 250.0) -> pd.DataFrame:
    """Reto 3: aísla las filas cuyo tiempo_respuesta supera el umbral."""
    return df[df["tiempo_respuesta"] > threshold]


def build_eda_figure(
    bins: int = 30,
    panel_b: str = "density",
    hue_server: bool = False,
) -> bytes:
    """Construye la figura 2x2 del notebook y la devuelve como PNG en bytes.

    Parámetros de los retos:
    - bins (Reto 1): número de cajas del histograma.
    - panel_b (Reto 2): 'density' (KDE) o 'scatter' (usuarios vs. tiempo).
    - hue_server (Reto 4): si True, agrega columna 'servidor' y usa hue
      en el boxplot para comparar Servidor_A vs Servidor_B.
    """
    df = generate_server_metrics()
    if hue_server:
        rng = np.random.default_rng(7)
        df["servidor"] = rng.choice(["Servidor_A", "Servidor_B"], len(df))

    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(
        "Análisis Exploratorio de Datos: Detección de Patrones Visuales",
        fontsize=18,
        fontweight="bold",
    )

    # Panel A: Histograma (frecuencias)
    sns.histplot(
        df["tiempo_respuesta"],
        bins=bins,
        ax=axes[0, 0],
        color="royalblue",
        edgecolor="black",
    )
    axes[0, 0].set_title(f"Histograma (bins={bins})", fontsize=14)
    axes[0, 0].set_xlabel("Tiempo de Respuesta (ms)")
    axes[0, 0].set_ylabel("Frecuencia")

    # Panel B: Densidad KDE o Scatter según el reto elegido
    if panel_b == "scatter":
        sns.scatterplot(
            data=df,
            x="usuarios_concurrentes",
            y="tiempo_respuesta",
            ax=axes[0, 1],
            color="darkblue",
            alpha=0.5,
            s=15,
        )
        axes[0, 1].set_title("Dispersión: usuarios vs. tiempo", fontsize=14)
        axes[0, 1].set_xlabel("Usuarios Concurrentes")
        axes[0, 1].set_ylabel("Tiempo de Respuesta (ms)")
    else:
        sns.kdeplot(
            df["tiempo_respuesta"],
            ax=axes[0, 1],
            color="darkblue",
            fill=True,
            alpha=0.5,
        )
        axes[0, 1].set_title("Densidad: probabilidad", fontsize=14)
        axes[0, 1].set_xlabel("Tiempo de Respuesta (ms)")
        axes[0, 1].set_ylabel("Densidad")

    # Panel C: Boxplot (cuartiles y outliers), con hue opcional por servidor
    if hue_server:
        sns.boxplot(
            data=df,
            x="tiempo_respuesta",
            hue="servidor",
            ax=axes[1, 0],
        )
        axes[1, 0].set_title("Boxplot por servidor (hue)", fontsize=14)
    else:
        sns.boxplot(x=df["tiempo_respuesta"], ax=axes[1, 0], color="lightsteelblue")
        axes[1, 0].set_title("Boxplot: cuartiles y outliers", fontsize=14)
    axes[1, 0].set_xlabel("Tiempo de Respuesta (ms)")

    # Panel D: Líneas (tendencia de usuarios, primeras 100 horas)
    sns.lineplot(
        x=df["fecha"][:100],
        y=df["usuarios_concurrentes"][:100],
        ax=axes[1, 1],
        color="crimson",
        marker="o",
        markersize=4,
    )
    axes[1, 1].set_title("Líneas: tendencia de usuarios", fontsize=14)
    axes[1, 1].set_xlabel("Fecha / Hora")
    axes[1, 1].set_ylabel("Usuarios Concurrentes")
    axes[1, 1].tick_params(axis="x", rotation=45)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()
