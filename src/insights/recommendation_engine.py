"""Recommendation engines for VC and startup insights (USA-focused Phase 1)."""

from __future__ import annotations

import csv
import io
import os
import zipfile
from functools import lru_cache
from pathlib import Path
from typing import Optional

import httpx
import numpy as np

from src.data.cache import classify_industry, get_all_pitches, get_deals
from src.nlp.hybrid_ai import model_stack_status, transcript_behavioral_features


KAGGLE_ZIP = Path("data/archive.zip")

# Align multiple naming schemes into one insight taxonomy.
INDUSTRY_ALIASES = {
    "food & beverage": "Food & Beverage",
    "food and beverage": "Food & Beverage",
    "food": "Food & Beverage",
    "technology": "Technology",
    "technology/software": "Technology",
    "tech": "Technology",
    "health & wellness": "Health & Wellness",
    "health/wellness": "Health & Wellness",
    "health": "Health & Wellness",
    "fashion & beauty": "Fashion & Beauty",
    "fashion/beauty": "Fashion & Beauty",
    "lifestyle/home": "Home & Garden",
    "home & garden": "Home & Garden",
    "children & education": "Children & Education",
    "children/education": "Children & Education",
    "fitness/sports/outdoors": "Fitness & Sports",
    "fitness & sports": "Fitness & Sports",
    "media/entertainment": "Entertainment",
    "pet products": "Pet Products",
    "automotive": "Automotive",
    "other": "Other",
    "uncertain/other": "Other",
}

KAGGLE_TO_INSIGHT_INDUSTRY = {
    "Food and Beverage": "Food & Beverage",
    "Technology/Software": "Technology",
    "Health/Wellness": "Health & Wellness",
    "Fashion/Beauty": "Fashion & Beauty",
    "Lifestyle/Home": "Home & Garden",
    "Children/Education": "Children & Education",
    "Fitness/Sports/Outdoors": "Fitness & Sports",
    "Media/Entertainment": "Entertainment",
    "Pet Products": "Pet Products",
    "Automotive": "Automotive",
}

# US market baseline scores are expert priors calibrated from publicly available
# composite indices (NVCA regional investment data, BLS labor statistics, USPS
# logistics density, Census population/consumer spending data) and normalised to
# a 0-1 scale for each dimension.  They are NOT model outputs — they are the
# starting point that the scoring function adjusts using industry priors, business
# model weights, and live news sentiment before producing a final fit score.
# Source: expert prior — update annually from NVCA, BLS, Census Bureau.
US_MARKETS = [
    {
        "name": "San Francisco Bay Area",
        "region": "West",
        "strengths": {
            "talent": 0.95,       # #1 tech talent density nationally (BLS OES 2024)
            "capital_access": 0.98,  # ~37% of all US VC dollars deployed (NVCA 2024)
            "enterprise_access": 0.82,  # dense Fortune 500 tech buyer cluster
            "consumer_access": 0.76,  # large but high-cost consumer base
            "cost_efficiency": 0.28,  # highest operating cost tier in the US
            "logistics": 0.64,       # port access but high last-mile costs
        },
    },
    {
        "name": "New York Metro",
        "region": "Northeast",
        "strengths": {
            "talent": 0.9,           # #2 national talent pool; finance + media depth
            "capital_access": 0.93,  # #2 VC market; strong fintech/consumer deal flow
            "enterprise_access": 0.88,  # highest enterprise buyer density east coast
            "consumer_access": 0.9,  # 20M metro population; high spending power
            "cost_efficiency": 0.35,  # second-highest cost tier nationally
            "logistics": 0.78,       # JFK/EWR hub; dense last-mile infrastructure
        },
    },
    {
        "name": "Boston",
        "region": "Northeast",
        "strengths": {
            "talent": 0.89,          # 35+ top research universities in metro area
            "capital_access": 0.82,  # strong life-sci / deeptech VC cluster
            "enterprise_access": 0.8,  # biotech + healthtech enterprise buyer density
            "consumer_access": 0.62,  # mid-size metro; educated, affluent demographic
            "cost_efficiency": 0.46,  # high cost but below NY/SF tier
            "logistics": 0.74,       # Logan hub; Northeast corridor rail access
        },
    },
    {
        "name": "Austin",
        "region": "South",
        "strengths": {
            "talent": 0.8,           # fastest growing tech talent relocation market
            "capital_access": 0.72,  # growing VC presence post-2020 migration wave
            "enterprise_access": 0.7,  # emerging enterprise base (Dell, Oracle campuses)
            "consumer_access": 0.66,  # fast-growing metro; younger demographic
            "cost_efficiency": 0.74,  # no state income tax; moderate commercial RE
            "logistics": 0.73,       # ABIA hub; central US geography advantage
        },
    },
    {
        "name": "Seattle",
        "region": "West",
        "strengths": {
            "talent": 0.86,          # Amazon/Microsoft anchor creates deep tech talent
            "capital_access": 0.76,  # mid-tier VC; strong cloud/enterprise deal flow
            "enterprise_access": 0.78,  # AWS + Microsoft = B2B enterprise access
            "consumer_access": 0.63,  # mid-size metro; high household income
            "cost_efficiency": 0.55,  # no state income tax; lower RE than SF
            "logistics": 0.71,       # Port of Seattle; Pacific Rim trade access
        },
    },
    {
        "name": "Chicago",
        "region": "Midwest",
        "strengths": {
            "talent": 0.74,          # large metro talent; strong finance + ops depth
            "capital_access": 0.67,  # growing VC; historically under-indexed vs coasts
            "enterprise_access": 0.82,  # #3 Fortune 500 headquarters city nationally
            "consumer_access": 0.74,  # 10M metro; strong mid-market consumer
            "cost_efficiency": 0.78,  # mid-cost market; favorable commercial RE
            "logistics": 0.9,        # O'Hare #2 cargo hub; rail + highway crossroads
        },
    },
    {
        "name": "Atlanta",
        "region": "South",
        "strengths": {
            "talent": 0.72,          # growing tech hub; HBCU pipeline advantage
            "capital_access": 0.62,  # Southeast VC market growing from low base
            "enterprise_access": 0.76,  # Coca-Cola, Delta, Home Depot cluster
            "consumer_access": 0.72,  # 6M metro; fast-growing Sun Belt demographics
            "cost_efficiency": 0.8,  # low cost of doing business; no franchise tax
            "logistics": 0.88,       # Hartsfield-Jackson #1 passenger; major freight
        },
    },
    {
        "name": "Los Angeles",
        "region": "West",
        "strengths": {
            "talent": 0.79,          # large creative + tech talent; USC/UCLA pipeline
            "capital_access": 0.75,  # strong consumer/media VC; growing deeptech
            "enterprise_access": 0.7,  # media + entertainment enterprise concentration
            "consumer_access": 0.91,  # 13M metro; highest consumer-facing market size
            "cost_efficiency": 0.44,  # high cost; improving vs SF but still expensive
            "logistics": 0.8,        # Port of LA/LB = largest US import gateway
        },
    },
]

