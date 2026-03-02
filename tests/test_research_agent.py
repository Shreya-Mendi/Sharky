"""Tests for research agent tools (unit tests, no API keys needed)."""
import pytest
from src.api.research_agent import search_deals_tool, get_market_stats_tool, predict_deal_tool


def test_search_deals_returns_results():
    results = search_deals_tool(query="food", limit=5)
    assert isinstance(results, list)
    assert len(results) <= 5
    if results:
        assert "company_name" in results[0]
        assert "relevance" in results[0]


def test_get_market_stats_returns_dict():
    stats = get_market_stats_tool(industry="Technology")
    assert isinstance(stats, dict)
    assert "industry" in stats
    assert "deal_count" in stats


def test_predict_deal_returns_score():
    result = predict_deal_tool(ask_amount=500000, equity_pct=10, revenue=100000)
    assert "deal_probability" in result
    assert "deal_score" in result
    assert 0 <= result["deal_probability"] <= 1
    assert 1 <= result["deal_score"] <= 10
