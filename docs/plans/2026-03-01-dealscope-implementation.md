# DealScope Redesign Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rebrand SharkTank AI Engine to DealScope — an AI-powered BI platform with app shell, dashboard, market analysis, research agent, and deal explorer.

**Architecture:** Next.js 16 App Router with route groups: `(marketing)` for landing page, `(app)` for authenticated app shell with sidebar. FastAPI backend extended with `/data/industries`, `/data/deals`, and `/agent/research` endpoints. Research agent uses Claude tool-calling with SSE streaming.

**Tech Stack:** Next.js 16, TypeScript, Tailwind v4, Framer Motion, Recharts, Lucide React, FastAPI, XGBoost, Anthropic Claude API

**Design Doc:** `docs/plans/2026-03-01-dealscope-redesign-design.md`

---

## Task 1: Backend — Industries & Deals Endpoints

Add two new API endpoints that the frontend dashboard, market analysis, and deal explorer pages need.

**Files:**
- Modify: `src/data/cache.py`
- Modify: `src/api/schemas.py`
- Modify: `src/api/main.py`
- Test: `tests/test_api_new_endpoints.py`

**Step 1: Write failing tests**

Create `tests/test_api_new_endpoints.py`:

```python
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
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_api_new_endpoints.py -v`
Expected: FAIL (404 for /data/industries and /data/deals)

**Step 3: Add industry classification to cache.py**

Add to `src/data/cache.py` after the `get_stats()` function (after line 105):

```python
# Industry keyword mapping for classifying pitches from SRT data
INDUSTRY_KEYWORDS = {
    "Food & Beverage": ["food", "restaurant", "cook", "kitchen", "recipe", "drink", "beverage", "snack", "sauce", "spice", "meal", "eat", "chef", "bakery", "candy", "chocolate"],
    "Technology": ["app", "software", "tech", "digital", "online", "platform", "website", "internet", "computer", "ai", "data", "cloud", "saas"],
    "Health & Wellness": ["health", "medical", "wellness", "vitamin", "supplement", "therapy", "doctor", "patient", "organic", "natural", "cbd", "hemp"],
    "Fashion & Beauty": ["fashion", "clothing", "beauty", "cosmetic", "makeup", "skin", "hair", "jewelry", "accessories", "dress", "wear", "style"],
    "Home & Garden": ["home", "house", "garden", "furniture", "decor", "clean", "storage", "organize", "kitchen", "bathroom"],
    "Children & Education": ["kid", "child", "baby", "toy", "education", "learn", "school", "parent", "family"],
    "Fitness & Sports": ["fitness", "gym", "workout", "exercise", "sport", "athletic", "training", "yoga"],
    "Entertainment": ["entertainment", "game", "music", "movie", "party", "fun", "play", "media"],
    "Automotive": ["car", "auto", "vehicle", "motor", "drive", "truck"],
    "Pet Products": ["pet", "dog", "cat", "animal"],
}


def classify_industry(pitch: dict) -> str:
    """Classify a pitch into an industry based on segment text."""
    text_parts = []
    for seg_name in ["founder_pitch", "product_demo"]:
        seg = pitch.get("segments", {}).get(seg_name, [])
        if isinstance(seg, list):
            text_parts.extend(seg)
    text = " ".join(text_parts).lower()

    scores: dict[str, int] = {}
    for industry, keywords in INDUSTRY_KEYWORDS.items():
        scores[industry] = sum(1 for kw in keywords if kw in text)

    best = max(scores, key=scores.get)  # type: ignore
    return best if scores[best] > 0 else "Other"


def get_industries() -> list[dict]:
    """Get industry-level aggregate stats."""
    pitches = get_all_pitches()
    industry_data: dict[str, list[dict]] = {}
    for pitch in pitches:
        ind = classify_industry(pitch)
        industry_data.setdefault(ind, []).append(pitch)

    result = []
    for industry, ind_pitches in sorted(industry_data.items()):
        revenues = [p["signals"]["revenue_mentioned"] for p in ind_pitches if p["signals"]["revenue_mentioned"] > 0]
        asks = [p["signals"]["revenue_mentioned"] for p in ind_pitches]  # approximation
        has_negotiation = [p for p in ind_pitches if p["signals"]["negotiation_rounds"] > 0]
        result.append({
            "industry": industry,
            "deal_count": len(ind_pitches),
            "success_rate": round(len(has_negotiation) / len(ind_pitches), 4) if ind_pitches else 0,
            "avg_ask": round(sum(revenues) / len(revenues), 2) if revenues else 0,
            "avg_revenue": round(sum(revenues) / len(revenues), 2) if revenues else 0,
            "avg_equity": 0,  # not available from SRT data alone
            "avg_valuation": 0,
            "pitch_count": len(ind_pitches),
        })
    return result


def get_deals(
    limit: int = 50,
    offset: int = 0,
    industry: str | None = None,
    has_deal: bool | None = None,
    search: str | None = None,
    min_revenue: float | None = None,
    max_revenue: float | None = None,
) -> dict:
    """Get filterable, paginated deal list."""
    pitches = get_all_pitches()

    # Enrich with industry
    enriched = []
    for p in pitches:
        deal = {
            "episode": p["episode"],
            "company_name": p.get("entrepreneur_name", "Unknown"),
            "industry": classify_industry(p),
            "season": p["episode"][:3] if p.get("episode") else "",
            "revenue": p["signals"]["revenue_mentioned"],
            "objection_count": p["signals"]["objection_count"],
            "negotiation_rounds": p["signals"]["negotiation_rounds"],
            "founder_confidence": p["signals"]["founder_confidence"],
            "shark_enthusiasm": p["signals"]["shark_enthusiasm_max"],
            "has_deal": p["signals"]["negotiation_rounds"] > 0,
        }
        enriched.append(deal)

    # Apply filters
    filtered = enriched
    if industry:
        filtered = [d for d in filtered if d["industry"] == industry]
    if has_deal is not None:
        filtered = [d for d in filtered if d["has_deal"] == has_deal]
    if search:
        search_lower = search.lower()
        filtered = [d for d in filtered if search_lower in d["company_name"].lower()]
    if min_revenue is not None:
        filtered = [d for d in filtered if d["revenue"] >= min_revenue]
    if max_revenue is not None:
        filtered = [d for d in filtered if d["revenue"] <= max_revenue]

    return {"total": len(filtered), "deals": filtered[offset:offset + limit]}
```

