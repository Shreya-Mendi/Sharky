"""Hybrid NLP stack: transformer classifiers + embedding retrieval with fallbacks."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Sequence

import numpy as np


@dataclass
class ModelStackStatus:
    sentiment_model: str
    embedding_model: str
    reranker_model: str
    enabled: bool


def _enabled() -> bool:
    return os.environ.get("ENABLE_TRANSFORMER_MODELS", "true").lower() in {"1", "true", "yes"}


@lru_cache(maxsize=1)
def _load_sentiment_pipeline():
    if not _enabled():
        return None
    try:
        from transformers import pipeline

        return pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
    except Exception:
        return None


@lru_cache(maxsize=1)
def _load_embedding_model():
    if not _enabled():
        return None
    try:
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    except Exception:
        return None


@lru_cache(maxsize=1)
def _load_reranker_model():
    if not _enabled():
        return None
    try:
        from sentence_transformers import CrossEncoder

        return CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    except Exception:
        return None


def model_stack_status() -> dict:
    sentiment = _load_sentiment_pipeline()
    embedder = _load_embedding_model()
    reranker = _load_reranker_model()
    status = ModelStackStatus(
        sentiment_model="distilbert-base-uncased-finetuned-sst-2-english" if sentiment else "heuristic-fallback",
        embedding_model="sentence-transformers/all-MiniLM-L6-v2" if embedder else "lexical-fallback",
        reranker_model="cross-encoder/ms-marco-MiniLM-L-6-v2" if reranker else "token-fallback",
        enabled=_enabled(),
    )
    return status.__dict__


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def transcript_behavioral_features(text: str) -> dict:
    """Return transformer-style transcript features with deterministic fallback."""
    clean = (text or "").strip()
    if not clean:
        return {
            "sentiment_score": 0.0,
            "objection_score": 0.0,
            "negotiation_strength": 0.0,
            "traction_quality": 0.0,
            "source": "empty",
        }

    objection_markers = ("concern", "risk", "too high", "not convinced", "i'm out", "problem")
    negotiation_markers = ("offer", "counter", "equity", "terms", "deal", "valuation")
    traction_markers = ("revenue", "growth", "customers", "retention", "margin", "profit")
    lowered = clean.lower()

    sentiment_pipeline = _load_sentiment_pipeline()
    if sentiment_pipeline:
        try:
            sent = sentiment_pipeline(clean[:3000])[0]
            polarity = sent["score"] if sent["label"].upper().startswith("POS") else -sent["score"]
            sentiment_score = float(np.clip(polarity, -1.0, 1.0))
            objection = _clamp01(sum(lowered.count(m) for m in objection_markers) / 8.0)
            negotiation = _clamp01(sum(lowered.count(m) for m in negotiation_markers) / 7.0)
            traction = _clamp01(sum(lowered.count(m) for m in traction_markers) / 8.0)
            return {
                "sentiment_score": round(sentiment_score, 4),
                "objection_score": round(objection, 4),
                "negotiation_strength": round(negotiation, 4),
                "traction_quality": round(traction, 4),
                "source": "transformer",
            }
        except Exception:
            pass

    # Heuristic fallback preserves API behavior if transformer stack is unavailable.
    pos = sum(lowered.count(t) for t in ("growth", "strong", "great", "profit", "traction", "demand"))
    neg = sum(lowered.count(t) for t in ("risk", "weak", "decline", "loss", "concern", "out"))
    sentiment_score = 0.0 if (pos + neg) == 0 else (pos - neg) / max(pos + neg, 1)
    objection = _clamp01(sum(lowered.count(m) for m in objection_markers) / 8.0)
    negotiation = _clamp01(sum(lowered.count(m) for m in negotiation_markers) / 7.0)
    traction = _clamp01(sum(lowered.count(m) for m in traction_markers) / 8.0)
    return {
        "sentiment_score": round(float(np.clip(sentiment_score, -1.0, 1.0)), 4),
        "objection_score": round(objection, 4),
        "negotiation_strength": round(negotiation, 4),
        "traction_quality": round(traction, 4),
        "source": "heuristic",
    }


def semantic_retrieve(
    query: str,
    docs: Sequence[dict],
    text_key: str = "text",
    top_k: int = 10,
) -> list[tuple[int, float]]:
    """Return (doc_index, score) using embedding retrieval + reranking if available."""
    if not docs:
        return []

    embedder = _load_embedding_model()
    reranker = _load_reranker_model()
    clean_query = (query or "").strip()
    if not clean_query:
        return []

    if not embedder:
        # Lexical fallback by token overlap.
        q_tokens = {t for t in clean_query.lower().split() if t}
        scored = []
        for i, doc in enumerate(docs):
            text = str(doc.get(text_key, "")).lower()
            d_tokens = {t for t in text.split() if t}
            overlap = len(q_tokens & d_tokens)
            if overlap > 0:
                scored.append((i, float(overlap)))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    corpus_text = [str(d.get(text_key, ""))[:5000] for d in docs]
    query_vec = embedder.encode([clean_query], normalize_embeddings=True)
    corpus_vec = embedder.encode(corpus_text, normalize_embeddings=True)
    base_scores = np.dot(corpus_vec, query_vec.T).reshape(-1)
    pre_rank = sorted(enumerate(base_scores.tolist()), key=lambda x: x[1], reverse=True)[: max(top_k * 4, 24)]

    if reranker:
        try:
            pairs = [(clean_query, corpus_text[idx]) for idx, _ in pre_rank]
            rerank_scores = reranker.predict(pairs)
            reranked = [(pre_rank[i][0], float(rerank_scores[i])) for i in range(len(pre_rank))]
            reranked.sort(key=lambda x: x[1], reverse=True)
            return reranked[:top_k]
        except Exception:
            pass

    return pre_rank[:top_k]

