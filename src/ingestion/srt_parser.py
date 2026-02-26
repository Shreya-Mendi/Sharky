"""srt_parser.py — Parse Shark Tank SRT files into per-pitch analysis.

Handles two speaker label formats:
- Bracket: [Speaker_N] text (Seasons 1, 2, 5+)
- Colon: Speaker_N: text (Seasons 3, 4)

Pipeline: parse SRT -> split into pitches -> classify roles -> segment -> extract signals.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PITCH_BOUNDARY_PATTERN = re.compile(
    r"(?:first into the (?:tank|shark tank)|"
    r"next up (?:is|are)|"
    r"next into the (?:tank|shark tank) (?:is|are)|"
    r"our next entrepreneur)",
    re.IGNORECASE,
)

OBJECTION_PATTERNS = [
    r"i'?m out",
    r"for that reason,?\s*i'?m out",
    r"too risky",
    r"don'?t (?:see|think|believe)",
    r"concerned about",
    r"problem (?:is|with)",
    r"can'?t (?:justify|support|get behind)",
    r"overvalued",
    r"not for me",
    r"no deal",
    r"pass on this",
]

NEGOTIATION_PATTERNS = [
    r"i(?:'ll|.will) (?:offer|give you|do)",
    r"counter.?offer",
    r"how about",
    r"would you (?:take|accept|consider)",
    r"(?:deal|offer) (?:is|at)",
    r"\d+%?\s*(?:for|equity)",
]

DEMO_KEYWORDS = re.compile(
    r"\b(demo|watch this|let me show|check this out|look at this|"
    r"here'?s how|taste|try this|sample)\b",
    re.IGNORECASE,
)

DOLLAR_PATTERN = re.compile(
    r"\$\s?([\d,]+(?:\.\d+)?)\s*"
    r"(?:(thousand|million|billion|k|m|b))?\b",
    re.IGNORECASE,
)

MARKET_SIZE_PATTERN = re.compile(
    r"(?:market\s+(?:size|opportunity|worth|valued)|"
    r"(?:tam|total\s+addressable\s+market)|"
    r"(?:industry\s+(?:is|worth|valued))|"
    r"(?:billion|million)\s+dollar\s+(?:market|industry|space))",
    re.IGNORECASE,
)

ENTREPRENEUR_INTRO_PATTERN = re.compile(
    r"(?:my name is|i'?m .{1,30} from|hello,? (?:my name|i'?m)|"
    r"i'?m asking for \$|i'?m (?:the )?(?:founder|ceo|owner|president))",
    re.IGNORECASE,
)

# Speaker label extraction patterns
_BRACKET_SPEAKER = re.compile(r"^\[([Ss]peaker_\d+)\]\s*(.*)$")
_COLON_SPEAKER = re.compile(r"^([Ss]peaker_\d+):\s*(.*)$")

# SRT timestamp pattern
_TIMESTAMP_RE = re.compile(
    r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})"
    r"\s*-->\s*"
    r"(\d{2}):(\d{2}):(\d{2})[,.](\d{3})"
)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class SubtitleBlock:
    """A single parsed SRT subtitle block with speaker label."""
    index: int
    start_seconds: float
    end_seconds: float
    speaker: str
    text: str


@dataclass
class PitchSegments:
    """Segmented dialogue from a single Shark Tank pitch."""
    founder_pitch: list[SubtitleBlock] = field(default_factory=list)
    product_demo: list[SubtitleBlock] = field(default_factory=list)
    shark_questions: list[SubtitleBlock] = field(default_factory=list)
    objections: list[SubtitleBlock] = field(default_factory=list)
    negotiation: list[SubtitleBlock] = field(default_factory=list)
    closing_reason: list[SubtitleBlock] = field(default_factory=list)

    def to_dict(self) -> dict[str, list[str]]:
        return {
            name: [b.text for b in getattr(self, name)]
            for name in (
                "founder_pitch", "product_demo", "shark_questions",
                "objections", "negotiation", "closing_reason",
            )
        }


@dataclass
class ExtractedSignals:
    """NLP signals extracted from a single pitch."""
    revenue_mentioned: float = 0.0
    market_size_claim: float = 0.0
    founder_confidence: float = 0.0
    shark_enthusiasm_max: float = 0.0
    objection_count: int = 0
    negotiation_rounds: int = 0

    def to_dict(self) -> dict:
        return {
            "revenue_mentioned": self.revenue_mentioned,
            "market_size_claim": self.market_size_claim,
            "founder_confidence": self.founder_confidence,
            "shark_enthusiasm_max": self.shark_enthusiasm_max,
            "objection_count": self.objection_count,
            "negotiation_rounds": self.negotiation_rounds,
        }


@dataclass
class ParsedPitch:
    """Complete parse result for one pitch within an episode."""
    episode: str
    pitch_index: int
    entrepreneur_name: str
    segments: PitchSegments
    signals: ExtractedSignals
    speaker_map: dict[str, str]
    confidence_scores: dict[str, float]
    raw_blocks: list[SubtitleBlock]

    def to_dict(self) -> dict:
        return {
            "episode": self.episode,
            "pitch_index": self.pitch_index,
            "entrepreneur_name": self.entrepreneur_name,
            "segments": self.segments.to_dict(),
            "signals": self.signals.to_dict(),
            "speaker_map": self.speaker_map,
        }


# ---------------------------------------------------------------------------
# SRT Parsing
# ---------------------------------------------------------------------------

def _timestamp_to_seconds(hours: str, minutes: str, seconds: str, ms: str) -> float:
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(ms) / 1000


def _extract_speaker_and_text(raw_text: str) -> tuple[str, str]:
    """Extract speaker label and clean text from a subtitle line.

    Handles both formats:
    - [Speaker_N] text
    - Speaker_N: text
    - No speaker label (returns empty speaker)
    """
    m = _BRACKET_SPEAKER.match(raw_text)
    if m:
        return m.group(1), m.group(2).strip()
    m = _COLON_SPEAKER.match(raw_text)
    if m:
        return m.group(1), m.group(2).strip()
    return "", raw_text.strip()


def parse_srt(text: str) -> list[SubtitleBlock]:
    """Parse raw SRT text into SubtitleBlock objects with speaker labels."""
    blocks: list[SubtitleBlock] = []
    raw_blocks = re.split(r"\n\s*\n", text.strip())

    for raw in raw_blocks:
        lines = raw.strip().splitlines()
        if len(lines) < 2:
            continue

        try:
            index = int(lines[0].strip())
        except ValueError:
            continue

        ts_match = _TIMESTAMP_RE.match(lines[1].strip())
        if not ts_match:
            continue

        g = ts_match.groups()
        start = _timestamp_to_seconds(g[0], g[1], g[2], g[3])
        end = _timestamp_to_seconds(g[4], g[5], g[6], g[7])

        subtitle_text = " ".join(lines[2:])
        subtitle_text = re.sub(r"<[^>]+>", "", subtitle_text).strip()

        if not subtitle_text:
            continue

        speaker, clean_text = _extract_speaker_and_text(subtitle_text)

        blocks.append(SubtitleBlock(
            index=index,
            start_seconds=start,
            end_seconds=end,
            speaker=speaker,
            text=clean_text,
        ))

    return blocks


def parse_srt_file(path: str | Path) -> list[SubtitleBlock]:
    """Read and parse an SRT file from disk."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"SRT file not found: {path}")
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            text = path.read_text(encoding=encoding)
            return parse_srt(text)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Could not decode SRT file: {path}")