INDUSTRY_MARKET_PRIORS = {
    "Food & Beverage": {"consumer_access": 1.2, "logistics": 1.2, "cost_efficiency": 1.1},
    "Technology": {"talent": 1.25, "capital_access": 1.2, "enterprise_access": 1.1},
    "Health & Wellness": {"consumer_access": 1.05, "talent": 1.1, "capital_access": 1.05},
    "Fashion & Beauty": {"consumer_access": 1.25, "logistics": 1.05, "capital_access": 1.0},
    "Home & Garden": {"consumer_access": 1.05, "logistics": 1.2, "cost_efficiency": 1.1},
    "Children & Education": {"consumer_access": 1.1, "enterprise_access": 1.0, "cost_efficiency": 1.05},
    "Fitness & Sports": {"consumer_access": 1.2, "cost_efficiency": 1.0, "capital_access": 1.0},
    "Entertainment": {"consumer_access": 1.25, "capital_access": 1.1, "talent": 1.05},
    "Pet Products": {"consumer_access": 1.1, "logistics": 1.1, "cost_efficiency": 1.05},
    "Automotive": {"logistics": 1.25, "enterprise_access": 1.15, "cost_efficiency": 1.1},
    "Other": {"cost_efficiency": 1.0},
}

SECTOR_ADJACENCY = {
    "Food & Beverage": ["Health & Wellness", "Home & Garden", "Fitness & Sports"],
    "Technology": ["Entertainment", "Health & Wellness", "Children & Education"],
    "Health & Wellness": ["Food & Beverage", "Fitness & Sports", "Technology"],
    "Fashion & Beauty": ["Entertainment", "Health & Wellness", "Home & Garden"],
    "Home & Garden": ["Food & Beverage", "Fashion & Beauty", "Technology"],
    "Children & Education": ["Technology", "Health & Wellness", "Entertainment"],
    "Fitness & Sports": ["Health & Wellness", "Food & Beverage", "Technology"],
    "Entertainment": ["Technology", "Fashion & Beauty", "Children & Education"],
    "Pet Products": ["Food & Beverage", "Health & Wellness", "Home & Garden"],
    "Automotive": ["Technology", "Home & Garden", "Fitness & Sports"],
}

US_GROWTH_AVENUES = [
    {
        "avenue": "Enterprise Partnerships",
        "fit_rules": {"b2b_bonus": 0.18, "margin_bonus": 0.06, "growth_bonus": 0.04},
        "description": "Channel growth via enterprise buyers, pilots, and long-term contracts.",
    },
    {
        "avenue": "Retail Distribution",
        "fit_rules": {"b2c_bonus": 0.15, "consumer_bonus": 0.08, "logistics_bonus": 0.06},
        "description": "Scale through retail placements and regional distributor leverage.",
    },
    {
        "avenue": "DTC Performance Marketing",
        "fit_rules": {"b2c_bonus": 0.16, "margin_bonus": 0.05, "growth_bonus": 0.03},
        "description": "Expand with direct response channels and disciplined CAC payback tracking.",
    },
    {
        "avenue": "Marketplace + Platform Integrations",
        "fit_rules": {"b2b_bonus": 0.08, "b2c_bonus": 0.08, "tech_bonus": 0.07},
        "description": "Accelerate distribution by integrating into existing digital ecosystems.",
    },
    {
        "avenue": "Licensing / White-Label",
        "fit_rules": {"margin_bonus": 0.07, "burn_penalty_relief": 0.05, "enterprise_bonus": 0.06},
        "description": "Grow via partner channels while reducing front-loaded go-to-market spend.",
    },
]


def normalize_industry(industry: str) -> str:
    if not industry:
        return "Other"
    key = industry.strip().lower()
    return INDUSTRY_ALIASES.get(key, industry.strip())


@lru_cache(maxsize=1)
def load_kaggle_rows() -> list[dict]:
    if not KAGGLE_ZIP.exists():
        return []
    with zipfile.ZipFile(KAGGLE_ZIP) as z:
        with z.open("Shark Tank US dataset.csv") as f:
            return list(csv.DictReader(io.TextIOWrapper(f)))


def _safe_float(value: str, default: float = 0.0) -> float:
    try:
        cleaned = value.strip().replace(",", "").replace("$", "")
        return float(cleaned) if cleaned else default
    except (AttributeError, ValueError):
        return default


