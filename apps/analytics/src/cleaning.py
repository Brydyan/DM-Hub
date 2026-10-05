"""Módulo de limpieza y calidad de datos para el pipeline de preparación (CRISP-DM Fase 3)."""
from typing import List, Optional
import numpy as np
import pandas as pd
from sklearn.impute import KNNImputer
from sqlalchemy.engine import Engine

from src.db_connector import extract_raw_data, get_database_engine


def clean_inconsistencies(df: pd.DataFrame) -> pd.DataFrame:
    """Estandariza columnas categóricas y marca con NaN valores numéricos que violan reglas de negocio.

    - Normaliza la columna 'region': elimina espacios en blanco (strip) y estandariza a Title Case.
    - Valida reglas de negocio en 'age': valores fuera del rango [18, 100] se convierten en NaN
      para forzar su paso por la etapa de imputación.
    """
    df_clean = df.copy()

    # Normalización de columna categórica 'region'
    if "region" in df_clean.columns:
        df_clean["region"] = df_clean["region"].apply(
            lambda val: val.strip().title() if isinstance(val, str) else val
        )

    # Validación de reglas de negocio en variables numéricas (age)
    if "age" in df_clean.columns:
        df_clean["age"] = pd.to_numeric(df_clean["age"], errors="coerce")
        invalid_age_mask = (df_clean["age"] < 18) | (df_clean["age"] > 100)
        df_clean.loc[invalid_age_mask, "age"] = np.nan

    return df_clean


def impute_column(
    df: pd.DataFrame,
    column: str,
    strategy: str = "mean",
) -> pd.DataFrame:
    """Imputa valores faltantes (NaN) en una columna usando diversas estrategias.

    Estrategias soportadas:
    1. 'mean': Media matemática (variables numéricas continuas).
    2. 'median': Mediana estadística (variables numéricas continuas o asimétricas).
    3. 'mode': Moda (obligatoria para variables categóricas como 'region').
    4. 'knn': Imputación multivariable avanzada utilizando KNNImputer de scikit-learn.
    """
    df_imputed = df.copy()

    if column not in df_imputed.columns:
        raise ValueError(f"Columna '{column}' no encontrada en el DataFrame.")

    strategy_lower = strategy.lower().strip()

    if strategy_lower == "mean":
        mean_val = df_imputed[column].astype(float).mean()
        df_imputed[column] = df_imputed[column].fillna(mean_val)

    elif strategy_lower == "median":
        median_val = df_imputed[column].astype(float).median()
        df_imputed[column] = df_imputed[column].fillna(median_val)

    elif strategy_lower == "mode":
        mode_series = df_imputed[column].dropna().mode()
        if not mode_series.empty:
            df_imputed[column] = df_imputed[column].fillna(mode_series.iloc[0])

    elif strategy_lower == "knn":
        numeric_cols = df_imputed.select_dtypes(include=[np.number]).columns.tolist()
        if column not in numeric_cols:
            raise ValueError(
                f"La imputación KNN requiere columnas numéricas, pero '{column}' no es numérica."
            )

        n_neighbors = min(3, max(1, len(df_imputed) - 1))
        imputer = KNNImputer(n_neighbors=n_neighbors)
        imputed_array = imputer.fit_transform(df_imputed[numeric_cols])
        df_imputed_numeric = pd.DataFrame(
            imputed_array, columns=numeric_cols, index=df_imputed.index
        )
        df_imputed[column] = df_imputed_numeric[column]

    else:
        raise ValueError(
            f"Estrategia '{strategy}' no soportada. Use 'mean', 'median', 'mode' o 'knn'."
        )

    return df_imputed


def handle_outliers(
    df: pd.DataFrame,
    columns: Optional[List[str]] = None,
    method: str = "iqr",
    factor: float = 1.5,
) -> pd.DataFrame:
    """Detecta y trata outliers numéricos utilizando la técnica de Acotamiento (Capping).

    A diferencia de la eliminación directa, fija los valores atípicos en umbrales límite
    (inferior y superior), preservando el 100% de los registros del dataset.

    Métodos:
    - 'iqr': Rango intercuartílico [Q1 - factor * IQR, Q3 + factor * IQR].
    - 'empirical' / '3sigma': Regla empírica basada en 3 desviaciones estándar [mu - 3*sigma, mu + 3*sigma].
    """
    df_capped = df.copy()
    target_columns = columns or ["annual_income", "loan_amount"]
    method_lower = method.lower().strip()

    for col in target_columns:
        if col not in df_capped.columns:
            continue

        series = pd.to_numeric(df_capped[col], errors="coerce")

        if method_lower == "iqr":
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - factor * iqr
            upper_bound = q3 + factor * iqr
        elif method_lower in ["empirical", "3sigma", "zscore"]:
            mean = series.mean()
            std = series.std()
            lower_bound = mean - 3.0 * std
            upper_bound = mean + 3.0 * std
        else:
            raise ValueError(
                f"Método '{method}' no soportado. Seleccione 'iqr' o 'empirical'."
            )

        # Capping: acotar los valores conservando todas las observaciones
        df_capped[col] = series.clip(lower=lower_bound, upper=upper_bound)

    return df_capped


