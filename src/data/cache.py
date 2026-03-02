"""cache.py — Parse all SRT transcripts and cache as JSON.

Parses once, serves from memory. Rebuild cache with rebuild_cache().
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from src.ingestion.srt_parser import parse_all_episodes

logger = logging.getLogger(__name__)

TRANSCRIPT_DIR = Path("transcripts")
CACHE_FILE = Path("data/processed/all_pitches.json")

_cached_pitches: list[dict] | None = None
_cached_stats: dict | None = None


def rebuild_cache(transcript_dir: Path | None = None) -> list[dict]:
    """Parse all SRT files and write JSON cache."""
    srt_dir = transcript_dir or TRANSCRIPT_DIR
    logger.info("Parsing all SRT files from %s...", srt_dir)
    pitches = parse_all_episodes(srt_dir)
    logger.info("Parsed %d pitches from SRT files", len(pitches))
    pitch_dicts = [p.to_dict() for p in pitches]
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(pitch_dicts, f, indent=2)
    logger.info("Cache written to %s", CACHE_FILE)
    return pitch_dicts


def get_all_pitches() -> list[dict]:
    """Get all cached pitches. Parses if cache doesn't exist."""
    global _cached_pitches
    if _cached_pitches is not None:
        return _cached_pitches
    if CACHE_FILE.exists():
        logger.info("Loading pitches from cache file %s", CACHE_FILE)
        with open(CACHE_FILE) as f:
            _cached_pitches = json.load(f)
    else:
        logger.info("No cache file found, parsing transcripts...")
        _cached_pitches = rebuild_cache()
    return _cached_pitches


def get_episodes() -> list[dict]:
    """Get pitches grouped by episode."""
    pitches = get_all_pitches()
    episodes: dict[str, dict] = {}
    for pitch in pitches:
        ep = pitch["episode"]
        if ep not in episodes:
            episodes[ep] = {"episode": ep, "pitch_count": 0, "deal_count": 0, "pitches": []}
        episodes[ep]["pitches"].append(pitch)
        episodes[ep]["pitch_count"] += 1
    return sorted(episodes.values(), key=lambda e: e["episode"])


def get_episode(code: str) -> dict | None:
    """Get a single episode by code (e.g., 'S01E01')."""
    for ep in get_episodes():
        if ep["episode"] == code:
            return ep
    return None


def get_stats() -> dict:
    """Compute aggregate statistics for dashboard."""
    global _cached_stats
    if _cached_stats is not None:
        return _cached_stats
    pitches = get_all_pitches()
    episodes = get_episodes()
    revenues = [p["signals"]["revenue_mentioned"] for p in pitches if p["signals"]["revenue_mentioned"] > 0]
    avg_revenue = sum(revenues) / len(revenues) if revenues else 0
    objections = [p["signals"]["objection_count"] for p in pitches]
    avg_objections = sum(objections) / len(objections) if objections else 0
    sentiments = [p["signals"]["founder_confidence"] for p in pitches]
    avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
    season_data: dict[str, dict] = {}
    for pitch in pitches:
        season = pitch["episode"][:3]
        if season not in season_data:
            season_data[season] = {"season": season, "pitch_count": 0, "episodes": set()}
        season_data[season]["pitch_count"] += 1
        season_data[season]["episodes"].add(pitch["episode"])
    seasons = []
    for s in sorted(season_data.values(), key=lambda x: x["season"]):
        seasons.append({"season": s["season"], "pitch_count": s["pitch_count"], "episode_count": len(s["episodes"])})
    _cached_stats = {
        "total_pitches": len(pitches),
        "total_episodes": len(episodes),
        "total_seasons": len(seasons),
        "avg_revenue_mentioned": round(avg_revenue, 2),
        "avg_objection_count": round(avg_objections, 2),
        "avg_founder_confidence": round(avg_sentiment, 4),
        "seasons": seasons,
    }
    return _cached_stats


# Industry keyword mapping for classifying pitches from SRT data
INDUSTRY_KEYWORDS = {
    "Food & Beverage": ["food", "restaurant", "cook", "kitchen", "recipe", "drink", "beverage", "snack", "sauce", "spice", "meal", "eat", "chef", "bakery", "candy", "chocolate"],
    "Technology": ["app", "software", "tech", "digital", "online", "platform", "website", "internet", "computer", "ai", "data", "cloud", "saas"],
    "Health & Wellness": ["health", "medical", "wellness", "vitamin", "supplement", "therapy", "doctor", "patient", "organic", "natural", "cbd", "hemp"],
    "Fashion & Beauty": ["fashion", "clothing", "beauty", "cosmetic", "makeup", "skin", "hair", "jewelry", "accessories", "dress", "wear", "style"],
    "Home & Garden": ["home", "house", "garden", "furniture", "decor", "clean", "storage", "organize"],
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

    best = max(scores, key=scores.get)
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
        has_negotiation = [p for p in ind_pitches if p["signals"]["negotiation_rounds"] > 0]
        result.append({
            "industry": industry,
            "deal_count": len(ind_pitches),
            "success_rate": round(len(has_negotiation) / len(ind_pitches), 4) if ind_pitches else 0,
            "avg_ask": round(sum(revenues) / len(revenues), 2) if revenues else 0,
            "avg_revenue": round(sum(revenues) / len(revenues), 2) if revenues else 0,
            "avg_equity": 0,
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