**Step 4: Add API endpoints to main.py**

Add to `src/api/main.py` after the `/data/pitches` endpoint (after line 158), and add the imports:

Add import at top (after line 20):
```python
from src.data.cache import get_all_pitches, get_episodes, get_episode, get_stats, get_industries, get_deals
```
(Replace the existing import line that only imports `get_all_pitches, get_episodes, get_episode, get_stats`)

Add endpoints:
```python
@app.get("/data/industries")
def list_industries():
    """List all industries with aggregate stats."""
    return get_industries()


@app.get("/data/deals")
def list_deals(
    limit: int = 50,
    offset: int = 0,
    industry: str | None = None,
    has_deal: bool | None = None,
    search: str | None = None,
    min_revenue: float | None = None,
    max_revenue: float | None = None,
):
    """Filterable, paginated deal list."""
    return get_deals(
        limit=limit, offset=offset, industry=industry,
        has_deal=has_deal, search=search,
        min_revenue=min_revenue, max_revenue=max_revenue,
    )
```

**Step 5: Run tests to verify they pass**

Run: `pytest tests/test_api_new_endpoints.py -v`
Expected: ALL PASS

**Step 6: Commit**

```bash
git add src/data/cache.py src/api/main.py tests/test_api_new_endpoints.py
git commit -m "feat: add /data/industries and /data/deals endpoints for DealScope"
```

---

## Task 2: Backend — Research Agent Endpoint

Build the multi-step research agent with Claude tool-calling and SSE streaming.

**Files:**
- Create: `src/api/research_agent.py`
- Modify: `src/api/main.py`
- Test: `tests/test_research_agent.py`

**Step 1: Write failing tests**

Create `tests/test_research_agent.py`:

```python
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
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_research_agent.py -v`
Expected: FAIL (module not found)

**Step 3: Create research agent module**

Create `src/api/research_agent.py`:

