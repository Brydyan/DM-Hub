"""Módulo de conexión y extracción de fuentes de datos relacionales."""
import os
from typing import Generator, Optional
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

DEFAULT_DB_URL = (
    "postgresql+psycopg2://dm_user:dm_password@postgres_db:5432/enterprise_warehouse"
)

def get_database_engine(connection_url: Optional[str] = None) -> Engine:
    """Crea un motor de conexión utilizando SQLAlchemy con connection pooling configurado."""
    url = connection_url or os.getenv("DB_URL", DEFAULT_DB_URL)
    return create_engine(
        url,
        pool_size=5,
        max_overflow=10,
        pool_recycle=1800,
        echo=False
    )

def extract_raw_data(query: str, engine: Optional[Engine] = None) -> pd.DataFrame:
    """Ejecuta una consulta SQL y carga la totalidad del resultado en un DataFrame de Pandas."""
    active_engine = engine or get_database_engine()
    with active_engine.connect() as connection:
        df = pd.read_sql_query(text(query), con=connection)
    return df

def extract_raw_data_in_chunks(
    query: str,
    chunk_size: int = 500,
    engine: Optional[Engine] = None
) -> Generator[pd.DataFrame, None, None]:
    """Extrae datos masivos por lotes (chunking) para proteger la memoria RAM."""
    active_engine = engine or get_database_engine()
    with active_engine.connect() as connection:
        for chunk in pd.read_sql_query(text(query), con=connection, chunksize=chunk_size):
            yield chunk
