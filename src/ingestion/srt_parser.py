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

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


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


# ---------------------------------------------------------------------------
# Pitch Splitting
# ---------------------------------------------------------------------------

def split_into_pitches(blocks: list[SubtitleBlock]) -> list[list[SubtitleBlock]]:
    """Split an episode's subtitle blocks into individual pitch segments."""
    if not blocks:
        return []

    boundaries: list[int] = []
    for i, block in enumerate(blocks):
        if PITCH_BOUNDARY_PATTERN.search(block.text):
            boundaries.append(i)

    if not boundaries:
        return [blocks]

    pitches: list[list[SubtitleBlock]] = []
    for i, start_idx in enumerate(boundaries):
        end_idx = boundaries[i + 1] if i + 1 < len(boundaries) else len(blocks)
        pitch_blocks = blocks[start_idx:end_idx]
        if pitch_blocks:
            pitches.append(pitch_blocks)

    return pitches


# ---------------------------------------------------------------------------
# Role Classification
# ---------------------------------------------------------------------------

def classify_speakers(
    pitch_blocks: list[SubtitleBlock],
    all_blocks: list[SubtitleBlock],
) -> tuple[dict[str, str], dict[str, float]]:
    """Classify Speaker_N labels as narrator, entrepreneur, or shark."""
    roles: dict[str, str] = {}
    confidences: dict[str, float] = {}
    pitch_speakers = set(b.speaker for b in pitch_blocks if b.speaker)

    # Narrator: speaker who delivers boundary/transition lines
    narrator_scores: dict[str, int] = {}
    for block in all_blocks:
        if not block.speaker:
            continue
        if PITCH_BOUNDARY_PATTERN.search(block.text):
            narrator_scores[block.speaker] = narrator_scores.get(block.speaker, 0) + 3
        if re.search(r"sharks? (?:are|is) out|chances? to|will (?:one|they)", block.text, re.IGNORECASE):
            narrator_scores[block.speaker] = narrator_scores.get(block.speaker, 0) + 1

    narrator_speaker = ""
    if narrator_scores:
        narrator_speaker = max(narrator_scores, key=narrator_scores.get)
        total_boundary = sum(narrator_scores.values())
        narrator_conf = min(narrator_scores[narrator_speaker] / max(total_boundary, 1), 1.0)
    else:
        narrator_conf = 0.0

    if narrator_speaker and narrator_speaker in pitch_speakers:
        roles[narrator_speaker] = "narrator"
        confidences[narrator_speaker] = narrator_conf

    # Entrepreneur: says "my name is", "I'm asking for", dominates early lines
    entrepreneur_scores: dict[str, float] = {}
    for block in pitch_blocks:
        if not block.speaker or block.speaker == narrator_speaker:
            continue
        score = entrepreneur_scores.get(block.speaker, 0.0)
        if ENTREPRENEUR_INTRO_PATTERN.search(block.text):
            score += 3.0
        pitch_start = pitch_blocks[0].start_seconds
        pitch_end = pitch_blocks[-1].end_seconds
        pitch_duration = pitch_end - pitch_start
        if pitch_duration > 0:
            relative_pos = (block.start_seconds - pitch_start) / pitch_duration
            if relative_pos < 0.4:
                score += 0.5
        entrepreneur_scores[block.speaker] = score

    entrepreneur_speaker = ""
    if entrepreneur_scores:
        entrepreneur_speaker = max(entrepreneur_scores, key=entrepreneur_scores.get)
        if entrepreneur_scores[entrepreneur_speaker] >= 1.0:
            roles[entrepreneur_speaker] = "entrepreneur"
            max_score = max(entrepreneur_scores.values())
            confidences[entrepreneur_speaker] = min(max_score / 5.0, 1.0)

    # Sharks: everyone else
    for speaker in pitch_speakers:
        if speaker not in roles:
            roles[speaker] = "shark"
            confidences[speaker] = 0.7

    return roles, confidences


# ---------------------------------------------------------------------------
# Segmentation and Signal Extraction
# ---------------------------------------------------------------------------

_sentiment: Optional[SentimentIntensityAnalyzer] = None