```python
"""Multi-step research agent with Claude tool-calling and SSE streaming."""

from __future__ import annotations

import json
import os
from typing import Generator

from src.data.cache import get_all_pitches, get_industries, get_deals, classify_industry


# ── Tool implementations (no API keys needed) ──────────────────────────

def search_deals_tool(query: str, limit: int = 10) -> list[dict]:
    """Search deals by keyword matching across pitch text."""
    pitches = get_all_pitches()
    query_lower = query.lower()
    scored = []
    for p in pitches:
        text_parts = []
        for seg_name, seg_blocks in p.get("segments", {}).items():
            if isinstance(seg_blocks, list):
                text_parts.extend(seg_blocks)
        full_text = " ".join(text_parts).lower()
        # Simple relevance: count keyword occurrences
        relevance = full_text.count(query_lower)
        if relevance > 0:
            scored.append({
                "company_name": p.get("entrepreneur_name", "Unknown"),
                "episode": p["episode"],
                "industry": classify_industry(p),
                "revenue": p["signals"]["revenue_mentioned"],
                "negotiation_rounds": p["signals"]["negotiation_rounds"],
                "relevance": relevance,
                "snippet": full_text[:200],
            })
    scored.sort(key=lambda x: x["relevance"], reverse=True)
    return scored[:limit]


def get_market_stats_tool(industry: str | None = None) -> dict:
    """Get aggregate market statistics, optionally filtered by industry."""
    industries = get_industries()
    if industry:
        for ind in industries:
            if ind["industry"].lower() == industry.lower():
                return ind
        return {"industry": industry, "deal_count": 0, "error": "Industry not found"}
    return {
        "total_industries": len(industries),
        "industries": industries,
    }


def predict_deal_tool(ask_amount: float, equity_pct: float, revenue: float = 0) -> dict:
    """Run deal prediction model with given parameters."""
    implied_valuation = ask_amount / (equity_pct / 100) if equity_pct > 0 else 0
    revenue_score = min(revenue / 1_000_000, 1.0) * 0.4
    valuation_score = max(0, 1 - implied_valuation / 10_000_000) * 0.3
    sentiment_score = 0.5 * 0.3  # neutral default
    prob = max(0.05, min(0.95, revenue_score + valuation_score + sentiment_score))
    score = max(1, min(10, round(prob * 10)))

    strengths, risks = [], []
    if revenue > 500_000:
        strengths.append("Strong revenue traction")
    if equity_pct < 15:
        risks.append("Low equity offer may deter investors")
    if implied_valuation > 5_000_000 and revenue < 500_000:
        risks.append("High valuation relative to revenue")

    return {
        "deal_probability": round(prob, 4),
        "deal_score": score,
        "implied_valuation": round(implied_valuation, 2),
        "strengths": strengths,
        "risks": risks,
    }


def analyze_patterns_tool(industry: str, metric: str = "success_rate") -> dict:
    """Analyze cross-cutting patterns across deals."""
    deals_resp = get_deals(limit=1000, industry=industry)
    deals = deals_resp["deals"]
    if not deals:
        return {"industry": industry, "error": "No deals found"}

    revenues = [d["revenue"] for d in deals if d["revenue"] > 0]
    confidences = [d["founder_confidence"] for d in deals]
    success = [d for d in deals if d["has_deal"]]

    return {
        "industry": industry,
        "total_deals": len(deals),
        "success_count": len(success),
        "success_rate": round(len(success) / len(deals), 4) if deals else 0,
        "avg_revenue": round(sum(revenues) / len(revenues), 2) if revenues else 0,
        "median_revenue": round(sorted(revenues)[len(revenues) // 2], 2) if revenues else 0,
        "avg_confidence": round(sum(confidences) / len(confidences), 4) if confidences else 0,
        "top_companies": [d["company_name"] for d in sorted(deals, key=lambda x: x["revenue"], reverse=True)[:5]],
    }


# ── Claude tool definitions ────────────────────────────────────────────

AGENT_TOOLS = [
    {
        "name": "search_deals",
        "description": "Search the database of 741+ venture pitch deals by keyword. Returns matching deals with relevance scores.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search keyword or phrase"},
                "limit": {"type": "integer", "description": "Max results (default 10)", "default": 10},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_market_stats",
        "description": "Get aggregate market statistics for a specific industry or all industries. Returns deal counts, success rates, average metrics.",
        "input_schema": {
            "type": "object",
            "properties": {
                "industry": {"type": "string", "description": "Industry name to filter (e.g., 'Technology', 'Food & Beverage'). Omit for all industries."},
            },
        },
    },
    {
        "name": "predict_deal",
        "description": "Run the deal prediction model with specific pitch parameters. Returns probability score and risk assessment.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ask_amount": {"type": "number", "description": "Investment ask in USD"},
                "equity_pct": {"type": "number", "description": "Equity offered as percentage"},
                "revenue": {"type": "number", "description": "Trailing 12-month revenue in USD", "default": 0},
            },
            "required": ["ask_amount", "equity_pct"],
        },
    },
    {
        "name": "analyze_patterns",
        "description": "Analyze cross-cutting patterns in deal data for a specific industry. Returns success rates, revenue distributions, top companies.",
        "input_schema": {
            "type": "object",
            "properties": {
                "industry": {"type": "string", "description": "Industry to analyze"},
                "metric": {"type": "string", "description": "Focus metric: success_rate, revenue, valuation", "default": "success_rate"},
            },
            "required": ["industry"],
        },
    },
]

TOOL_MAP = {
    "search_deals": lambda args: search_deals_tool(**args),
    "get_market_stats": lambda args: get_market_stats_tool(**args),
    "predict_deal": lambda args: predict_deal_tool(**args),
    "analyze_patterns": lambda args: analyze_patterns_tool(**args),
}


SYSTEM_PROMPT = """You are DealScope Research Agent — an AI analyst specializing in venture deal intelligence.

You have access to a database of 741+ real venture pitches with detailed signals (revenue, sentiment, objections, negotiations). Use your tools to research the user's question thoroughly.

Research methodology:
1. Start by understanding what data is relevant to the question
2. Use search_deals to find specific companies or topics
3. Use get_market_stats to get industry-level aggregates
4. Use analyze_patterns for deeper cross-industry analysis
5. Use predict_deal to model hypothetical scenarios
6. Synthesize findings into actionable insights

Always cite specific data points and companies. Be quantitative. Focus on actionable business intelligence, not trivia."""


def run_research_stream(query: str, depth: str = "standard") -> Generator[dict, None, None]:
    """Execute the research agent with streaming tool calls.

    Yields dicts with type: "step" | "answer" | "error" | "done"
    """
    try:
        import anthropic
    except ImportError:
        yield {"type": "error", "data": "anthropic package not installed"}
        return

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        # Fallback: do basic research without Claude
        yield from _fallback_research(query)
        return

    client = anthropic.Anthropic(api_key=api_key)
    messages = [{"role": "user", "content": query}]
    max_turns = 8 if depth == "deep" else 4

    for turn in range(max_turns):
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=AGENT_TOOLS,
            messages=messages,
        )

        # Process each content block
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                tool_name = block.name
                tool_input = block.input

                yield {
                    "type": "tool_call",
                    "tool": tool_name,
                    "input": tool_input,
                    "status": "running",
                }

                # Execute tool
                tool_fn = TOOL_MAP.get(tool_name)
                if tool_fn:
                    result = tool_fn(tool_input)
                else:
                    result = {"error": f"Unknown tool: {tool_name}"}

                yield {
                    "type": "tool_result",
                    "tool": tool_name,
                    "result": result,
                    "status": "complete",
                }

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                })

            elif block.type == "text" and block.text.strip():
                if response.stop_reason == "end_turn":
                    yield {"type": "answer", "content": block.text}
                else:
                    yield {"type": "thinking", "content": block.text}

        if response.stop_reason == "end_turn":
            break

        if tool_results:
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

    yield {"type": "done"}


def _fallback_research(query: str) -> Generator[dict, None, None]:
    """Basic research without Claude API — uses keyword matching."""
    query_lower = query.lower()

    # Step 1: Search deals
    yield {"type": "tool_call", "tool": "search_deals", "input": {"query": query_lower}, "status": "running"}
    deals = search_deals_tool(query_lower, limit=10)
    yield {"type": "tool_result", "tool": "search_deals", "result": deals, "status": "complete"}

    # Step 2: Get market stats
    yield {"type": "tool_call", "tool": "get_market_stats", "input": {}, "status": "running"}
    stats = get_market_stats_tool()
    yield {"type": "tool_result", "tool": "get_market_stats", "result": stats, "status": "complete"}

    # Build summary
    deal_count = len(deals)
    industries = stats.get("industries", [])
    total = sum(i["deal_count"] for i in industries) if industries else 0

    answer_parts = [
        f"## Research Results for: \"{query}\"\n",
        f"Found **{deal_count}** matching deals across our database of {total} total pitches.\n",
    ]
    if deals:
        answer_parts.append("### Top Matching Companies\n")
        for d in deals[:5]:
            answer_parts.append(f"- **{d['company_name']}** ({d['episode']}) — {d['industry']}, Revenue: ${d['revenue']:,.0f}\n")

    if industries:
        answer_parts.append("\n### Industry Breakdown\n")
        for ind in sorted(industries, key=lambda x: x["deal_count"], reverse=True)[:5]:
            answer_parts.append(f"- **{ind['industry']}**: {ind['deal_count']} deals, {ind['success_rate']:.0%} success rate\n")

    yield {"type": "answer", "content": "".join(answer_parts)}
    yield {"type": "done"}
```

**Step 4: Wire up SSE endpoint in main.py**

Add to `src/api/main.py` after the existing `/analyze/stream` endpoint:

```python
@app.get("/agent/research")
async def research_stream_endpoint(query: str, depth: str = "standard"):
    """SSE streaming research agent endpoint."""
    from src.api.research_agent import run_research_stream

    def event_generator():
        try:
            for chunk in run_research_stream(query, depth=depth):
                event_data = json_module.dumps(chunk)
                yield f"data: {event_data}\n\n"
        except Exception as e:
            error_data = json_module.dumps({"type": "error", "data": str(e)})
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )
```

**Step 5: Run tests to verify they pass**

Run: `pytest tests/test_research_agent.py -v`
Expected: ALL PASS

**Step 6: Commit**

```bash
git add src/api/research_agent.py src/api/main.py tests/test_research_agent.py
git commit -m "feat: add research agent with tool-calling and SSE streaming"
```

---

## Task 3: Frontend — Rebrand & Route Structure

Set up the new DealScope branding, route groups, and app shell layout with sidebar.

