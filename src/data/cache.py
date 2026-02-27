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
