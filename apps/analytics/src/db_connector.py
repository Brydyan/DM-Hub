"""Módulo de conexión y extracción de fuentes de datos relacionales."""
import os
from typing import Generator, Optional
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# Carga un .env local si existe (ejecución fuera de Docker). Dentro del
# contenedor la URL llega como variable de entorno DB_URL (docker-compose).
# Las credenciales NUNCA se escriben en el código fuente.
load_dotenv()

def get_database_engine(connection_url: Optional[str] = None) -> Engine:
    """
    Crea un motor de conexión utilizando SQLAlchemy con connection pooling configurado.
    
    Jerarquía de configuración: URL explícita > variable de entorno DB_URL.
    Si ninguna está definida, falla con un mensaje claro.
    """
    # 1. Selecciona la URL priorizando el parámetro directo y luego el entorno
    url = connection_url or os.getenv("DB_URL")
    if not url:
        raise RuntimeError(
            "DB_URL no está definida. Configúrala como variable de entorno "
            "o en un archivo .env (ver .env.example)."
        )
    
    # 2. Configura el pool de conexiones de SQLAlchemy
    return create_engine(
        url,
        pool_size=15,       # Número base de conexiones permanentes en el pool
        max_overflow=10,   # Conexiones adicionales temporales permitidas en picos de demanda
        pool_recycle=1800, # Tiempo en segundos (30 min) tras el cual se renuevan las conexiones
        echo=False         # Suprime los logs de depuración SQL en la salida estándar
    )

def extract_raw_data(
    query: str,
    params: Optional[dict] = None,
    engine: Optional[Engine] = None
) -> pd.DataFrame:
    """
    Ejecuta una consulta SQL y carga la totalidad del resultado en un DataFrame de Pandas.
    
    Recomendado para volúmenes de datos pequeños o medianos que quepan holgadamente en RAM.
    Acepta `params` para consultas parametrizadas (previene inyección SQL).
    """
    # Reutiliza el motor inyectado o instancia uno nuevo
    active_engine = engine or get_database_engine()
    
    # Gestiona el ciclo de vida de la conexión mediante context manager
    with active_engine.connect() as connection:
        # text(query) convierte el string en un objeto SQL ejecutable compatible con SQLAlchemy 2.0+
        df = pd.read_sql_query(text(query), con=connection, params=params)
        
    return df

def extract_raw_data_in_chunks(
    query: str,
    chunk_size: int = 3,
    engine: Optional[Engine] = None
) -> Generator[pd.DataFrame, None, None]:
    """
    Extrae datos masivos por lotes (chunking) para proteger la memoria RAM.
    
    Retorna un generador que entrega lotes de filas como DataFrames individuales.
    """
    # Reutiliza el motor inyectado o instancia uno nuevo
    active_engine = engine or get_database_engine()
    
    # Mantiene la conexión abierta mientras el generador esté produciendo elementos
    with active_engine.connect() as connection:
        # Al especificar chunksize, Pandas devuelve un iterador en lugar de cargar todo el conjunto
        for chunk in pd.read_sql_query(text(query), con=connection, chunksize=chunk_size):
            yield chunk  # Emite el DataFrame parcial hacia el consumidor