def _kaggle_snapshot(industry: str) -> dict:
    rows = load_kaggle_rows()
    if not rows:
        return {"count": 0, "deal_rate": 0.0, "avg_ask": 0.0, "avg_valuation": 0.0, "avg_equity": 0.0}

    normalized = normalize_industry(industry)
    filtered: list[dict] = []
    for row in rows:
        source_industry = KAGGLE_TO_INSIGHT_INDUSTRY.get(row.get("Industry", ""), row.get("Industry", "Other"))
        if normalize_industry(source_industry) == normalized:
            filtered.append(row)

    if not filtered:
        return {"count": 0, "deal_rate": 0.0, "avg_ask": 0.0, "avg_valuation": 0.0, "avg_equity": 0.0}

    deals = [1 if row.get("Got Deal", "").strip() == "1" else 0 for row in filtered]
    asks = [_safe_float(row.get("Original Ask Amount", "")) for row in filtered]
    vals = [_safe_float(row.get("Valuation Requested", "")) for row in filtered]
    equities = [_safe_float(row.get("Original Offered Equity", "")) for row in filtered]

    return {
        "count": len(filtered),
        "deal_rate": round(sum(deals) / len(filtered), 4),
        "avg_ask": round(sum(asks) / len(asks), 2) if asks else 0.0,
        "avg_valuation": round(sum(vals) / len(vals), 2) if vals else 0.0,
        "avg_equity": round(sum(equities) / len(equities), 2) if equities else 0.0,
    }


def _srt_snapshot(industry: str, deals: list[dict]) -> dict:
    normalized = normalize_industry(industry)
    filtered = [d for d in deals if normalize_industry(d.get("industry", "Other")) == normalized]
    if not filtered:
        return {
            "count": 0,
            "success_rate_proxy": 0.0,
            "avg_revenue": 0.0,
            "avg_founder_confidence": 0.0,
            "avg_shark_enthusiasm": 0.0,
            "avg_objection_count": 0.0,
            "avg_negotiation_rounds": 0.0,
        }

    revenues = [float(d.get("revenue", 0.0) or 0.0) for d in filtered]
    confidences = [float(d.get("founder_confidence", 0.0) or 0.0) for d in filtered]
    enthusiasm = [float(d.get("shark_enthusiasm", 0.0) or 0.0) for d in filtered]
    objections = [float(d.get("objection_count", 0.0) or 0.0) for d in filtered]
    negotiations = [float(d.get("negotiation_rounds", 0.0) or 0.0) for d in filtered]
    successes = [1 if d.get("has_deal") else 0 for d in filtered]

    return {
        "count": len(filtered),
        "success_rate_proxy": round(sum(successes) / len(filtered), 4),
        "avg_revenue": round(sum(revenues) / len(revenues), 2) if revenues else 0.0,
        "avg_founder_confidence": round(sum(confidences) / len(confidences), 4) if confidences else 0.0,
        "avg_shark_enthusiasm": round(sum(enthusiasm) / len(enthusiasm), 4) if enthusiasm else 0.0,
        "avg_objection_count": round(sum(objections) / len(objections), 2) if objections else 0.0,
        "avg_negotiation_rounds": round(sum(negotiations) / len(negotiations), 2) if negotiations else 0.0,
    }


def _opportunities_and_risks(kaggle: dict, srt: dict) -> tuple[list[str], list[str]]:
    opportunities: list[str] = []
    risks: list[str] = []

    if kaggle["deal_rate"] >= 0.6:
        opportunities.append("Historical deal conversion in this industry is above 60% in the Kaggle labeled set.")
    elif kaggle["deal_rate"] > 0:
        risks.append("Historical deal conversion is modest; pricing and traction proof need to be stronger than peers.")

    if srt["avg_founder_confidence"] >= 0.35:
        opportunities.append("Founder confidence signals are strong in successful pitches, indicating narrative quality is a differentiator.")
    else:
        risks.append("Founder confidence signal is weak; narrative and credibility framing are likely bottlenecks.")

    if srt["avg_objection_count"] >= 3.0:
        risks.append("Objection pressure is high; due diligence depth and unit economics need tighter preparation.")
    else:
        opportunities.append("Objection intensity is comparatively low, creating space for faster negotiation cycles.")

    if srt["avg_negotiation_rounds"] >= 1.5:
        opportunities.append("Negotiation depth is high, suggesting investors engage when traction evidence is credible.")
    else:
        risks.append("Negotiation activity is limited; initial valuation/ask framing may be misaligned with investor expectations.")

    return opportunities[:4], risks[:4]


def _industry_health_score(kaggle: dict, srt: dict) -> float:
    score = 0.0
    score += 40 * kaggle["deal_rate"]
    score += 20 * min(srt["success_rate_proxy"], 1.0)
    score += 20 * min(max((srt["avg_founder_confidence"] + 1) / 2, 0.0), 1.0)
    score += 10 * min(srt["avg_shark_enthusiasm"] + 0.5, 1.0)
    score += 10 * max(0.0, 1.0 - (srt["avg_objection_count"] / 6.0))
    return round(max(0.0, min(100.0, score)), 1)


def _build_comparables(industry: str, deals: list[dict], top_k: int) -> list[dict]:
    normalized = normalize_industry(industry)
    filtered = [d for d in deals if normalize_industry(d.get("industry", "Other")) == normalized]
    ranked = sorted(
        filtered,
        key=lambda d: (
            1 if d.get("has_deal") else 0,
            float(d.get("revenue", 0) or 0),
            float(d.get("founder_confidence", 0) or 0),
        ),
        reverse=True,
    )
    results = []
    for d in ranked[:top_k]:
        results.append(
            {
                "company_name": d.get("company_name", "Unknown"),
                "episode": d.get("episode", ""),
                "revenue": float(d.get("revenue", 0.0) or 0.0),
                "founder_confidence": float(d.get("founder_confidence", 0.0) or 0.0),
                "objection_count": int(d.get("objection_count", 0) or 0),
                "has_deal": bool(d.get("has_deal", False)),
            }
        )
    return results