**Files:**
- Modify: `frontend/src/app/layout.tsx` (rebrand metadata)
- Modify: `frontend/src/app/globals.css` (add sidebar/app styles)
- Create: `frontend/src/app/(marketing)/layout.tsx`
- Create: `frontend/src/app/(marketing)/page.tsx` (move landing)
- Create: `frontend/src/app/(app)/layout.tsx` (app shell with sidebar)
- Create: `frontend/src/app/(app)/page.tsx` (dashboard redirect)
- Create: `frontend/src/components/layout/Sidebar.tsx`
- Create: `frontend/src/components/layout/AppTopBar.tsx`

**Step 1: Update root layout metadata**

In `frontend/src/app/layout.tsx`, change metadata title to "DealScope — AI-Powered Business Intelligence" and description to "Turn venture pitch data into actionable business intelligence." Remove the Navbar import since marketing and app layouts will handle their own nav.

```tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "DealScope — AI-Powered Business Intelligence",
  description: "Turn venture pitch data into actionable business intelligence.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-[var(--bg-primary)] text-white antialiased`}>
        {children}
      </body>
    </html>
  );
}
```

**Step 2: Add new CSS utilities to globals.css**

Append to `frontend/src/app/globals.css`:

```css
/* Sidebar */
.sidebar {
  background: rgba(10, 10, 20, 0.95);
  backdrop-filter: blur(20px);
  border-right: 1px solid rgba(255, 255, 255, 0.06);
}

.sidebar-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  border-radius: 10px;
  color: rgba(255, 255, 255, 0.5);
  transition: all 0.2s;
  font-size: 14px;
}

.sidebar-item:hover {
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.8);
}

.sidebar-item.active {
  background: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
}

/* Scrollbar styling */
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.2);
}

/* KPI Card */
.kpi-card {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  padding: 20px;
}
```

**Step 3: Create marketing route group layout**

Create `frontend/src/app/(marketing)/layout.tsx`:

```tsx
import Navbar from "@/components/layout/Navbar";

export default function MarketingLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <Navbar />
      <main className="pt-16">{children}</main>
    </>
  );
}
```

**Step 4: Move landing page**

Create `frontend/src/app/(marketing)/page.tsx` — this will be a brand-new landing page (built in Task 4). For now, create a placeholder that imports from the old page.

```tsx
export { default } from "@/app/page-legacy";
```

Rename the current `frontend/src/app/page.tsx` to `frontend/src/app/page-legacy.tsx` temporarily. Then create a new `frontend/src/app/page.tsx` that redirects:

Actually, with Next.js route groups, the `(marketing)/page.tsx` IS the `/` route. So we need to:

1. Move `frontend/src/app/page.tsx` content to `frontend/src/app/(marketing)/page.tsx`
2. Delete `frontend/src/app/page.tsx` (the route group takes over)

```bash
mkdir -p frontend/src/app/\(marketing\)
mv frontend/src/app/page.tsx frontend/src/app/\(marketing\)/page.tsx
```

**Step 5: Create Sidebar component**

Create `frontend/src/components/layout/Sidebar.tsx`:

```tsx
"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard,
  TrendingUp,
  SlidersHorizontal,
  Bot,
  Search,
  ChevronLeft,
  ChevronRight,
  Zap,
} from "lucide-react";