def run_cleaning_pipeline(
    df: Optional[pd.DataFrame] = None,
    save_to_db: bool = True,
    engine: Optional[Engine] = None,
    imputation_strategy: str = "mean",
    outlier_method: str = "iqr",
    verbose: bool = True,
) -> pd.DataFrame:
    """Orquesta secuencialmente el pipeline de limpieza y calidad de datos:

    1. Filtro de inconsistencias (normalización de 'region' y validación de reglas de negocio en 'age').
    2. Imputación estadística (variables numéricas continuas) y por moda (variables categóricas).
    3. Detección y acotamiento de Outliers ('annual_income', 'loan_amount').
    4. Auditoría de calidad mostrando varianza de 'annual_income' antes y después.
    5. Persistencia en la tabla 'customer_credit_clean' de PostgreSQL.
    """
    active_engine = engine or get_database_engine()

    # Carga de datos crudos si no se suministra un DataFrame explícito
    if df is None:
        raw_query = "SELECT * FROM customer_credit_transactions;"
        df_raw = extract_raw_data(raw_query, engine=active_engine)
    else:
        df_raw = df.copy()

    # Varianza inicial de annual_income antes de tratamiento
    var_income_before = float(df_raw["annual_income"].dropna().var())

    # 1. Filtro de inconsistencias
    df_step1 = clean_inconsistencies(df_raw)

    # 2. Imputación estadística
    df_step2 = df_step1.copy()
    continuous_cols = ["age", "annual_income", "credit_score", "loan_amount"]
    for col in continuous_cols:
        if col in df_step2.columns and df_step2[col].isna().any():
            df_step2 = impute_column(df_step2, col, strategy=imputation_strategy)

    if "region" in df_step2.columns and df_step2["region"].isna().any():
        df_step2 = impute_column(df_step2, "region", strategy="mode")

    # 3. Detección y acotamiento de Outliers
    df_clean = handle_outliers(
        df_step2,
        columns=["annual_income", "loan_amount"],
        method=outlier_method,
    )

    # Varianza final de annual_income post-tratamiento
    var_income_after = float(df_clean["annual_income"].var())
    variance_reduction = (
        ((var_income_before - var_income_after) / var_income_before * 100.0)
        if var_income_before > 0
        else 0.0
    )

    if verbose:
        print("\n" + "=" * 65)
        print("          AUDITORÍA DE CALIDAD - PIPELINE DE LIMPIEZA          ")
        print("=" * 65)
        print(f"Registros procesados:              {len(df_clean)} (100% registros conservados)")
        print(f"Varianza 'annual_income' (Antes):   {var_income_before:,.2f}")
        print(f"Varianza 'annual_income' (Después): {var_income_after:,.2f}")
        print(f"Reducción porcentual de varianza:   {variance_reduction:.2f}%")
        print("-" * 65)
        print("Valores nulos post-pipeline:")
        for col, null_count in df_clean.isna().sum().items():
            print(f"  - {col}: {null_count}")
        print("=" * 65 + "\n")

    # 4. Guardar en base de datos PostgreSQL
    if save_to_db:
        with active_engine.begin() as conn:
            df_clean.to_sql(
                "customer_credit_clean",
                con=conn,
                if_exists="replace",
                index=False,
            )
        if verbose:
            print("Resultado persistido exitosamente en tabla 'customer_credit_clean'.\n")

    return df_clean


if __name__ == "__main__":
    df_clean = run_cleaning_pipeline()
    print("REFLEXIÓN TEÓRICO-PRÁCTICA (Riesgo Crediticio y Capping):")
    print(
        "En el análisis de riesgo crediticio, eliminar observaciones atípicas (outliers) "
        "implicaría descartar clientes de alto patrimonio o solicitudes de financiamiento "
        "extraordinarias, introduciendo un sesgo de selección severo en los modelos predictivos "
        "y perdiendo el historial de pago o incumplimiento de segmentos críticos de cartera. "
        "El acotamiento (capping) preserva la integridad muestral y el volumen de registros, "
        "neutralizando el apalancamiento desmedido que los valores extremos ejercen sobre la "
        "varianza y los pesos de modelos lineales o basados en distancia, sin perder la señal "
        "de riesgo del cliente."
    )
