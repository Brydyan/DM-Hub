import pytest
from fastapi.testclient import TestClient
from src.api import app

client = TestClient(app)

def test_health():
    """Valida que el endpoint de salud reporte conectividad con PostgreSQL."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_list_transactions():
    """Valida que se listen las transacciones sembradas."""
    response = client.get("/api/transactions")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 9
    assert "customer_id" in data[0]
    assert "credit_score" in data[0]

def test_list_transactions_region_filter():
    """Valida el filtro parametrizado por región."""
    response = client.get("/api/transactions", params={"region": "Costa"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert all(r["region"] == "Costa" for r in data)

def test_stats_by_region():
    """Valida el conteo agrupado por región (Ejercicio 1)."""
    response = client.get("/api/stats/by-region")
    assert response.status_code == 200
    data = response.json()
    assert {r["region"] for r in data} >= {"Costa", "Sierra"}
    assert all(r["total"] > 0 for r in data)

def test_stats_risk_profile():
    """Valida que solo retorne clientes bajo el umbral de credit_score."""
    response = client.get("/api/stats/risk-profile", params={"threshold": 650})
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert all(r["credit_score"] < 650 for r in data)

def test_transactions_crud_cycle():
    """Valida el ciclo completo: crear, actualizar y eliminar un registro."""
    payload = {
        "customer_id": "TEST-CRUD",
        "age": 30,
        "annual_income": 40000.0,
        "credit_score": 700,
        "loan_amount": 9000.0,
        "has_defaulted": False,
        "region": "Costa",
    }
    # CREATE
    res = client.post("/api/transactions", json=payload)
    assert res.status_code == 201
    new_id = res.json()["transaction_id"]

    # UPDATE
    res = client.put(f"/api/transactions/{new_id}", json={**payload, "credit_score": 750})
    assert res.status_code == 200
    assert res.json()["credit_score"] == 750

    # DELETE
    res = client.delete(f"/api/transactions/{new_id}")
    assert res.status_code == 204

    # DELETE de un id inexistente → 404
    res = client.delete(f"/api/transactions/{new_id}")
    assert res.status_code == 404

def test_stats_overview():
    """Valida los KPIs generales del warehouse."""
    response = client.get("/api/stats/overview")
    assert response.status_code == 200
    data = response.json()
    assert data["total_customers"] >= 9
    assert data["total_regions"] >= 3
    assert 0 <= data["default_rate_pct"] <= 100
