"""Pipeline base para extracción y preprocesamiento de datos."""
from typing import Tuple
import pandas as pd
from sklearn.datasets import load_iris
from sklearn.preprocessing import StandardScaler

def load_and_preprocess_dataset() -> Tuple[pd.DataFrame, pd.Series]:
    """Carga Iris, valida ausencia de duplicados y separa variables."""
    dataset = load_iris(as_frame=True)
    df: pd.DataFrame = dataset.frame
    
    # Limpieza inicial
    df_clean = df.drop_duplicates().dropna()
    
    features = df_clean[dataset.feature_names]
    target = df_clean["target"]
    
    return features, target

def calculate_feature_metrics(data: pd.DataFrame) -> pd.DataFrame:
    """Calcula estadísticas descriptivas básicas de las características."""
    return data.describe().T[["mean", "std", "min", "max"]]

def scale_features(data: pd.DataFrame) -> pd.DataFrame:
    """Aplica normalización estándar (Z-score) con StandardScaler de Scikit-Learn.

    Cada columna se transforma para que tenga media 0 y desviación estándar 1.
    Se conservan los nombres de las columnas y el índice del DataFrame original.
    """
    scaler = StandardScaler()
    scaled_array = scaler.fit_transform(data)
    return pd.DataFrame(scaled_array, columns=data.columns, index=data.index)
