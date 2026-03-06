"""Tests for VC and startup insight endpoints."""

from fastapi.testclient import TestClient

from src.api.main import app


client = TestClient(app)


def _stub_news(*_args, **_kwargs):
    return {
        "status": "enabled",
        "articles_scanned": 24,
        "sentiment_hint": "positive",
        "summary": "Stubbed positive market sentiment.",
    }


def test_vc_insight_endpoint_returns_market_brief(monkeypatch):
    monkeypatch.setenv("NEWSAPI_KEY", "test-key")
    monkeypatch.setattr("src.insights.recommendation_engine._news_signal_snapshot", _stub_news)
    payload = {
        "industry": "Technology",
        "top_k": 3,
        "risk_appetite": "balanced",
    }
    resp = client.post("/insights/vc", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["industry"] == "Technology"
    assert "industry_health_score" in data
    assert "kpis" in data
    assert "thesis" in data
    assert "comparable_companies" in data
    assert "news_signals" in data
    assert "confidence_score" in data
    assert "data_sources" in data
    assert isinstance(data["thesis"], list)


def test_startup_strategy_endpoint_returns_us_market_recommendations(monkeypatch):
    monkeypatch.setenv("NEWSAPI_KEY", "test-key")
    monkeypatch.setattr("src.insights.recommendation_engine._news_signal_snapshot", _stub_news)
    payload = {
        "company_name": "NovaChain",
        "industry": "Technology",
        "ask_amount": 500000,
        "equity_offered_pct": 10,
        "revenue_trailing_12m": 350000,
        "founder_count": 2,
        "growth_rate_qoq": 0.12,
        "monthly_burn": 45000,
        "gross_margin_pct": 62,
        "business_model": "b2b",
        "pitch_sentiment_score": 0.45,
        "shark_enthusiasm_max": 0.3,
        "objection_count": 2,
        "negotiation_rounds": 1,
    }
    resp = client.post("/insights/startup", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["company_name"] == "NovaChain"
    assert "readiness_score" in data
    assert "deal_probability" in data
    assert "strengths" in data
    assert "gaps" in data
    assert "recommendations" in data
    assert "us_market_recommendations" in data
    assert "news_signals" in data
    assert len(data["us_market_recommendations"]) > 0
    top_market = data["us_market_recommendations"][0]
    assert "market" in top_market
    assert "fit_score" in top_market
    assert "confidence" in top_market


def test_market_fit_engine_returns_sector_and_avenue_rankings(monkeypatch):
    monkeypatch.setenv("NEWSAPI_KEY", "test-key")
    monkeypatch.setattr("src.insights.recommendation_engine._news_signal_snapshot", _stub_news)
    payload = {
        "industry": "Technology",
        "business_model": "b2b",
        "revenue_trailing_12m": 750000,
        "monthly_burn": 50000,
        "growth_rate_qoq": 0.14,
        "gross_margin_pct": 61,
        "top_k": 4,
    }
    resp = client.post("/insights/market-fit", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["input_industry"] == "Technology"
    assert len(data["sector_rankings"]) > 0
    assert len(data["avenue_rankings"]) > 0
    assert len(data["geo_rankings"]) > 0
    sector = data["sector_rankings"][0]
    assert "sector" in sector
    assert "fit_score" in sector
    assert "confidence" in sector
    assert "reasons" in sector
    avenue = data["avenue_rankings"][0]
    assert "avenue" in avenue
    assert "fit_score" in avenue
    assert "confidence" in avenue
    geo = data["geo_rankings"][0]
    assert "market" in geo
    assert "region" in geo
    assert "fit_score" in geo


def test_vc_insight_requires_newsapi_key(monkeypatch):
    monkeypatch.delenv("NEWSAPI_KEY", raising=False)
    payload = {
        "industry": "Technology",
        "top_k": 3,
        "risk_appetite": "balanced",
    }
    resp = client.post("/insights/vc", json=payload)
    assert resp.status_code == 503
    assert "NEWSAPI_KEY is required" in resp.json()["detail"]