def _get_sentiment() -> SentimentIntensityAnalyzer:
    global _sentiment
    if _sentiment is None:
        _sentiment = SentimentIntensityAnalyzer()
    return _sentiment


def _matches_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(p, text, re.IGNORECASE) for p in patterns)


def _parse_dollar_amount(match: re.Match) -> float:
    raw = match.group(1).replace(",", "")
    value = float(raw)
    multiplier_str = (match.group(2) or "").lower()
    multipliers = {
        "thousand": 1_000, "k": 1_000,
        "million": 1_000_000, "m": 1_000_000,
        "billion": 1_000_000_000, "b": 1_000_000_000,
    }
    return value * multipliers.get(multiplier_str, 1)


def _extract_max_dollar(text: str) -> float:
    matches = DOLLAR_PATTERN.finditer(text)
    amounts = [_parse_dollar_amount(m) for m in matches]
    return max(amounts, default=0.0)


def segment_pitch(
    pitch_blocks: list[SubtitleBlock],
    roles: dict[str, str],
) -> PitchSegments:
    """Segment a pitch's blocks using speaker roles and content patterns."""
    segments = PitchSegments()
    first_shark_question_seen = False

    for block in pitch_blocks:
        role = roles.get(block.speaker, "unknown")
        text = block.text

        if role == "narrator":
            continue

        # Entrepreneur intro lines should not be treated as negotiation
        is_intro = role == "entrepreneur" and ENTREPRENEUR_INTRO_PATTERN.search(text)

        if _matches_any(text, OBJECTION_PATTERNS):
            segments.objections.append(block)
            continue

        if not is_intro and _matches_any(text, NEGOTIATION_PATTERNS):
            segments.negotiation.append(block)
            continue

        if role == "entrepreneur" and DEMO_KEYWORDS.search(text):
            segments.product_demo.append(block)
            continue

        if role == "shark" and "?" in text:
            segments.shark_questions.append(block)
            first_shark_question_seen = True
            continue

        if role == "shark":
            segments.shark_questions.append(block)
            first_shark_question_seen = True
            continue

        if role == "entrepreneur":
            if not first_shark_question_seen:
                segments.founder_pitch.append(block)
            else:
                segments.shark_questions.append(block)
            continue

    # Closing reason: blocks after final objection/negotiation
    all_tagged = (
        [(b, "obj") for b in segments.objections]
        + [(b, "neg") for b in segments.negotiation]
    )
    if all_tagged:
        last_action_time = max(b.start_seconds for b, _ in all_tagged)
        closing = [
            b for b in pitch_blocks
            if b.start_seconds > last_action_time
            and roles.get(b.speaker) != "narrator"
        ]
        if closing:
            segments.closing_reason = closing

    return segments


def extract_signals(
    pitch_blocks: list[SubtitleBlock],
    segments: PitchSegments,
    roles: dict[str, str],
) -> ExtractedSignals:
    """Extract NLP signals from a segmented pitch."""
    sia = _get_sentiment()
    signals = ExtractedSignals()

    entrepreneur_text = " ".join(
        b.text for b in segments.founder_pitch + segments.product_demo
    )
    signals.revenue_mentioned = _extract_max_dollar(entrepreneur_text)

    full_text = " ".join(b.text for b in pitch_blocks)
    for sent in re.split(r"[.!?]", full_text):
        if MARKET_SIZE_PATTERN.search(sent):
            amount = _extract_max_dollar(sent)
            if amount > signals.market_size_claim:
                signals.market_size_claim = amount

    if entrepreneur_text:
        scores = sia.polarity_scores(entrepreneur_text)
        signals.founder_confidence = round(scores["compound"], 4)

    shark_texts: dict[str, list[str]] = {}
    for block in pitch_blocks:
        if roles.get(block.speaker) == "shark":
            shark_texts.setdefault(block.speaker, []).append(block.text)

    max_enthusiasm = 0.0
    for speaker, texts in shark_texts.items():
        combined = " ".join(texts)
        score = sia.polarity_scores(combined)["compound"]
        if score > max_enthusiasm:
            max_enthusiasm = score
    signals.shark_enthusiasm_max = round(max_enthusiasm, 4)

    signals.objection_count = len(segments.objections)
    signals.negotiation_rounds = len(segments.negotiation)

    return signals