@lru_cache(maxsize=64)
def _news_signal_snapshot(industry: str) -> dict:
    """Mandatory market news signal feed for live recommendations."""
    api_key = os.environ.get("NEWSAPI_KEY")
    if not api_key:
        raise RuntimeError("NEWSAPI_KEY is required for insights endpoints.")

    try:
        params = {
            "q": f"{industry} startup market United States",
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 20,
            "apiKey": api_key,
        }
        with httpx.Client(timeout=5.0) as client:
            resp = client.get("https://newsapi.org/v2/everything", params=params)
            resp.raise_for_status()
            payload = resp.json()
    except Exception as exc:
        raise RuntimeError(f"NewsAPI fetch failed for {industry}: {exc}") from exc

    articles = payload.get("articles", []) or []
    if not articles:
        raise RuntimeError(f"NewsAPI returned no articles for query: {industry}")

    titles = " ".join((a.get("title", "") or "") for a in articles).lower()
    positive_markers = ("growth", "expands", "funding", "record", "surge", "demand")
    negative_markers = ("layoff", "decline", "slowdown", "regulatory", "drop", "risk")
    pos = sum(titles.count(token) for token in positive_markers)
    neg = sum(titles.count(token) for token in negative_markers)
    hint = "positive" if pos > neg else ("negative" if neg > pos else "neutral")
    alerts = []
    for article in articles[:8]:
        title = article.get("title", "") or "Untitled update"
        url = article.get("url", "")
        published = article.get("publishedAt", "")
        title_l = title.lower()
        impact = 0.5
        if any(t in title_l for t in ("funding", "record", "surge", "expands")):
            impact = 0.8
        if any(t in title_l for t in ("layoff", "decline", "drop", "regulatory")):
            impact = 0.3
        alerts.append(
            {
                "title": title,
                "url": url,
                "published_at": published,
                "impact_score": round(impact, 2),
            }
        )

    return {
        "status": "enabled",
        "articles_scanned": len(articles),
        "sentiment_hint": hint,
        "summary": f"Market sentiment from recent US news appears {hint}.",
        "alerts": alerts,
    }


def _confidence_from_coverage(kaggle_count: int, srt_count: int, articles_scanned: int) -> float:
    coverage_score = min(kaggle_count / 120, 1.0) * 0.45 + min(srt_count / 80, 1.0) * 0.35
    news_score = min(articles_scanned / 25, 1.0) * 0.2
    return round((coverage_score + news_score) * 100, 1)


def _news_sentiment_bonus(hint: str) -> float:
    if hint == "positive":
        return 0.06
    if hint == "negative":
        return -0.06
    return 0.0


def _confidence_level(score: float) -> str:
    if score >= 82:
        return "high"
    if score >= 63:
        return "medium"
    return "low"


def _common_citations(industry: str) -> list[dict]:
    return [
        {"source": "Kaggle shark-tank-us-dataset", "industry": industry, "fields": ["Got Deal", "Original Ask Amount", "Valuation Requested"]},
        {"source": "Shark Tank SRT Subtitles", "industry": industry, "fields": ["objection_count", "founder_confidence", "negotiation_rounds"]},
        {"source": "News APIs", "industry": industry, "fields": ["title", "publishedAt", "sentiment_hint"]},
    ]


def _top_drivers(driver_map: dict[str, float]) -> list[dict]:
    ordered = sorted(driver_map.items(), key=lambda x: abs(x[1]), reverse=True)[:5]
    return [{"driver": k, "impact": round(v, 4)} for k, v in ordered]


@lru_cache(maxsize=64)
def _transcript_behavior_snapshot(industry: str) -> dict:
    pitches = get_all_pitches()
    normalized = normalize_industry(industry)
    bucket: list[str] = []
    for pitch in pitches:
        if normalize_industry(classify_industry(pitch)) != normalized:
            continue
        segs = pitch.get("segments", {})
        text = " ".join(sum((segs.get(k, []) for k in ("founder_pitch", "shark_questions", "objections", "negotiation")), []))
        if text:
            bucket.append(text[:4000])
        if len(bucket) >= 120:
            break
    if not bucket:
        return {
            "avg_sentiment_score": 0.0,
            "avg_objection_score": 0.0,
            "avg_negotiation_strength": 0.0,
            "avg_traction_quality": 0.0,
            "source": "empty",
            "count": 0,
        }

    signals = [transcript_behavioral_features(t) for t in bucket]
    return {
        "avg_sentiment_score": round(sum(s["sentiment_score"] for s in signals) / len(signals), 4),
        "avg_objection_score": round(sum(s["objection_score"] for s in signals) / len(signals), 4),
        "avg_negotiation_strength": round(sum(s["negotiation_strength"] for s in signals) / len(signals), 4),
        "avg_traction_quality": round(sum(s["traction_quality"] for s in signals) / len(signals), 4),
        "source": signals[0]["source"],
        "count": len(signals),
    }


def _expected_scenario_panel(score: float, confidence: float, sentiment_hint: str) -> dict:
    optimism = 0.08 if sentiment_hint == "positive" else (-0.08 if sentiment_hint == "negative" else 0.0)
    base = max(0.0, min(1.0, score / 100))
    certainty = max(0.35, min(0.92, confidence / 100))
    bull = max(0.0, min(1.0, base + optimism + 0.12 * certainty))
    bear = max(0.0, min(1.0, base - optimism - 0.18 * (1 - certainty)))
    return {
        "if_we_invest_here": {
            "bull_case_success": round(bull * 100, 1),
            "base_case_success": round(base * 100, 1),
            "bear_case_success": round(bear * 100, 1),
            "commentary": "Scenario probabilities blend sector score, data coverage confidence, and live market tone.",
        }
    }


