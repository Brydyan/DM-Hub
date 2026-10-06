"""Generador de datos sintéticos para `customer_credit_transactions`.

Puebla la tabla con registros realistas e inyecta defectos deliberados
(nulos, outliers, duplicados y categorías inconsistentes) para dar
material a los temas de EDA (U2-T2) y limpieza de datos (U2-T3).

La variable `has_defaulted` se genera con probabilidad inversamente
proporcional al `credit_score`, de modo que exista una señal real que
los modelos de clasificación de la Unidad 3 puedan aprender.

Uso (desde el host, contra el contenedor):
    docker compose exec analytics python scripts/seed_synthetic.py --n 2000

El script es reejecutable: cada corrida agrega un lote nuevo.
"""
import argparse

import numpy as np
import pandas as pd
from sqlalchemy import text

from src.db_connector import get_database_engine

REGIONS = ["Costa", "Sierra", "Oriente", "Insular"]
REGION_WEIGHTS = [0.45, 0.30, 0.20, 0.05]

# Variantes "sucias" para ejercicios de normalización de categorías
DIRTY_REGIONS = {
    "Costa": ["costa", " COSTA", "Costa "],
    "Sierra": ["sierra", "Sierra  "],
}


def generate_frame(n: int, seed: int = 42) -> pd.DataFrame:
    """Genera `n` registros sintéticos con distribuciones realistas."""
    rng = np.random.default_rng(seed)

    age = np.clip(rng.normal(38, 12, n), 18, 80).round()
    annual_income = np.clip(rng.lognormal(10.3, 0.55, n), 8000, 150000).round(2)
    credit_score = np.clip(rng.normal(680, 60, n), 300, 850).round()
    # El préstamo se correlaciona positivamente con el ingreso
    loan_amount = (
        annual_income * rng.uniform(0.1, 0.6, n) * (1 + rng.normal(0, 0.05, n))
    ).round(2)
    region = rng.choice(REGIONS, n, p=REGION_WEIGHTS)

    # P(default) decrece con el score: 90% en score 300, ~5% en score 850
    p_default = np.clip(0.9 - (credit_score - 300) / 550 * 0.85, 0.02, 0.9)
    has_defaulted = rng.random(n) < p_default

    return pd.DataFrame(
        {
            "customer_id": [f"CUST-{20000 + i}" for i in range(n)],
            "age": age,
            "annual_income": annual_income,
            "credit_score": credit_score,
            "loan_amount": loan_amount,
            "has_defaulted": has_defaulted,
            "region": region,
        }
    )


def inject_dirty_data(df: pd.DataFrame, seed: int = 43) -> pd.DataFrame:
    """Ensucia el dataset a propósito para los temas de limpieza (U2-T3)."""
    rng = np.random.default_rng(seed)
    dirty = df.copy()
    n = len(dirty)

    # ~3% de nulos en edad y ~4% en ingreso
    dirty.loc[rng.choice(n, int(n * 0.03), replace=False), "age"] = np.nan
    dirty.loc[rng.choice(n, int(n * 0.04), replace=False), "annual_income"] = (
        np.nan
    )

    # Outliers extremos e imposibles
    dirty.loc[rng.choice(n, 3, replace=False), "annual_income"] = [
        500000.0,
        620000.0,
        999.0,
    ]
    dirty.loc[rng.choice(n, 2, replace=False), "age"] = [150, -5]
    dirty.loc[rng.choice(n, 3, replace=False), "credit_score"] = 999

    # ~5% de categorías inconsistentes en Costa/Sierra
    mask = dirty["region"].isin(DIRTY_REGIONS.keys())
    idx = dirty[mask].sample(frac=0.05, random_state=seed).index
    dirty.loc[idx, "region"] = [
        rng.choice(DIRTY_REGIONS[r]) for r in dirty.loc[idx, "region"]
    ]

    # 8 duplicados exactos para el ejercicio de deduplicación
    duplicates = dirty.sample(8, random_state=seed)
    return pd.concat([dirty, duplicates], ignore_index=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Siembra datos sintéticos en customer_credit_transactions"
    )
    parser.add_argument("--n", type=int, default=2000, help="registros base")
    parser.add_argument("--seed", type=int, default=42, help="semilla RNG")
    args = parser.parse_args()

    engine = get_database_engine()
    with engine.connect() as conn:
        before = conn.execute(
            text("SELECT COUNT(*) FROM customer_credit_transactions")
        ).scalar()

    df = inject_dirty_data(generate_frame(args.n, args.seed))
    df.to_sql(
        "customer_credit_transactions",
        engine,
        if_exists="append",
        index=False,
    )

    with engine.connect() as conn:
        after = conn.execute(
            text("SELECT COUNT(*) FROM customer_credit_transactions")
        ).scalar()

    print(f"Registros antes: {before} | insertados: {len(df)} | total: {after}")
    print(f"Nulos inyectados: edad={df['age'].isna().sum()}, "
          f"ingreso={df['annual_income'].isna().sum()}")
    print(f"Tasa de default sintética: {df['has_defaulted'].mean():.1%}")


if __name__ == "__main__":
    main()
