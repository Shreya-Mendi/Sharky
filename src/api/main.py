"""FastAPI application for the Shark Tank AI Engine."""

from __future__ import annotations

import numpy as np
from fastapi import FastAPI, HTTPException

from src.api.schemas import (
    PredictRequest,
    PredictResponse,
    AnalyzeRequest,
    AnalyzeResponse,
    CompsRequest,
    CompsResponse,
)
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