def build_vc_market_insight(
    industry: str,
    deals: list[dict],
    top_k: int = 5,
    risk_appetite: str = "balanced",
) -> dict:
    normalized = normalize_industry(industry)
    kaggle = _kaggle_snapshot(normalized)
    srt = _srt_snapshot(normalized, deals)
    transcript = _transcript_behavior_snapshot(normalized)
    opportunities, risks = _opportunities_and_risks(kaggle, srt)
    news = _news_signal_snapshot(normalized)
    health_score = _industry_health_score(kaggle, srt) + (_news_sentiment_bonus(news["sentiment_hint"]) * 100)
    health_score = round(max(0.0, min(100.0, health_score)), 1)
    comps = _build_comparables(normalized, deals, top_k=top_k)
    confidence_score = _confidence_from_coverage(kaggle["count"], srt["count"], int(news["articles_scanned"]))
    driver_map = {
        "historical_deal_rate": 0.34 * kaggle["deal_rate"],
        "transcript_success_proxy": 0.22 * srt["success_rate_proxy"],
        "founder_confidence_signal": 0.16 * min(max((srt["avg_founder_confidence"] + 1) / 2, 0.0), 1.0),
        "objection_pressure_penalty": -0.12 * min(srt["avg_objection_count"] / 6.0, 1.0),
        "live_news_momentum": _news_sentiment_bonus(news["sentiment_hint"]),
        "transformer_traction_quality": 0.14 * transcript["avg_traction_quality"],
        "transformer_negotiation_strength": 0.1 * transcript["avg_negotiation_strength"],
    }

    thesis = [
        f"{normalized} shows a historical labeled deal rate of {kaggle['deal_rate']:.0%} with {kaggle['count']} Kaggle records.",
        f"Transcript-derived proxy success is {srt['success_rate_proxy']:.0%} with avg objection count {srt['avg_objection_count']:.1f}.",
        f"Average pitch-side revenue signal in this industry is ${srt['avg_revenue']:,.0f}.",
    ]
    if risk_appetite == "aggressive":
        thesis.append("Aggressive profile: prioritize high-variance companies with strong enthusiasm and early growth signals.")
    elif risk_appetite == "conservative":
        thesis.append("Conservative profile: prioritize predictable revenue and low-objection comparables.")
    else:
        thesis.append("Balanced profile: mix traction quality with valuation discipline and negotiation depth.")

    return {
        "industry": normalized,
        "industry_health_score": health_score,
        "kpis": {
            "kaggle_deal_rate": kaggle["deal_rate"],
            "kaggle_avg_ask": kaggle["avg_ask"],
            "kaggle_avg_valuation": kaggle["avg_valuation"],
            "srt_success_rate_proxy": srt["success_rate_proxy"],
            "srt_avg_revenue": srt["avg_revenue"],
            "srt_avg_founder_confidence": srt["avg_founder_confidence"],
            "srt_avg_shark_enthusiasm": srt["avg_shark_enthusiasm"],
            "srt_avg_objection_count": srt["avg_objection_count"],
            "transformer_avg_sentiment": transcript["avg_sentiment_score"],
            "transformer_avg_objection": transcript["avg_objection_score"],
            "transformer_avg_negotiation_strength": transcript["avg_negotiation_strength"],
            "transformer_avg_traction_quality": transcript["avg_traction_quality"],
        },
        "thesis": thesis,
        "opportunities": opportunities,
        "risks": risks,
        "comparable_companies": comps,
        "news_signals": news,
        "confidence_score": confidence_score,
        "recommendation": {
            "score": health_score,
            "top_5_drivers": _top_drivers(driver_map),
            "risks": risks[:5],
            "comparable_companies": comps[:5],
            "confidence_level": _confidence_level(confidence_score),
            "citations": _common_citations(normalized),
        },
        "trend_alerts": news.get("alerts", []),
        "expected_scenario": _expected_scenario_panel(health_score, confidence_score, news["sentiment_hint"]),
        "citations": _common_citations(normalized),
        "model_stack": model_stack_status(),
        "data_sources": [
            {"source": "Kaggle shark-tank-us-dataset", "type": "Structured CSV", "purpose": "Deal outcomes, ask/equity/valuation baselines"},
            {"source": "Shark Tank SRT Subtitles", "type": "Unstructured text", "purpose": "Pitch dialogue, objections, negotiation behavior, confidence signals"},
            {"source": "News APIs", "type": "Streaming text", "purpose": "US market timing, competitive moves, category trends"},
        ],
    }


def _estimate_stage(revenue: float) -> str:
    if revenue >= 5_000_000:
        return "growth"
    if revenue >= 500_000:
        return "early-scale"
    if revenue >= 100_000:
        return "early-revenue"
    return "pre-scale"


