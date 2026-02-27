"""Tests for FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from src.api.main import app
    return TestClient(app)


class TestHealthEndpoint:
    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestPredictEndpoint:
    def test_predict_returns_200(self, client):
        payload = {
            "ask_amount": 200000,
            "equity_offered_pct": 10.0,
            "revenue_trailing_12m": 500000,
            "industry": "Food",
            "founder_count": 1,
        }
        response = client.post("/predict", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "deal_probability" in data
        assert "deal_score" in data

    def test_predict_validates_input(self, client):
        response = client.post("/predict", json={})
        assert response.status_code == 422


class TestDataEndpoints:
    def test_stats(self, client):
        response = client.get("/data/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_pitches" in data
        assert "total_episodes" in data

    def test_episodes_list(self, client):
        response = client.get("/data/episodes")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_pitches_paginated(self, client):
        response = client.get("/data/pitches?limit=5&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "pitches" in data