const NAV_ITEMS = [
  { href: "/app", icon: LayoutDashboard, label: "Dashboard" },
  { href: "/app/market", icon: TrendingUp, label: "Market Analysis" },
  { href: "/app/simulator", icon: SlidersHorizontal, label: "Deal Simulator" },
  { href: "/app/agent", icon: Bot, label: "Research Agent" },
  { href: "/app/deals", icon: Search, label: "Deal Explorer" },
];

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const pathname = usePathname();

  const isActive = (href: string) => {
    if (href === "/app") return pathname === "/app";
    return pathname.startsWith(href);
  };

  return (
    <aside
      className={`sidebar fixed left-0 top-0 h-screen z-40 flex flex-col transition-all duration-300 ${
        collapsed ? "w-16" : "w-60"
      }`}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 h-16 border-b border-white/5">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center flex-shrink-0">
          <Zap size={18} className="text-white" />
        </div>
        <AnimatePresence>
          {!collapsed && (
            <motion.span
              initial={{ opacity: 0, width: 0 }}
              animate={{ opacity: 1, width: "auto" }}
              exit={{ opacity: 0, width: 0 }}
              className="font-bold text-lg whitespace-nowrap overflow-hidden"
            >
              DealScope
            </motion.span>
          )}
        </AnimatePresence>
      </div>

      {/* Nav Items */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto custom-scrollbar">
        {NAV_ITEMS.map(({ href, icon: Icon, label }) => (
          <Link
            key={href}
            href={href}
            className={`sidebar-item ${isActive(href) ? "active" : ""}`}
            title={collapsed ? label : undefined}
          >
            <Icon size={20} className="flex-shrink-0" />
            <AnimatePresence>
              {!collapsed && (
                <motion.span
                  initial={{ opacity: 0, width: 0 }}
                  animate={{ opacity: 1, width: "auto" }}
                  exit={{ opacity: 0, width: 0 }}
                  className="whitespace-nowrap overflow-hidden"
                >
                  {label}
                </motion.span>
              )}
            </AnimatePresence>
          </Link>
        ))}
      </nav>

      {/* Collapse toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center justify-center h-12 border-t border-white/5 text-white/40 hover:text-white/70 transition-colors"
      >
        {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
      </button>
    </aside>
  );
}
```

**Step 6: Create AppTopBar component**

Create `frontend/src/components/layout/AppTopBar.tsx`:

```tsx
"use client";

import { usePathname } from "next/navigation";
import { Bell, Search } from "lucide-react";

const PAGE_TITLES: Record<string, string> = {
  "/app": "Dashboard",
  "/app/market": "Market Analysis",
  "/app/simulator": "Deal Simulator",
  "/app/agent": "Research Agent",
  "/app/deals": "Deal Explorer",
};

export default function AppTopBar() {
  const pathname = usePathname();
  const title = PAGE_TITLES[pathname] || "DealScope";

  return (
    <header className="h-16 border-b border-white/5 flex items-center justify-between px-6 bg-[var(--bg-primary)]/80 backdrop-blur-sm sticky top-0 z-30">
      <h1 className="text-lg font-semibold">{title}</h1>
      <div className="flex items-center gap-4">
        <div className="relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-white/30" />
          <input
            type="text"
            placeholder="Search deals..."
            className="bg-white/5 border border-white/10 rounded-lg pl-9 pr-4 py-2 text-sm text-white placeholder:text-white/30 focus:outline-none focus:border-blue-500/50 w-64"
          />
        </div>
        <button className="w-9 h-9 rounded-lg bg-white/5 flex items-center justify-center text-white/40 hover:text-white/70 transition-colors">
          <Bell size={18} />
        </button>
      </div>
    </header>
  );
}
```

**Step 7: Create app shell layout**

Create `frontend/src/app/(app)/layout.tsx`:

```tsx
import Sidebar from "@/components/layout/Sidebar";
import AppTopBar from "@/components/layout/AppTopBar";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 ml-60 transition-all duration-300">
        <AppTopBar />
        <main className="p-6">{children}</main>
      </div>
    </div>
  );
}
```

Note: The `ml-60` (margin-left 240px) matches the sidebar width. The sidebar collapse state is client-side only; for a production app you'd lift this state or use CSS.

**Step 8: Create app dashboard placeholder**

Create `frontend/src/app/(app)/page.tsx`:

```tsx
export default function DashboardPage() {
  return (
    <div className="text-center py-20">
      <h2 className="text-2xl font-bold mb-4">Dashboard</h2>
      <p className="text-white/50">Coming in Task 5</p>
    </div>
  );
}
```

**Step 9: Update Navbar for marketing pages**

Update `frontend/src/components/layout/Navbar.tsx` — change branding to "DealScope", update links to point to `/app/*` routes, and change CTA:

```tsx
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { Zap } from "lucide-react";

const links = [
  { href: "/", label: "Home" },
  { href: "#features", label: "Features" },
  { href: "#how-it-works", label: "How It Works" },
];

export default function Navbar() {
  const pathname = usePathname();

  return (
    <motion.nav
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      className="fixed top-0 w-full z-50 glass border-b border-white/10"
    >
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center">
            <Zap size={18} className="text-white" />
          </div>
          <span className="font-bold text-lg">DealScope</span>
        </Link>

        <div className="hidden md:flex items-center gap-8">
          {links.map(({ href, label }) => (
            <a
              key={href}
              href={href}
              className="text-sm text-white/60 hover:text-white transition-colors"
            >
              {label}
            </a>
          ))}
        </div>

        <Link
          href="/app"
          className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-2 rounded-lg text-sm font-semibold transition-all glow-blue"
        >
          Launch App
        </Link>
      </div>
    </motion.nav>
  );
}
```

**Step 10: Verify build compiles**

Run: `cd frontend && npm run build`
Expected: Build succeeds (may have warnings, no errors)

**Step 11: Commit**

```bash
git add frontend/src/
git commit -m "feat: add DealScope app shell with sidebar, route groups, and rebranding"
```

---

## Task 4: Frontend — Landing Page Redesign

Replace the current landing page with a polished, magic-receipt.ai-inspired marketing page.

**Files:**
- Rewrite: `frontend/src/app/(marketing)/page.tsx`
- Keep: `frontend/src/components/ui/AnimatedCounter.tsx` (reuse)

**Step 1: Write the new landing page**

Rewrite `frontend/src/app/(marketing)/page.tsx` with:

- Hero with gradient mesh background, "Turn Data Into Deal-Ready Intelligence" headline
- Animated stats strip (741+ Deals, 15 Seasons, $2.4B Tracked, 292 Episodes)
- Three-feature showcase cards (Market Analysis, Deal Simulator, Research Agent)
- How-it-works 3-step flow
- Dashboard preview section (glassmorphic card showing a mockup)
- CTA footer with "Launch DealScope" button

The page should use Framer Motion `whileInView` animations, the existing `AnimatedCounter` component, Lucide icons (TrendingUp, SlidersHorizontal, Bot, ArrowRight, BarChart3, Sparkles), and the existing glass/glow CSS classes.

Full component: ~250 lines. Key sections:

```tsx
"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowRight, TrendingUp, SlidersHorizontal, Bot, BarChart3, Sparkles, CheckCircle } from "lucide-react";
import AnimatedCounter from "@/components/ui/AnimatedCounter";

// ... fadeUp variants, features array, steps array ...

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      {/* Hero */}
      {/* Stats Strip */}
      {/* Features */}
      {/* How It Works */}
      {/* Dashboard Preview */}
      {/* CTA Footer */}
    </div>
  );
}
```

The implementer should build each section following the design doc Section 1 specifications exactly. Use the existing `glass`, `glow-blue` CSS classes. All CTAs link to `/app`.

**Step 2: Verify build compiles**

Run: `cd frontend && npm run build`
Expected: Build succeeds

**Step 3: Commit**

```bash
git add frontend/src/app/\(marketing\)/page.tsx
git commit -m "feat: redesign landing page with DealScope branding and marketing sections"
```

---

## Task 5: Frontend — Dashboard Page

Build the main dashboard with KPI cards, charts, market pulse, and quick actions.

**Files:**
- Rewrite: `frontend/src/app/(app)/page.tsx`
- Create: `frontend/src/components/dashboard/KPICard.tsx`
- Create: `frontend/src/components/dashboard/DealFlowChart.tsx`
- Create: `frontend/src/components/dashboard/IndustryHeatmap.tsx`
- Create: `frontend/src/components/dashboard/MarketPulse.tsx`
- Create: `frontend/src/components/dashboard/QuickActions.tsx`
- Create: `frontend/src/components/dashboard/RecentDeals.tsx`
- Modify: `frontend/src/lib/api.ts` (add fetchIndustries, fetchDeals)

**Step 1: Extend API client**

Add to `frontend/src/lib/api.ts`:

```typescript
export interface Industry {
  industry: string;
  deal_count: number;
  success_rate: number;
  avg_ask: number;
  avg_revenue: number;
  pitch_count: number;
}

export interface Deal {
  episode: string;
  company_name: string;
  industry: string;
  season: string;
  revenue: number;
  objection_count: number;
  negotiation_rounds: number;
  founder_confidence: number;
  shark_enthusiasm: number;
  has_deal: boolean;
}

export interface DealsResponse {
  total: number;
  deals: Deal[];
}

export async function fetchIndustries(): Promise<Industry[]> {
  const res = await fetch("/api/data/industries");
  if (!res.ok) throw new Error("Failed to fetch industries");
  return res.json();
}