def _rank_us_markets(
    industry: str,
    business_model: str,
    revenue: float,
    monthly_burn: float,
    growth_rate_qoq: float,
) -> tuple[list[dict], dict]:
    normalized = normalize_industry(industry)
    priors = INDUSTRY_MARKET_PRIORS.get(normalized, INDUSTRY_MARKET_PRIORS["Other"])
    news = _news_signal_snapshot(normalized)
    news_bonus = _news_sentiment_bonus(news["sentiment_hint"])

    # Base weights optimized for startup expansion decisions in US context.
    weights = {
        "talent": 0.22,
        "capital_access": 0.24,
        "enterprise_access": 0.18,
        "consumer_access": 0.16,
        "cost_efficiency": 0.14,
        "logistics": 0.06,
    }
    if business_model == "b2b":
        weights["enterprise_access"] += 0.08
        weights["consumer_access"] -= 0.05
    elif business_model == "b2c":
        weights["consumer_access"] += 0.1
        weights["enterprise_access"] -= 0.06

    if monthly_burn > 150_000 and revenue < 500_000:
        weights["cost_efficiency"] += 0.08
        weights["capital_access"] -= 0.04
    if growth_rate_qoq >= 0.15:
        weights["capital_access"] += 0.05
        weights["talent"] += 0.04

    ranked = []
    for market in US_MARKETS:
        strengths = market["strengths"]
        score = 0.0
        for dimension, weight in weights.items():
            dim_score = strengths.get(dimension, 0.5)
            multiplier = priors.get(dimension, 1.0)
            score += weight * dim_score * multiplier

        score = max(0.0, min(1.0, score + news_bonus))
        reasons = []
        if strengths["capital_access"] >= 0.85:
            reasons.append("strong investor density for fundraising")
        if strengths["talent"] >= 0.85:
            reasons.append("deep talent pool for execution speed")
        if strengths["cost_efficiency"] >= 0.75:
            reasons.append("better cost runway for capital efficiency")
        if strengths["consumer_access"] >= 0.85:
            reasons.append("large and testable consumer demand")
        if strengths["enterprise_access"] >= 0.82:
            reasons.append("strong enterprise buyer concentration")
        if not reasons:
            reasons.append("balanced market profile across capital, talent, and demand")

        ranked.append(
            {
                "market": market["name"],
                "region": market["region"],
                "fit_score": round(score * 100, 1),
                "rationale": "; ".join(reasons[:2]),
                "confidence": _confidence_from_coverage(80, 60, int(news["articles_scanned"])),
                "score": round(score * 100, 1),
                "top_5_drivers": _top_drivers(
                    {
                        "capital_access": weights.get("capital_access", 0) * strengths.get("capital_access", 0.5),
                        "talent": weights.get("talent", 0) * strengths.get("talent", 0.5),
                        "enterprise_access": weights.get("enterprise_access", 0) * strengths.get("enterprise_access", 0.5),
                        "consumer_access": weights.get("consumer_access", 0) * strengths.get("consumer_access", 0.5),
                        "cost_efficiency": weights.get("cost_efficiency", 0) * strengths.get("cost_efficiency", 0.5),
                        "news_momentum": _news_sentiment_bonus(news["sentiment_hint"]),
                    }
                ),
                "risks": [
                    "High operating cost pressure" if strengths["cost_efficiency"] < 0.45 else "Execution complexity in dense market",
                    "Competitive intensity risk",
                ],
                "comparable_companies": [],
                "confidence_level": _confidence_level(_confidence_from_coverage(80, 60, int(news["articles_scanned"]))),
                "citations": _common_citations(normalized),
            }
        )

    ranked.sort(key=lambda x: x["fit_score"], reverse=True)
    return ranked[:5], news


def _sector_similarity(base_industry: str, candidate: str) -> float:
    if candidate == base_industry:
        return 1.0
    adjacent = SECTOR_ADJACENCY.get(base_industry, [])
    if candidate in adjacent:
        return 0.78
    return 0.56


def _rank_growth_avenues(
    base_industry: str,
    business_model: str,
    gross_margin_pct: Optional[float],
    monthly_burn: float,
    growth_rate_qoq: float,
) -> list[dict]:
    priors = INDUSTRY_MARKET_PRIORS.get(base_industry, INDUSTRY_MARKET_PRIORS["Other"])
    enterprise = priors.get("enterprise_access", 1.0)
    consumer = priors.get("consumer_access", 1.0)
    logistics = priors.get("logistics", 1.0)
    margin = (gross_margin_pct or 50) / 100

    ranked: list[dict] = []
    for avenue in US_GROWTH_AVENUES:
        rules = avenue["fit_rules"]
        score = 0.52
        if business_model == "b2b":
            score += rules.get("b2b_bonus", 0.0)
        if business_model == "b2c":
            score += rules.get("b2c_bonus", 0.0)
        score += rules.get("consumer_bonus", 0.0) * consumer
        score += rules.get("enterprise_bonus", 0.0) * enterprise
        score += rules.get("logistics_bonus", 0.0) * logistics
        score += rules.get("tech_bonus", 0.0) * (1.0 if base_industry == "Technology" else 0.7)
        score += rules.get("margin_bonus", 0.0) * margin
        score += rules.get("growth_bonus", 0.0) * max(growth_rate_qoq, 0.0)
        if monthly_burn > 120_000:
            score += rules.get("burn_penalty_relief", 0.0)

        score = max(0.0, min(1.0, score))
        ranked.append(
            {
                "avenue": avenue["avenue"],
                "fit_score": round(score * 100, 1),
                "confidence": round((60 + score * 30), 1),
                "reason": avenue["description"],
                "score": round(score * 100, 1),
                "top_5_drivers": _top_drivers(
                    {
                        "business_model_alignment": rules.get("b2b_bonus", 0.0) if business_model == "b2b" else rules.get("b2c_bonus", 0.0),
                        "margin_support": rules.get("margin_bonus", 0.0) * margin,
                        "growth_signal": rules.get("growth_bonus", 0.0) * max(growth_rate_qoq, 0.0),
                        "enterprise_fit": rules.get("enterprise_bonus", 0.0) * enterprise,
                        "consumer_fit": rules.get("consumer_bonus", 0.0) * consumer,
                    }
                ),
                "risks": [
                    "Channel concentration risk if single partner dominates",
                    "Execution risk if CAC payback is not monitored weekly",
                ],
                "comparable_companies": [],
                "confidence_level": _confidence_level(round((60 + score * 30), 1)),
                "citations": _common_citations(base_industry),
            }
        )

    ranked.sort(key=lambda x: x["fit_score"], reverse=True)
    return ranked


