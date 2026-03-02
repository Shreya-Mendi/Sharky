"""Multi-step research agent with Claude tool-calling and SSE streaming."""

from __future__ import annotations

import json
import os
from typing import Generator

from src.data.cache import get_all_pitches, get_industries, get_deals, classify_industry


# -- Tool implementations (no API keys needed) --

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
    sentiment_score = 0.5 * 0.3
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


# -- Claude tool definitions --

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
        "description": "Get aggregate market statistics for a specific industry or all industries.",
        "input_schema": {
            "type": "object",
            "properties": {
                "industry": {"type": "string", "description": "Industry name to filter. Omit for all."},
            },
        },
    },
    {
        "name": "predict_deal",
        "description": "Run the deal prediction model with specific pitch parameters.",
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
        "description": "Analyze cross-cutting patterns in deal data for a specific industry.",
        "input_schema": {
            "type": "object",
            "properties": {
                "industry": {"type": "string", "description": "Industry to analyze"},
                "metric": {"type": "string", "description": "Focus metric", "default": "success_rate"},
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

Always cite specific data points and companies. Be quantitative. Focus on actionable business intelligence."""


def run_research_stream(query: str, depth: str = "standard") -> Generator[dict, None, None]:
    """Execute the research agent with streaming tool calls."""
    try:
        import anthropic
    except ImportError:
        yield from _fallback_research(query)
        return

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
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

    yield {"type": "tool_call", "tool": "search_deals", "input": {"query": query_lower}, "status": "running"}
    deals = search_deals_tool(query_lower, limit=10)
    yield {"type": "tool_result", "tool": "search_deals", "result": deals, "status": "complete"}

    yield {"type": "tool_call", "tool": "get_market_stats", "input": {}, "status": "running"}
    stats = get_market_stats_tool()
    yield {"type": "tool_result", "tool": "get_market_stats", "result": stats, "status": "complete"}

    deal_count = len(deals)
    industries = stats.get("industries", [])
    total = sum(i["deal_count"] for i in industries) if industries else 0

    answer_parts = [
        f"## Research Results for: \"{query}\"\n\n",
        f"Found **{deal_count}** matching deals across our database of {total} total pitches.\n\n",
    ]
    if deals:
        answer_parts.append("### Top Matching Companies\n\n")
        for d in deals[:5]:
            answer_parts.append(f"- **{d['company_name']}** ({d['episode']}) — {d['industry']}, Revenue: ${d['revenue']:,.0f}\n")

    if industries:
        answer_parts.append("\n### Industry Breakdown\n\n")
        for ind in sorted(industries, key=lambda x: x["deal_count"], reverse=True)[:5]:
            answer_parts.append(f"- **{ind['industry']}**: {ind['deal_count']} deals, {ind['success_rate']:.0%} success rate\n")

    yield {"type": "answer", "content": "".join(answer_parts)}
    yield {"type": "done"}
