"""FastAPI application for the Shark Tank AI Engine."""

from __future__ import annotations

import json as json_module

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from src.api.schemas import (
    PredictRequest,
    PredictResponse,
    AnalyzeRequest,
    AnalyzeResponse,
    CompsRequest,
    CompsResponse,
)
from src.data.cache import get_all_pitches, get_episodes, get_episode, get_stats, get_industries, get_deals
from src.models.deal_predictor import (
    NUMERIC_FEATURES,
    DealPrediction,
)
from xgboost import XGBClassifier

app = FastAPI(
    title="Shark Tank AI Engine",
    description="Analyze Shark Tank pitches, predict deal outcomes, find comparable deals.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model (loaded at startup or first request)
_model: XGBClassifier | None = None


@app.get("/health")
def health():
    return {"status": "healthy", "model_loaded": _model is not None}


@app.post("/predict", response_model=PredictResponse)
def predict_deal(request: PredictRequest):
    """Predict deal probability for a hypothetical pitch."""
    implied_valuation = (
        request.ask_amount / (request.equity_offered_pct / 100)
        if request.equity_offered_pct > 0
        else 0
    )

    features = np.array([[
        request.ask_amount,
        request.equity_offered_pct,
        implied_valuation,
        request.revenue_trailing_12m,
        float(request.founder_count),
        request.pitch_sentiment_score,
        request.shark_enthusiasm_max,
        float(request.objection_count),
        float(request.negotiation_rounds),
    ]])

    if _model is not None:
        prob = float(_model.predict_proba(features)[0, 1])
    else:
        # Fallback heuristic when model isn't loaded
        revenue_score = min(request.revenue_trailing_12m / 1_000_000, 1.0) * 0.4
        valuation_score = max(0, 1 - implied_valuation / 10_000_000) * 0.3
        sentiment_score = (request.pitch_sentiment_score + 1) / 2 * 0.3
        prob = revenue_score + valuation_score + sentiment_score
        prob = max(0.05, min(0.95, prob))

    score = max(1, min(10, round(prob * 10)))

    strengths = []
    risks = []
    if request.revenue_trailing_12m > 500_000:
        strengths.append("Strong revenue traction")
    if request.equity_offered_pct < 15:
        risks.append("Low equity offer may deter sharks")
    if implied_valuation > 5_000_000 and request.revenue_trailing_12m < 500_000:
        risks.append("High valuation relative to revenue")
    if request.pitch_sentiment_score > 0.5:
        strengths.append("Strong founder confidence")

    return PredictResponse(
        deal_probability=round(prob, 4),
        deal_score=score,
        strengths=strengths,
        risks=risks,
    )


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze_query(request: AnalyzeRequest):
    """RAG-powered analysis of Shark Tank data."""
    try:
        from src.rag.retrieval_chain import analyze
        result = analyze(request.query, top_k=request.top_k)
        sources = [
            {
                "episode": s.episode,
                "company_name": s.company_name,
                "segment_type": s.segment_type,
                "snippet": s.text_snippet,
            }
            for s in result.sources
        ]
        return AnalyzeResponse(answer=result.answer, sources=sources)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Analysis unavailable: {e}")


@app.post("/comps", response_model=CompsResponse)
def find_comps(request: CompsRequest):
    """Find comparable past pitches."""
    try:
        from src.rag.retrieval_chain import retrieve_context
        context = retrieve_context(request.query, top_k=request.top_k)
        return CompsResponse(matches=context)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Comps search unavailable: {e}")


@app.get("/data/episodes")
def list_episodes():
    """List all parsed episodes with pitch counts."""
    return get_episodes()


@app.get("/data/episodes/{code}")
def get_episode_detail(code: str):
    """Get a single episode with all pitch data."""
    episode = get_episode(code)
    if not episode:
        raise HTTPException(status_code=404, detail=f"Episode {code} not found")
    return episode


@app.get("/data/stats")
def stats():
    """Aggregate statistics for the dashboard."""
    return get_stats()


@app.get("/data/pitches")
def list_pitches(limit: int = 50, offset: int = 0):
    """List all pitches with pagination."""
    pitches = get_all_pitches()
    return {"total": len(pitches), "pitches": pitches[offset:offset + limit]}


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


@app.get("/analyze/stream")
async def analyze_stream_endpoint(query: str, top_k: int = 5):
    """SSE streaming analysis endpoint for SharkBot."""
    def event_generator():
        try:
            from src.rag.retrieval_chain import analyze_stream
            for chunk in analyze_stream(query, top_k=top_k):
                event_data = json_module.dumps(chunk)
                yield f"data: {event_data}\n\n"
            yield "data: {\"type\": \"done\"}\n\n"
        except Exception as e:
            error_data = json_module.dumps({"type": "error", "data": str(e)})
            yield f"data: {error_data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


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