def build_market_fit_recommender(
    industry: str,
    business_model: str,
    revenue_trailing_12m: float,
    monthly_burn: float,
    growth_rate_qoq: float,
    gross_margin_pct: Optional[float],
    deals: list[dict],
    top_k: int = 5,
) -> dict:
    base_industry = normalize_industry(industry)
    geo_rankings, _ = _rank_us_markets(
        industry=base_industry,
        business_model=business_model,
        revenue=revenue_trailing_12m,
        monthly_burn=monthly_burn,
        growth_rate_qoq=growth_rate_qoq,
    )

    sector_rankings: list[dict] = []
    candidates = [s for s in INDUSTRY_MARKET_PRIORS.keys() if s != "Other"]
    for candidate in candidates:
        kaggle = _kaggle_snapshot(candidate)
        srt = _srt_snapshot(candidate, deals)
        news = _news_signal_snapshot(candidate)
        similarity = _sector_similarity(base_industry, candidate)
        traction = min(revenue_trailing_12m / 1_000_000, 1.0)
        burn_pressure = min(monthly_burn / max(revenue_trailing_12m / 12, 1), 3.0) / 3.0 if revenue_trailing_12m > 0 else 1.0

        score = 0.34 * kaggle["deal_rate"]
        score += 0.24 * srt["success_rate_proxy"]
        score += 0.16 * similarity
        score += 0.1 * traction
        score += 0.08 * max(0.0, 1.0 - burn_pressure)
        score += _news_sentiment_bonus(news["sentiment_hint"])
        score = max(0.0, min(1.0, score))

        reasons = [
            f"Historical deal rate: {kaggle['deal_rate']:.0%} across {kaggle['count']} labeled cases.",
            f"SRT success proxy: {srt['success_rate_proxy']:.0%} with avg objections {srt['avg_objection_count']:.1f}.",
            f"News sentiment for this sector is {news['sentiment_hint']}.",
        ]
        confidence = _confidence_from_coverage(kaggle["count"], srt["count"], int(news["articles_scanned"]))
        comps = _build_comparables(candidate, deals, top_k=5)
        driver_map = {
            "historical_deal_rate": 0.34 * kaggle["deal_rate"],
            "transcript_success_proxy": 0.24 * srt["success_rate_proxy"],
            "sector_similarity": 0.16 * similarity,
            "revenue_traction_fit": 0.1 * traction,
            "burn_efficiency": 0.08 * max(0.0, 1.0 - burn_pressure),
            "news_momentum": _news_sentiment_bonus(news["sentiment_hint"]),
        }

        sector_rankings.append(
            {
                "sector": candidate,
                "fit_score": round(score * 100, 1),
                "confidence": confidence,
                "reasons": reasons,
                "score": round(score * 100, 1),
                "top_5_drivers": _top_drivers(driver_map),
                "risks": [
                    "Category saturation risk" if score < 0.62 else "Execution speed risk in high-opportunity sector",
                    "Capital intensity may increase as competition rises",
                ],
                "comparable_companies": comps,
                "confidence_level": _confidence_level(confidence),
                "citations": _common_citations(candidate),
            }
        )

    sector_rankings.sort(key=lambda x: x["fit_score"], reverse=True)
    sector_rankings = sector_rankings[:top_k]

    avenue_rankings = _rank_growth_avenues(
        base_industry=base_industry,
        business_model=business_model,
        gross_margin_pct=gross_margin_pct,
        monthly_burn=monthly_burn,
        growth_rate_qoq=growth_rate_qoq,
    )[:top_k]

    return {
        "input_industry": base_industry,
        "business_model": business_model,
        "sector_rankings": sector_rankings,
        "avenue_rankings": avenue_rankings,
        "geo_rankings": geo_rankings[:top_k],
        "recommendations": (sector_rankings + avenue_rankings + geo_rankings[:top_k])[:top_k],
        "summary": (
            f"Top sector fit opportunities are ranked for a {base_industry} startup with "
            f"${revenue_trailing_12m:,.0f} trailing revenue and {growth_rate_qoq:.0%} QoQ growth."
        ),
        "citations": _common_citations(base_industry),
        "model_stack": model_stack_status(),
        "data_sources": [
            {"source": "Kaggle shark-tank-us-dataset", "type": "Structured CSV", "purpose": "Cross-sector conversion and valuation baselines"},
            {"source": "Shark Tank SRT Subtitles", "type": "Unstructured text", "purpose": "Sector-level dialogue and negotiation pattern signals"},
            {"source": "News APIs", "type": "Streaming text", "purpose": "Real-time US category sentiment and trend momentum"},
        ],
    }


