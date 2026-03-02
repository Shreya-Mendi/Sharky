"""Tests for new DealScope API endpoints."""
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


def test_get_industries_returns_list():
    resp = client.get("/data/industries")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    first = data[0]
    assert "industry" in first
    assert "deal_count" in first
    assert "avg_ask" in first
    assert "avg_revenue" in first
    assert "success_rate" in first


def test_get_deals_returns_paginated():
    resp = client.get("/data/deals?limit=10&offset=0")
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert "deals" in data
    assert len(data["deals"]) <= 10


def test_get_deals_filter_by_industry():
    resp = client.get("/data/deals?industry=Technology&limit=50")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data["deals"], list)


def test_get_deals_filter_by_has_deal():
    resp = client.get("/data/deals?has_deal=true&limit=50")
    assert resp.status_code == 200


def test_get_deals_search_by_name():
    resp = client.get("/data/deals?search=test&limit=10")
    assert resp.status_code == 200
