import pytest
import pandas as pd
from sqlalchemy import text
from src.db_connector import get_database_engine, extract_raw_data, extract_raw_data_in_chunks

def test_engine_connection():
    """Valida la conectividad básica con el motor PostgreSQL."""
    engine = get_database_engine()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar()
        assert result == 1

def test_extract_raw_data():
    """Valida que los datos crudos se carguen correctamente en un DataFrame."""
    query = "SELECT * FROM customer_credit_transactions;"
    df = extract_raw_data(query)
    
    assert not df.empty
    assert isinstance(df, pd.DataFrame)
    assert "customer_id" in df.columns
    assert "credit_score" in df.columns
    assert len(df) >= 9

def test_extract_raw_data_in_chunks():
    """Valida que el generador de lotes entregue bloques correctos."""
    query = "SELECT * FROM customer_credit_transactions ORDER BY transaction_id;"
    chunks = list(extract_raw_data_in_chunks(query, chunk_size=3))
    
    assert len(chunks) >= 3
    assert len(chunks[0]) == 3
    assert isinstance(chunks[0], pd.DataFrame)