def build_startup_strategy(
    company_name: str,
    industry: str,
    ask_amount: float,
    equity_offered_pct: float,
    revenue_trailing_12m: float,
    founder_count: int,
    deal_probability: float,
    growth_rate_qoq: float = 0.0,
    monthly_burn: float = 0.0,
    gross_margin_pct: Optional[float] = None,
    business_model: str = "hybrid",
    objection_count: int = 0,
    price_change_pct: float = 0.0,
    gtm_efficiency_delta: float = 0.0,
    cac_delta: float = 0.0,
    hiring_plan_delta: float = 0.0,
    localization_readiness: float = 0.5,
) -> dict:
    stage = _estimate_stage(revenue_trailing_12m)
    readiness_raw = 100 * deal_probability
    readiness_raw += min(max(growth_rate_qoq, -0.2), 0.4) * 35
    readiness_raw += 4 if founder_count > 1 else 0
    readiness_raw -= min(objection_count, 8) * 1.8
    if monthly_burn > 0:
        runway_pressure = monthly_burn / max(revenue_trailing_12m / 12, 1)
        readiness_raw -= min(runway_pressure, 3.0) * 4.0
    if gross_margin_pct is not None:
        readiness_raw += (gross_margin_pct - 45) * 0.18
    readiness_score = int(max(1, min(100, round(readiness_raw))))

    strengths: list[str] = []
    gaps: list[str] = []
    recommendations: list[str] = []

    if deal_probability >= 0.65:
        strengths.append("Predicted deal probability is strong for this profile.")
    else:
        gaps.append("Predicted deal probability is below target for high-confidence fundraising.")

    if revenue_trailing_12m >= 1_000_000:
        strengths.append("Revenue traction is in a range that supports institutional diligence.")
    else:
        gaps.append("Revenue signal is still light versus top-performing comparables.")

    implied_valuation = ask_amount / max(equity_offered_pct / 100, 0.01)
    if revenue_trailing_12m > 0 and implied_valuation > (6 * revenue_trailing_12m):
        gaps.append("Valuation-to-revenue multiple is aggressive for current traction.")
        recommendations.append("Reframe valuation using milestone-based tranches or lower the initial ask.")
    else:
        strengths.append("Valuation framing is reasonably aligned with current traction.")

    if monthly_burn > 0 and revenue_trailing_12m > 0:
        burn_multiple = monthly_burn / max(revenue_trailing_12m / 12, 1)
        if burn_multiple > 1.4:
            gaps.append("Burn profile is high relative to current revenue base.")
            recommendations.append("Prioritize efficiency levers before scaling paid acquisition.")

    if gross_margin_pct is not None and gross_margin_pct < 40:
        gaps.append("Gross margin profile may reduce investor confidence on scalability.")
        recommendations.append("Improve contribution margin through pricing, mix, or COGS negotiations.")

    if founder_count <= 1:
        recommendations.append("Add visible functional depth (product/go-to-market/ops) to reduce execution risk.")
    if growth_rate_qoq < 0.05:
        recommendations.append("Demonstrate stronger quarter-over-quarter momentum before major fundraising.")

    market_recos, news = _rank_us_markets(
        industry=industry,
        business_model=business_model,
        revenue=revenue_trailing_12m,
        monthly_burn=monthly_burn,
        growth_rate_qoq=growth_rate_qoq,
    )

    if not recommendations:
        recommendations.append("Maintain current positioning and focus on scaling channels with the best payback.")

    normalized = normalize_industry(industry)
    comps = _build_comparables(normalized, deals, top_k=5) if (deals := get_deals(limit=5000, industry=normalized).get("deals", [])) else []
    driver_map = {
        "deal_probability_baseline": deal_probability,
        "growth_rate_qoq": min(max(growth_rate_qoq, -0.2), 0.4),
        "gross_margin_signal": (gross_margin_pct or 45) / 100,
        "burn_efficiency": max(0.0, 1.0 - (monthly_burn / max(revenue_trailing_12m / 12, 1)) / 3.0) if monthly_burn > 0 else 0.5,
        "team_depth": 0.75 if founder_count > 1 else 0.35,
        "objection_penalty": -min(objection_count, 8) / 10,
    }
    scenario_testing = []
    scenario_inputs = [
        ("Price optimization", price_change_pct, 0.18),
        ("GTM efficiency", gtm_efficiency_delta, 0.2),
        ("CAC control", -cac_delta, 0.16),
        ("Hiring velocity", hiring_plan_delta, 0.1),
        ("Localization readiness", localization_readiness - 0.5, 0.14),
    ]
    for name, delta, weight in scenario_inputs:
        scenario_score = max(0.0, min(100.0, readiness_score + (delta * 100 * weight)))
        scenario_testing.append(
            {
                "scenario": name,
                "input_delta": round(delta, 3),
                "projected_readiness_score": round(scenario_score, 1),
                "confidence": round(max(58.0, min(92.0, 70 + weight * 60)), 1),
            }
        )

    checklist = [
        {"item": "Tighten valuation narrative vs revenue multiple", "status": "done" if implied_valuation <= (6 * max(revenue_trailing_12m, 1)) else "pending"},
        {"item": "Document repeatable GTM motion with payback targets", "status": "done" if growth_rate_qoq >= 0.08 else "pending"},
        {"item": "Reduce burn multiple below 1.4x monthly revenue", "status": "done" if monthly_burn <= max(revenue_trailing_12m / 12, 1) * 1.4 else "pending"},
        {"item": "Prepare localization playbook for next US region", "status": "done" if localization_readiness >= 0.6 else "pending"},
        {"item": "Strengthen hiring plan for scaling stage", "status": "done" if founder_count > 1 else "pending"},
    ]

    rec_object = {
        "score": readiness_score,
        "top_5_drivers": _top_drivers(driver_map),
        "risks": gaps[:5],
        "comparable_companies": comps[:5],
        "confidence_level": _confidence_level(float(np.mean([m["confidence"] for m in market_recos])) if market_recos else 65),
        "citations": _common_citations(normalized),
    }

    return {
        "company_name": company_name,
        "industry": normalized,
        "stage": stage,
        "deal_probability": round(deal_probability, 4),
        "readiness_score": readiness_score,
        "strengths": strengths[:4],
        "gaps": gaps[:4],
        "recommendations": recommendations[:6],
        "us_market_recommendations": market_recos,
        "news_signals": news,
        "recommendation": rec_object,
        "improvement_checklist": checklist,
        "scenario_testing": scenario_testing,
        "comparable_companies": comps[:5],
        "citations": _common_citations(normalized),
        "model_stack": model_stack_status(),
        "data_sources": [
            {"source": "Kaggle shark-tank-us-dataset", "type": "Structured CSV", "purpose": "Outcome and valuation baselines"},
            {"source": "Shark Tank SRT Subtitles", "type": "Unstructured text", "purpose": "Dialogue-level confidence and objection signals"},
            {"source": "News APIs", "type": "Streaming text", "purpose": "US market timing overlays"},
        ],
    }