export async function fetchDeals(params?: {
  limit?: number;
  offset?: number;
  industry?: string;
  has_deal?: boolean;
  search?: string;
}): Promise<DealsResponse> {
  const searchParams = new URLSearchParams();
  if (params?.limit) searchParams.set("limit", String(params.limit));
  if (params?.offset) searchParams.set("offset", String(params.offset));
  if (params?.industry) searchParams.set("industry", params.industry);
  if (params?.has_deal !== undefined) searchParams.set("has_deal", String(params.has_deal));
  if (params?.search) searchParams.set("search", params.search);
  const res = await fetch(`/api/data/deals?${searchParams}`);
  if (!res.ok) throw new Error("Failed to fetch deals");
  return res.json();
}
```

**Step 2: Create KPICard component**

Create `frontend/src/components/dashboard/KPICard.tsx`:

```tsx
"use client";

import { motion } from "framer-motion";
import { LucideIcon } from "lucide-react";

interface Props {
  label: string;
  value: string;
  change?: string;
  changeType?: "up" | "down" | "neutral";
  icon: LucideIcon;
  color: string;
}

export default function KPICard({ label, value, change, changeType = "neutral", icon: Icon, color }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="kpi-card"
    >
      <div className="flex items-start justify-between mb-3">
        <span className="text-sm text-white/50">{label}</span>
        <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${color}`}>
          <Icon size={18} />
        </div>
      </div>
      <div className="text-2xl font-bold">{value}</div>
      {change && (
        <span className={`text-xs mt-1 ${
          changeType === "up" ? "text-emerald-400" : changeType === "down" ? "text-rose-400" : "text-white/40"
        }`}>
          {change}
        </span>
      )}
    </motion.div>
  );
}
```

**Step 3: Create remaining dashboard components**

Create each of these as separate files under `frontend/src/components/dashboard/`:

- `DealFlowChart.tsx` — Recharts AreaChart showing deals per season (from stats.seasons data)
- `IndustryHeatmap.tsx` — CSS grid of industry tiles, color-coded by success_rate (green→red), sized by deal_count
- `MarketPulse.tsx` — Glass card with AI-generated 3-sentence summary, computed from stats
- `QuickActions.tsx` — 4 Link buttons: "Simulate a Deal" → `/app/simulator`, "Research a Market" → `/app/agent`, "Browse Deals" → `/app/deals`, "View Trends" → `/app/market`
- `RecentDeals.tsx` — List of last 5 deals as compact cards showing company, industry, revenue, outcome badge

**Step 4: Build the dashboard page**

Rewrite `frontend/src/app/(app)/page.tsx`:

```tsx
"use client";

import { useEffect, useState } from "react";
import { Database, TrendingUp, Target, Award } from "lucide-react";
import { fetchStats, fetchIndustries, fetchDeals } from "@/lib/api";
import type { Industry, Deal } from "@/lib/api";
import KPICard from "@/components/dashboard/KPICard";
import DealFlowChart from "@/components/dashboard/DealFlowChart";
import IndustryHeatmap from "@/components/dashboard/IndustryHeatmap";
import MarketPulse from "@/components/dashboard/MarketPulse";
import QuickActions from "@/components/dashboard/QuickActions";
import RecentDeals from "@/components/dashboard/RecentDeals";

export default function DashboardPage() {
  const [stats, setStats] = useState<any>(null);
  const [industries, setIndustries] = useState<Industry[]>([]);
  const [recentDeals, setRecentDeals] = useState<Deal[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetchStats(),
      fetchIndustries(),
      fetchDeals({ limit: 5 }),
    ]).then(([s, ind, deals]) => {
      setStats(s);
      setIndustries(ind);
      setRecentDeals(deals.deals);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="animate-pulse text-white/30 py-20 text-center">Loading dashboard...</div>;

  const totalDeals = stats?.total_pitches || 0;
  const totalEpisodes = stats?.total_episodes || 0;
  const avgRevenue = stats?.avg_revenue_mentioned || 0;
  const topIndustry = industries.length > 0
    ? industries.reduce((a, b) => a.deal_count > b.deal_count ? a : b).industry
    : "N/A";
  const successCount = industries.reduce((sum, i) => sum + Math.round(i.deal_count * i.success_rate), 0);
  const successRate = totalDeals > 0 ? ((successCount / totalDeals) * 100).toFixed(1) : "0";

  return (
    <div className="space-y-6">
      {/* KPI Strip */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard label="Total Deals" value={totalDeals.toLocaleString()} icon={Database} color="bg-blue-500/20 text-blue-400" />
        <KPICard label="Avg Revenue" value={`$${(avgRevenue / 1000).toFixed(0)}K`} icon={TrendingUp} color="bg-emerald-500/20 text-emerald-400" />
        <KPICard label="Success Rate" value={`${successRate}%`} icon={Target} color="bg-amber-500/20 text-amber-400" />
        <KPICard label="Top Industry" value={topIndustry} icon={Award} color="bg-purple-500/20 text-purple-400" />
      </div>

      {/* Main grid */}
      <div className="grid lg:grid-cols-5 gap-6">
        {/* Left column 60% */}
        <div className="lg:col-span-3 space-y-6">
          <DealFlowChart seasons={stats?.seasons || []} />
          <IndustryHeatmap industries={industries} />
        </div>

        {/* Right column 40% */}
        <div className="lg:col-span-2 space-y-6">
          <MarketPulse stats={stats} industries={industries} />
          <QuickActions />
          <RecentDeals deals={recentDeals} />
        </div>
      </div>
    </div>
  );
}
```

**Step 5: Verify build compiles**

Run: `cd frontend && npm run build`
Expected: Build succeeds

**Step 6: Commit**

```bash
git add frontend/src/
git commit -m "feat: build DealScope dashboard with KPIs, charts, heatmap, and market pulse"
```

---

## Task 6: Frontend — Market Analysis Page

Build the industry deep-dive page with charts and AI brief.

**Files:**
- Create: `frontend/src/app/(app)/market/page.tsx`
- Create: `frontend/src/components/market/IndustrySelector.tsx`
- Create: `frontend/src/components/market/IndustryMetrics.tsx`
- Create: `frontend/src/components/market/IndustryCharts.tsx`
- Create: `frontend/src/components/market/IndustryBrief.tsx`

**Step 1: Create IndustrySelector**

Horizontal scrollable pill/chip bar listing all industries from the API. Props: `{ industries: Industry[], selected: string, onSelect: (industry: string) => void }`. First chip is "All Industries".

**Step 2: Create IndustryMetrics**

4-stat card grid: Deal Count, Avg Revenue, Success Rate, Pitch Count. Props: `{ industry: Industry }`.

**Step 3: Create IndustryCharts**

Two Recharts visualizations:
- Deal outcome donut chart (Recharts PieChart: deals with negotiation vs without)
- Revenue distribution bar chart (buckets: $0, $1-100K, $100K-500K, $500K-1M, $1M+)

Props: `{ deals: Deal[] }`

**Step 4: Create IndustryBrief**

Glass card showing AI-generated summary computed from data (not API call). Generates 3 sentences about the industry's performance based on success_rate, avg_revenue, and deal_count relative to overall averages. Props: `{ industry: Industry, allIndustries: Industry[] }`.

**Step 5: Build market page**

`frontend/src/app/(app)/market/page.tsx`:

```tsx
"use client";

import { useEffect, useState } from "react";
import { fetchIndustries, fetchDeals } from "@/lib/api";
import type { Industry, Deal } from "@/lib/api";
import IndustrySelector from "@/components/market/IndustrySelector";
import IndustryMetrics from "@/components/market/IndustryMetrics";
import IndustryCharts from "@/components/market/IndustryCharts";
import IndustryBrief from "@/components/market/IndustryBrief";

export default function MarketPage() {
  const [industries, setIndustries] = useState<Industry[]>([]);
  const [selected, setSelected] = useState("All Industries");
  const [deals, setDeals] = useState<Deal[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchIndustries().then(setIndustries).finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    const industry = selected === "All Industries" ? undefined : selected;
    fetchDeals({ limit: 1000, industry }).then((r) => setDeals(r.deals));
  }, [selected]);

  // ... render IndustrySelector, metrics, charts, brief
}
```

**Step 6: Verify build**

Run: `cd frontend && npm run build`

**Step 7: Commit**

```bash
git add frontend/src/app/\(app\)/market/ frontend/src/components/market/
git commit -m "feat: add Market Analysis page with industry selector, charts, and AI brief"
```

---

## Task 7: Frontend — Deal Simulator (Migrate)

Move existing simulator into the app shell route group and enhance.

**Files:**
- Create: `frontend/src/app/(app)/simulator/page.tsx`
- Reuse: All `frontend/src/components/simulator/*.tsx` components

**Step 1: Create app-route simulator page**

Create `frontend/src/app/(app)/simulator/page.tsx` — copy logic from the existing `frontend/src/app/simulator/page.tsx` but update navigation links (e.g., "Ask SharkBot" → "Ask Research Agent" linking to `/app/agent`, "See Comparable Deals" → linking to `/app/deals`).

**Step 2: Update StepVerdict links**

In `frontend/src/components/simulator/StepVerdict.tsx`, update the two action buttons:
- "Ask SharkBot for Advice" → "Ask Research Agent" with href `/app/agent`
- "See Comparable Deals" → "Explore Similar Deals" with href `/app/deals`

**Step 3: Verify build**

Run: `cd frontend && npm run build`

**Step 4: Commit**

```bash
git add frontend/src/app/\(app\)/simulator/ frontend/src/components/simulator/
git commit -m "feat: migrate Deal Simulator to app shell route"
```

---

## Task 8: Frontend — Research Agent Page

Build the research agent chat UI with tool-call visualization.

**Files:**
- Create: `frontend/src/app/(app)/agent/page.tsx`
- Create: `frontend/src/components/agent/AgentChat.tsx`
- Create: `frontend/src/components/agent/ToolCallCard.tsx`
- Create: `frontend/src/components/agent/ResearchSteps.tsx`
- Modify: `frontend/src/lib/api.ts` (add streamResearch)

**Step 1: Add streaming API function**

Add to `frontend/src/lib/api.ts`:

```typescript
export interface ToolCallEvent {
  type: "tool_call" | "tool_result" | "thinking" | "answer" | "error" | "done";
  tool?: string;
  input?: Record<string, unknown>;
  result?: unknown;
  content?: string;
  data?: string;
  status?: string;
}

export async function* streamResearch(query: string, depth: string = "standard"): AsyncGenerator<ToolCallEvent> {
  const res = await fetch(`/api/agent/research?query=${encodeURIComponent(query)}&depth=${encodeURIComponent(depth)}`);
  if (!res.ok) throw new Error("Research agent unavailable");
  const reader = res.body?.getReader();
  if (!reader) return;
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";
    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          yield JSON.parse(line.slice(6));
        } catch {}
      }
    }
  }
}
```

**Step 2: Create ToolCallCard component**

`frontend/src/components/agent/ToolCallCard.tsx`:

Shows a single tool call with: tool icon, tool name, input params (collapsible), result summary, status spinner → checkmark. Props: `{ tool: string, input: any, result?: any, status: "running" | "complete" }`.

**Step 3: Create ResearchSteps panel**

`frontend/src/components/agent/ResearchSteps.tsx`:

Right-panel component that displays a vertical list of ToolCallCards. Props: `{ steps: ToolCallEvent[] }`.

**Step 4: Create AgentChat component**

`frontend/src/components/agent/AgentChat.tsx`:

Left-panel chat component with:
- Starter prompt pills (4): "Food-tech market analysis", "Best equity structures", "Revenue benchmarks by industry", "Emerging categories"
- Message input with send button
- Chat messages (user + assistant) rendered with markdown
- Streams responses via `streamResearch()`
- Collects tool_call and tool_result events for the ResearchSteps panel

**Step 5: Build agent page**

`frontend/src/app/(app)/agent/page.tsx`:

```tsx
"use client";

import { useState } from "react";
import AgentChat from "@/components/agent/AgentChat";
import ResearchSteps from "@/components/agent/ResearchSteps";
import type { ToolCallEvent } from "@/lib/api";

export default function AgentPage() {
  const [steps, setSteps] = useState<ToolCallEvent[]>([]);

  return (
    <div className="grid lg:grid-cols-5 gap-6 h-[calc(100vh-7rem)]">
      <div className="lg:col-span-3">
        <AgentChat onStep={(step) => setSteps((prev) => [...prev, step])} onReset={() => setSteps([])} />
      </div>
      <div className="lg:col-span-2">
        <ResearchSteps steps={steps} />
      </div>
    </div>
  );
}
```

**Step 6: Verify build**

Run: `cd frontend && npm run build`

**Step 7: Commit**

```bash
git add frontend/src/app/\(app\)/agent/ frontend/src/components/agent/ frontend/src/lib/api.ts
git commit -m "feat: add Research Agent page with tool-call visualization and SSE streaming"
```

---

## Task 9: Frontend — Deal Explorer Page

Build the filterable, sortable data table for browsing all 741 deals.

**Files:**
- Create: `frontend/src/app/(app)/deals/page.tsx`
- Create: `frontend/src/components/deals/DealsTable.tsx`
- Create: `frontend/src/components/deals/DealsFilters.tsx`

**Step 1: Create DealsFilters**

`frontend/src/components/deals/DealsFilters.tsx`:

Horizontal filter bar with:
- Industry dropdown (select from API industries)
- Outcome toggle (All / Got Deal / No Deal)
- Search input (company name)
- Revenue range (min/max inputs)

Props: `{ filters, onChange, industries }`. Filters state: `{ industry, has_deal, search, min_revenue, max_revenue }`.

**Step 2: Create DealsTable**

`frontend/src/components/deals/DealsTable.tsx`:

Full-width table with sortable column headers. Columns: Company, Industry, Season, Revenue, Objections, Negotiations, Confidence, Outcome (badge). Click header to sort. Expandable row on click (show full details). Pagination controls at bottom (25 per page). Props: `{ deals: Deal[], total: number, page: number, onPageChange }`.

**Step 3: Build deals page**

`frontend/src/app/(app)/deals/page.tsx`:

```tsx
"use client";

import { useEffect, useState, useCallback } from "react";
import { fetchDeals, fetchIndustries } from "@/lib/api";
import type { Deal, Industry } from "@/lib/api";
import DealsFilters from "@/components/deals/DealsFilters";
import DealsTable from "@/components/deals/DealsTable";

const PAGE_SIZE = 25;

export default function DealsPage() {
  const [deals, setDeals] = useState<Deal[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [industries, setIndustries] = useState<Industry[]>([]);
  const [filters, setFilters] = useState({ industry: "", has_deal: undefined as boolean | undefined, search: "", min_revenue: undefined as number | undefined, max_revenue: undefined as number | undefined });
  const [loading, setLoading] = useState(true);

  useEffect(() => { fetchIndustries().then(setIndustries); }, []);

  const loadDeals = useCallback(() => {
    setLoading(true);
    fetchDeals({
      limit: PAGE_SIZE,
      offset: page * PAGE_SIZE,
      industry: filters.industry || undefined,
      has_deal: filters.has_deal,
      search: filters.search || undefined,
    }).then(({ deals, total }) => {
      setDeals(deals);
      setTotal(total);
      setLoading(false);
    });
  }, [page, filters]);

  useEffect(() => { loadDeals(); }, [loadDeals]);

  return (
    <div className="space-y-6">
      <DealsFilters filters={filters} onChange={(f) => { setFilters(f); setPage(0); }} industries={industries} />
      <DealsTable deals={deals} total={total} page={page} onPageChange={setPage} loading={loading} />
    </div>
  );
}
```

**Step 4: Verify build**

Run: `cd frontend && npm run build`

**Step 5: Commit**

```bash
git add frontend/src/app/\(app\)/deals/ frontend/src/components/deals/
git commit -m "feat: add Deal Explorer page with filterable, sortable data table"
```

---

## Task 10: Cleanup & Polish

Remove legacy routes, ensure all navigation works, final visual polish.

**Files:**
- Delete: `frontend/src/app/simulator/page.tsx` (old route)
- Delete: `frontend/src/app/hub/page.tsx` (old route)
- Delete: `frontend/src/app/chat/page.tsx` (old route)
- Verify: All internal links point to `/app/*` routes
- Verify: Both servers start and all pages render

**Step 1: Remove old route pages**

```bash
rm frontend/src/app/simulator/page.tsx
rm frontend/src/app/hub/page.tsx
rm frontend/src/app/chat/page.tsx
rmdir frontend/src/app/simulator frontend/src/app/hub frontend/src/app/chat 2>/dev/null || true
```

Note: Keep the component files under `components/simulator/`, `components/hub/`, `components/chat/` — the simulator components are reused, and the others may be useful later.

**Step 2: Verify full build**

Run: `cd frontend && npm run build`
Expected: Build succeeds with no errors

**Step 3: Start both servers and verify all pages**

Start API: `python3 -m uvicorn src.api.main:app --port 8001 --reload`
Start frontend: `cd frontend && npm run dev -- -p 3001`

Visit and verify:
- `http://localhost:3001/` → Landing page with DealScope branding
- `http://localhost:3001/app` → Dashboard with KPIs and charts
- `http://localhost:3001/app/market` → Market Analysis with industry selector
- `http://localhost:3001/app/simulator` → Deal Simulator wizard
- `http://localhost:3001/app/agent` → Research Agent chat
- `http://localhost:3001/app/deals` → Deal Explorer table

**Step 4: Run all backend tests**

Run: `pytest tests/ -v`
Expected: ALL PASS

**Step 5: Commit**

```bash
git add -A
git commit -m "chore: remove legacy routes and finalize DealScope v1"
```

---

## Task Summary

| Task | Description | Est. Time |
|------|-------------|-----------|
| 1 | Backend — Industries & Deals endpoints | 10 min |
| 2 | Backend — Research Agent endpoint | 15 min |
| 3 | Frontend — Rebrand & Route Structure | 15 min |
| 4 | Frontend — Landing Page Redesign | 15 min |
| 5 | Frontend — Dashboard Page | 20 min |
| 6 | Frontend — Market Analysis Page | 15 min |
| 7 | Frontend — Deal Simulator (Migrate) | 5 min |
| 8 | Frontend — Research Agent Page | 20 min |
| 9 | Frontend — Deal Explorer Page | 15 min |
| 10 | Cleanup & Polish | 10 min |

**Total estimated: ~2.5 hours**

### Dependencies
- Tasks 1-2 (backend) are independent of each other → can run in parallel
- Task 3 (route structure) must complete before Tasks 4-9
- Tasks 4-9 are independent of each other → can run in parallel after Task 3
- Task 10 runs last after all others complete
