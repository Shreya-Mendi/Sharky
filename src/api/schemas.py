"""API request/response schemas."""

from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    ask_amount: float = Field(..., gt=0)
    equity_offered_pct: float = Field(..., gt=0, le=100)
    revenue_trailing_12m: float = Field(default=0, ge=0)
    industry: str = Field(default="Unknown")
    founder_count: int = Field(default=1, ge=1)
    pitch_sentiment_score: float = Field(default=0.0, ge=-1, le=1)
    shark_enthusiasm_max: float = Field(default=0.0, ge=-1, le=1)
    objection_count: int = Field(default=0, ge=0)
    negotiation_rounds: int = Field(default=0, ge=0)


class PredictResponse(BaseModel):
    deal_probability: float
    deal_score: int
    strengths: list[str] = []
    risks: list[str] = []


class AnalyzeRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class AnalyzeResponse(BaseModel):
    answer: str
    sources: list[dict] = []


class CompsRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class CompsResponse(BaseModel):
    matches: list[dict] = []


class EpisodeSummary(BaseModel):
    episode: str
    pitch_count: int
    deal_count: int


class EpisodeDetail(BaseModel):
    episode: str
    pitch_count: int
    deal_count: int
    pitches: list[dict]


class StatsResponse(BaseModel):
    total_pitches: int
    total_episodes: int
    total_seasons: int
    avg_revenue_mentioned: float
    avg_objection_count: float
    avg_founder_confidence: float
    seasons: list[dict]
