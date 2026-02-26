# Phase 1 Pipeline Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the complete Shark Tank AI analysis pipeline from SRT transcript parsing through FastAPI endpoints.

**Architecture:** Monolithic Python pipeline with 6 modules: srt_parser (rewrite) -> kaggle_loader -> embed_pipeline -> deal_predictor -> retrieval_chain -> api. Storage: PostgreSQL + Pinecone. Neo4j deferred to Phase 2.

**Tech Stack:** Python 3.11+, spaCy, VADER, XGBoost, OpenAI embeddings, Pinecone, LangChain, Claude API, FastAPI, PostgreSQL/SQLAlchemy.

**Design doc:** `docs/plans/2026-02-26-phase1-pipeline-design.md`

---

## Task 1: Project Setup and Dependencies

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `src/__init__.py` (already exists)
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

**Step 1: Create requirements.txt**

```
# Core
pandas>=2.0
numpy>=1.24
scikit-learn>=1.3
xgboost>=2.0
shap>=0.43

# NLP
spacy>=3.7
vaderSentiment>=3.3

# Embeddings & Vector Store
openai>=1.0
pinecone-client>=3.0

# RAG
langchain>=0.2
langchain-anthropic>=0.1
langchain-openai>=0.1
langchain-pinecone>=0.1

# API
fastapi>=0.110
uvicorn>=0.27
pydantic>=2.0

# Database
sqlalchemy>=2.0
psycopg2-binary>=2.9
alembic>=1.13

# Dev
pytest>=8.0
httpx>=0.27
python-dotenv>=1.0
```

**Step 2: Create .env.example**

```
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
PINECONE_API_KEY=
PINECONE_INDEX_NAME=shark-tank-engine
DATABASE_URL=postgresql://localhost:5432/sharktank
```

**Step 3: Create tests/conftest.py with shared fixtures**

```python
"""Shared test fixtures for the Shark Tank AI Engine."""

import pytest


SAMPLE_SRT_BRACKET = """1
00:00:00,000 --> 00:00:03,000
[Speaker_1] Welcome to Shark Tank.

2
00:00:03,000 --> 00:00:06,000
[Speaker_1] Tonight, five entrepreneurs will pitch their ideas.

3
00:00:06,000 --> 00:00:10,000
[Speaker_1] First into the tank is Jane Smith, with a revolutionary new product.

4
00:00:10,000 --> 00:00:15,000
[Speaker_2] Hello, my name is Jane Smith from Austin, Texas.

5
00:00:15,000 --> 00:00:20,000
[Speaker_2] I'm asking for $200,000 for 10% of my company, FreshBites.

6
00:00:20,000 --> 00:00:25,000
[Speaker_2] We make healthy snack bars with $500,000 in sales last year.

7
00:00:25,000 --> 00:00:28,000
[Speaker_2] Let me show you how they taste.

8
00:00:28,000 --> 00:00:32,000
[Speaker_3] What's your margin on these?

9
00:00:32,000 --> 00:00:35,000
[Speaker_2] We're at about 40% gross margin.

10
00:00:35,000 --> 00:00:38,000
[Speaker_4] I love this product. How did you get into retail?

11
00:00:38,000 --> 00:00:42,000
[Speaker_2] We started at farmers markets and now we're in 200 stores.

12
00:00:42,000 --> 00:00:45,000
[Speaker_3] The problem is your valuation is too high. I'm out.

13
00:00:45,000 --> 00:00:48,000
[Speaker_5] For that reason, I'm out.

14
00:00:48,000 --> 00:00:52,000
[Speaker_4] I'll offer you $200,000 for 25%.

15
00:00:52,000 --> 00:00:55,000
[Speaker_2] Would you consider 20%?

16
00:00:55,000 --> 00:00:58,000
[Speaker_4] I'll do 22%. Final offer.

17
00:00:58,000 --> 00:01:02,000
[Speaker_2] Deal. Thank you so much.

18
00:01:02,000 --> 00:01:06,000
[Speaker_1] Next up is Bob Lee, who has a tech product the sharks won't believe.

19
00:01:06,000 --> 00:01:10,000
[Speaker_6] Hi, my name is Bob Lee. I'm asking for $1 million for 5%.

20
00:01:10,000 --> 00:01:14,000
[Speaker_6] My company is in the $50 billion dollar market of home automation.

21
00:01:14,000 --> 00:01:17,000
[Speaker_3] What are your sales?

22
00:01:17,000 --> 00:01:20,000
[Speaker_6] We did $100,000 last year.

23
00:01:20,000 --> 00:01:24,000
[Speaker_3] You're crazy. $1 million for a company doing $100K? I'm out.

24
00:01:24,000 --> 00:01:27,000
[Speaker_4] I don't see how this scales. I'm out.

25
00:01:27,000 --> 00:01:30,000
[Speaker_5] Not for me. I'm out.
"""


SAMPLE_SRT_COLON = """1
00:00:00,000 --> 00:00:03,000
Speaker_1: Welcome to Shark Tank.

2
00:00:03,000 --> 00:00:06,000
Speaker_1: Tonight, five entrepreneurs will pitch their ideas.

3
00:00:06,000 --> 00:00:10,000
Speaker_1: First into the tank is Jane Smith, with a revolutionary new product.

4
00:00:10,000 --> 00:00:15,000
Speaker_2: Hello, my name is Jane Smith from Austin, Texas.

5
00:00:15,000 --> 00:00:20,000
Speaker_2: I'm asking for $200,000 for 10% of my company, FreshBites.

6
00:00:20,000 --> 00:00:25,000
Speaker_2: We make healthy snack bars with $500,000 in sales last year.

7
00:00:25,000 --> 00:00:28,000
Speaker_2: Let me show you how they taste.

8
00:00:28,000 --> 00:00:32,000
Speaker_3: What's your margin on these?

9
00:00:32,000 --> 00:00:35,000
Speaker_2: We're at about 40% gross margin.

10
00:00:35,000 --> 00:00:38,000
Speaker_4: I love this product. How did you get into retail?

11
00:00:38,000 --> 00:00:42,000
Speaker_2: We started at farmers markets and now we're in 200 stores.

12
00:00:42,000 --> 00:00:45,000
Speaker_3: The problem is your valuation is too high. I'm out.

13
00:00:45,000 --> 00:00:48,000
Speaker_5: For that reason, I'm out.

14
00:00:48,000 --> 00:00:52,000
Speaker_4: I'll offer you $200,000 for 25%.

15
00:00:52,000 --> 00:00:55,000
Speaker_2: Would you consider 20%?

16
00:00:55,000 --> 00:00:58,000
Speaker_4: I'll do 22%. Final offer.

17
00:00:58,000 --> 00:01:02,000
Speaker_2: Deal. Thank you so much.

18
00:01:02,000 --> 00:01:06,000
Speaker_1: Next up is Bob Lee, who has a tech product the sharks won't believe.

19
00:01:06,000 --> 00:01:10,000
Speaker_6: Hi, my name is Bob Lee. I'm asking for $1 million for 5%.

20
00:01:10,000 --> 00:01:14,000
Speaker_6: My company is in the $50 billion dollar market of home automation.

21
00:01:14,000 --> 00:01:17,000
Speaker_3: What are your sales?

22
00:01:17,000 --> 00:01:20,000
Speaker_6: We did $100,000 last year.

23
00:01:20,000 --> 00:01:24,000
Speaker_3: You're crazy. $1 million for a company doing $100K? I'm out.

24
00:01:24,000 --> 00:01:27,000
Speaker_4: I don't see how this scales. I'm out.

25
00:01:27,000 --> 00:01:30,000
Speaker_5: Not for me. I'm out.
"""


@pytest.fixture
def sample_srt_bracket():
    return SAMPLE_SRT_BRACKET


@pytest.fixture
def sample_srt_colon():
    return SAMPLE_SRT_COLON


@pytest.fixture
def sample_srt_file(tmp_path, sample_srt_bracket):
    srt_file = tmp_path / "S01E01_with_speakers.srt"
    srt_file.write_text(sample_srt_bracket, encoding="utf-8")
    return srt_file


@pytest.fixture
def sample_srt_dir(tmp_path, sample_srt_bracket, sample_srt_colon):
    srt_file1 = tmp_path / "S01E01_with_speakers.srt"
    srt_file1.write_text(sample_srt_bracket, encoding="utf-8")
    srt_file2 = tmp_path / "S03E01.srt"
    srt_file2.write_text(sample_srt_colon, encoding="utf-8")
    return tmp_path
```

**Step 4: Create tests/__init__.py**

Empty file.

**Step 5: Install dependencies and spaCy model**

Run: `pip3 install --break-system-packages -r requirements.txt && python3 -m spacy download en_core_web_sm`
Expected: All packages install successfully.

**Step 6: Commit**

```bash
git add requirements.txt .env.example tests/__init__.py tests/conftest.py
git commit -m "feat: add project dependencies and test fixtures"
```

---

## Task 2: SRT Parser — Core Parsing (Rewrite)

Rewrite `src/ingestion/srt_parser.py` from scratch. This task handles SRT parsing and speaker label extraction for both formats.

**Files:**
- Rewrite: `src/ingestion/srt_parser.py`
- Create: `tests/test_srt_parser.py`

**Step 1: Write failing tests for SRT block parsing and speaker extraction**

Create `tests/test_srt_parser.py`:

```python
"""Tests for the SRT parser module."""

from src.ingestion.srt_parser import (
    SubtitleBlock,
    parse_srt,
    parse_srt_file,
)


class TestParseSrt:
    """Test raw SRT text parsing."""

    def test_parse_bracket_format(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        assert len(blocks) == 25
        assert blocks[0].index == 1
        assert blocks[0].start_seconds == 0.0
        assert blocks[0].end_seconds == 3.0
        assert blocks[0].speaker == "Speaker_1"
        assert blocks[0].text == "Welcome to Shark Tank."

    def test_parse_colon_format(self, sample_srt_colon):
        blocks = parse_srt(sample_srt_colon)
        assert len(blocks) == 25
        assert blocks[0].speaker == "Speaker_1"
        assert blocks[0].text == "Welcome to Shark Tank."

    def test_speaker_extracted_from_brackets(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        assert blocks[3].speaker == "Speaker_2"
        assert "Jane Smith" in blocks[3].text

    def test_speaker_extracted_from_colon(self, sample_srt_colon):
        blocks = parse_srt(sample_srt_colon)
        assert blocks[3].speaker == "Speaker_2"
        assert "Jane Smith" in blocks[3].text

    def test_timestamps_parsed_correctly(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        # Block 3: 00:00:06,000 --> 00:00:10,000
        assert blocks[2].start_seconds == 6.0
        assert blocks[2].end_seconds == 10.0
        # Block 18: 00:01:02,000 --> 00:01:06,000
        assert blocks[17].start_seconds == 62.0
        assert blocks[17].end_seconds == 66.0

    def test_html_tags_stripped(self):
        srt = """1
00:00:00,000 --> 00:00:03,000
[Speaker_1] <i>Welcome</i> to <b>Shark Tank</b>.
"""
        blocks = parse_srt(srt)
        assert blocks[0].text == "Welcome to Shark Tank."

    def test_empty_input(self):
        blocks = parse_srt("")
        assert blocks == []

    def test_malformed_blocks_skipped(self):
        srt = """not a number
00:00:00,000 --> 00:00:03,000
[Speaker_1] This should be skipped.

2
bad timestamp
[Speaker_1] This too.

3
00:00:06,000 --> 00:00:10,000
[Speaker_1] This one is valid.
"""
        blocks = parse_srt(srt)
        assert len(blocks) == 1
        assert blocks[0].text == "This one is valid."


class TestParseSrtFile:
    """Test SRT file reading."""

    def test_read_file(self, sample_srt_file):
        blocks = parse_srt_file(sample_srt_file)
        assert len(blocks) == 25

    def test_file_not_found(self, tmp_path):
        import pytest
        with pytest.raises(FileNotFoundError):
            parse_srt_file(tmp_path / "nonexistent.srt")
```

**Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_srt_parser.py -v`
Expected: FAIL — current srt_parser.py has no `speaker` field on SubtitleBlock.

**Step 3: Rewrite srt_parser.py — core parsing only**

Rewrite `src/ingestion/srt_parser.py` with:

```python
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
```

**Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_srt_parser.py -v`
Expected: All tests PASS.

**Step 5: Commit**

```bash
git add src/ingestion/srt_parser.py tests/test_srt_parser.py
git commit -m "feat: rewrite SRT parser with speaker label extraction

Handles both [Speaker_N] bracket and Speaker_N: colon formats.
Extracts speaker labels, timestamps, and clean text per block."
```

---

## Task 3: SRT Parser — Pitch Splitting

Split a full episode SRT into individual pitches using narrator boundary detection.

**Files:**
- Modify: `src/ingestion/srt_parser.py`
- Modify: `tests/test_srt_parser.py`

**Step 1: Write failing tests for pitch splitting**

Add to `tests/test_srt_parser.py`:

```python
from src.ingestion.srt_parser import split_into_pitches


class TestSplitIntoPitches:
    """Test splitting episode SRT into individual pitches."""

    def test_two_pitches_bracket_format(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        pitches = split_into_pitches(blocks)
        assert len(pitches) == 2

    def test_two_pitches_colon_format(self, sample_srt_colon):
        blocks = parse_srt(sample_srt_colon)
        pitches = split_into_pitches(blocks)
        assert len(pitches) == 2

    def test_first_pitch_contains_jane(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        pitches = split_into_pitches(blocks)
        first_pitch_text = " ".join(b.text for b in pitches[0])
        assert "Jane Smith" in first_pitch_text

    def test_second_pitch_contains_bob(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        pitches = split_into_pitches(blocks)
        second_pitch_text = " ".join(b.text for b in pitches[1])
        assert "Bob Lee" in second_pitch_text

    def test_intro_blocks_excluded_from_pitches(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        pitches = split_into_pitches(blocks)
        # First two blocks are intro ("Welcome...", "Tonight...")
        # Pitches should start from the boundary line
        first_block = pitches[0][0]
        assert "First into the tank" in first_block.text or "Jane" in first_block.text

    def test_single_pitch_no_boundary(self):
        srt = """1
00:00:00,000 --> 00:00:05,000
[Speaker_1] Hello, my name is Alice. I'm asking for $100,000 for 10%.

2
00:00:05,000 --> 00:00:10,000
[Speaker_2] What are your sales?
"""
        blocks = parse_srt(srt)
        pitches = split_into_pitches(blocks)
        assert len(pitches) == 1

    def test_empty_input(self):
        pitches = split_into_pitches([])
        assert pitches == []
```

**Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_srt_parser.py::TestSplitIntoPitches -v`
Expected: FAIL — `split_into_pitches` not defined.

**Step 3: Implement split_into_pitches**

Add to `src/ingestion/srt_parser.py`:

```python
def split_into_pitches(blocks: list[SubtitleBlock]) -> list[list[SubtitleBlock]]:
    """Split an episode's subtitle blocks into individual pitch segments.

    Uses narrator boundary patterns like "First into the tank is..."
    and "Next up is..." to detect where each pitch begins.
    Intro/outro blocks before the first pitch boundary are discarded.
    """
    if not blocks:
        return []

    # Find boundary indices
    boundaries: list[int] = []
    for i, block in enumerate(blocks):
        if PITCH_BOUNDARY_PATTERN.search(block.text):
            boundaries.append(i)

    # No boundaries found — treat entire episode as one pitch
    if not boundaries:
        return [blocks]

    # Split into pitch segments
    pitches: list[list[SubtitleBlock]] = []
    for i, start_idx in enumerate(boundaries):
        end_idx = boundaries[i + 1] if i + 1 < len(boundaries) else len(blocks)
        pitch_blocks = blocks[start_idx:end_idx]
        if pitch_blocks:
            pitches.append(pitch_blocks)

    return pitches
```

**Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_srt_parser.py::TestSplitIntoPitches -v`
Expected: All PASS.

**Step 5: Commit**

```bash
git add src/ingestion/srt_parser.py tests/test_srt_parser.py
git commit -m "feat: add pitch boundary detection and splitting

Splits episode SRT into individual pitches using narrator
transition patterns (First into the tank, Next up, etc.)."
```

---

## Task 4: SRT Parser — Role Classification

Classify Speaker_N labels as narrator, entrepreneur, or shark within each pitch.

**Files:**
- Modify: `src/ingestion/srt_parser.py`
- Modify: `tests/test_srt_parser.py`

**Step 1: Write failing tests for role classification**

Add to `tests/test_srt_parser.py`:

```python
from src.ingestion.srt_parser import classify_speakers


class TestClassifySpeakers:
    """Test speaker role classification."""

    def test_narrator_identified(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        pitches = split_into_pitches(blocks)
        roles, confidences = classify_speakers(pitches[0], blocks)
        # Speaker_1 is the narrator (intro lines, boundary announcements)
        assert roles["Speaker_1"] == "narrator"

    def test_entrepreneur_identified(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        pitches = split_into_pitches(blocks)
        roles, confidences = classify_speakers(pitches[0], blocks)
        # Speaker_2 says "my name is Jane Smith" and "I'm asking for"
        assert roles["Speaker_2"] == "entrepreneur"

    def test_sharks_identified(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        pitches = split_into_pitches(blocks)
        roles, confidences = classify_speakers(pitches[0], blocks)
        # Speaker_3, 4, 5 are sharks (ask questions, make offers, go out)
        shark_speakers = [s for s, r in roles.items() if r == "shark"]
        assert len(shark_speakers) >= 2

    def test_confidence_scores_between_0_and_1(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        pitches = split_into_pitches(blocks)
        roles, confidences = classify_speakers(pitches[0], blocks)
        for speaker, score in confidences.items():
            assert 0.0 <= score <= 1.0

    def test_second_pitch_different_entrepreneur(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        pitches = split_into_pitches(blocks)
        roles1, _ = classify_speakers(pitches[0], blocks)
        roles2, _ = classify_speakers(pitches[1], blocks)
        # First pitch entrepreneur is Speaker_2, second is Speaker_6
        entrepreneurs1 = [s for s, r in roles1.items() if r == "entrepreneur"]
        entrepreneurs2 = [s for s, r in roles2.items() if r == "entrepreneur"]
        assert entrepreneurs1 != entrepreneurs2
```

**Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_srt_parser.py::TestClassifySpeakers -v`
Expected: FAIL — `classify_speakers` not defined.

**Step 3: Implement classify_speakers**

Add to `src/ingestion/srt_parser.py`:

```python
def classify_speakers(
    pitch_blocks: list[SubtitleBlock],
    all_blocks: list[SubtitleBlock],
) -> tuple[dict[str, str], dict[str, float]]:
    """Classify Speaker_N labels as narrator, entrepreneur, or shark.

    Args:
        pitch_blocks: Blocks belonging to this specific pitch.
        all_blocks: All blocks in the episode (for narrator detection).

    Returns:
        Tuple of (role_map, confidence_map).
        role_map: {"Speaker_1": "narrator", "Speaker_2": "entrepreneur", ...}
        confidence_map: {"Speaker_1": 0.95, "Speaker_2": 0.9, ...}
    """
    roles: dict[str, str] = {}
    confidences: dict[str, float] = {}

    # Collect all unique speakers in this pitch
    pitch_speakers = set(b.speaker for b in pitch_blocks if b.speaker)

    # --- Narrator detection ---
    # The narrator is the speaker who delivers pitch boundary lines
    # and appears most in intro/outro segments across the full episode.
    narrator_scores: dict[str, int] = {}
    for block in all_blocks:
        if not block.speaker:
            continue
        if PITCH_BOUNDARY_PATTERN.search(block.text):
            narrator_scores[block.speaker] = narrator_scores.get(block.speaker, 0) + 3
        # Narrator phrases: "sharks are out", "only has X more chances"
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

    # --- Entrepreneur detection ---
    # The entrepreneur introduces themselves and dominates early lines.
    entrepreneur_scores: dict[str, float] = {}
    for block in pitch_blocks:
        if not block.speaker or block.speaker == narrator_speaker:
            continue
        score = entrepreneur_scores.get(block.speaker, 0.0)
        if ENTREPRENEUR_INTRO_PATTERN.search(block.text):
            score += 3.0
        # Early blocks (first 40% of pitch) weighted higher for entrepreneur
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

    # --- Sharks: everyone else in the pitch ---
    for speaker in pitch_speakers:
        if speaker not in roles:
            roles[speaker] = "shark"
            # Confidence based on how clearly they're not narrator/entrepreneur
            confidences[speaker] = 0.7

    return roles, confidences
```

**Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_srt_parser.py::TestClassifySpeakers -v`
Expected: All PASS.

**Step 5: Commit**

```bash
git add src/ingestion/srt_parser.py tests/test_srt_parser.py
git commit -m "feat: add speaker role classification

Classifies Speaker_N as narrator/entrepreneur/shark using
boundary patterns, intro phrases, and position heuristics."
```

---

## Task 5: SRT Parser — Segmentation and Signal Extraction

Segment each pitch's blocks by role and extract NLP signals.

**Files:**
- Modify: `src/ingestion/srt_parser.py`
- Modify: `tests/test_srt_parser.py`

**Step 1: Write failing tests for segmentation and signals**

Add to `tests/test_srt_parser.py`:

```python
from src.ingestion.srt_parser import (
    segment_pitch,
    extract_signals,
    ExtractedSignals,
    PitchSegments,
)


class TestSegmentPitch:
    """Test pitch segmentation by role and content."""

    def test_founder_pitch_captured(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        pitches = split_into_pitches(blocks)
        roles, _ = classify_speakers(pitches[0], blocks)
        segments = segment_pitch(pitches[0], roles)
        assert len(segments.founder_pitch) > 0
        # Entrepreneur lines should be in founder_pitch
        texts = [b.text for b in segments.founder_pitch]
        assert any("asking for" in t for t in texts)

    def test_product_demo_captured(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        pitches = split_into_pitches(blocks)
        roles, _ = classify_speakers(pitches[0], blocks)
        segments = segment_pitch(pitches[0], roles)
        # "Let me show you how they taste" should be product_demo
        demo_texts = [b.text for b in segments.product_demo]
        assert any("show" in t.lower() for t in demo_texts)

    def test_objections_captured(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        pitches = split_into_pitches(blocks)
        roles, _ = classify_speakers(pitches[0], blocks)
        segments = segment_pitch(pitches[0], roles)
        assert len(segments.objections) >= 2
        obj_texts = [b.text for b in segments.objections]
        assert any("I'm out" in t for t in obj_texts)

    def test_negotiation_captured(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        pitches = split_into_pitches(blocks)
        roles, _ = classify_speakers(pitches[0], blocks)
        segments = segment_pitch(pitches[0], roles)
        assert len(segments.negotiation) >= 1

    def test_shark_questions_captured(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        pitches = split_into_pitches(blocks)
        roles, _ = classify_speakers(pitches[0], blocks)
        segments = segment_pitch(pitches[0], roles)
        assert len(segments.shark_questions) >= 1
        q_texts = [b.text for b in segments.shark_questions]
        assert any("?" in t for t in q_texts)


class TestExtractSignals:
    """Test NLP signal extraction."""

    def test_revenue_extracted(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        pitches = split_into_pitches(blocks)
        roles, _ = classify_speakers(pitches[0], blocks)
        segments = segment_pitch(pitches[0], roles)
        signals = extract_signals(pitches[0], segments, roles)
        # "$500,000 in sales" mentioned in pitch
        assert signals.revenue_mentioned == 500_000.0

    def test_objection_count(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        pitches = split_into_pitches(blocks)
        roles, _ = classify_speakers(pitches[0], blocks)
        segments = segment_pitch(pitches[0], roles)
        signals = extract_signals(pitches[0], segments, roles)
        assert signals.objection_count >= 2

    def test_negotiation_rounds(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        pitches = split_into_pitches(blocks)
        roles, _ = classify_speakers(pitches[0], blocks)
        segments = segment_pitch(pitches[0], roles)
        signals = extract_signals(pitches[0], segments, roles)
        assert signals.negotiation_rounds >= 1

    def test_founder_confidence_is_float(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        pitches = split_into_pitches(blocks)
        roles, _ = classify_speakers(pitches[0], blocks)
        segments = segment_pitch(pitches[0], roles)
        signals = extract_signals(pitches[0], segments, roles)
        assert isinstance(signals.founder_confidence, float)
        assert -1.0 <= signals.founder_confidence <= 1.0

    def test_market_size_from_second_pitch(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        pitches = split_into_pitches(blocks)
        roles, _ = classify_speakers(pitches[1], blocks)
        segments = segment_pitch(pitches[1], roles)
        signals = extract_signals(pitches[1], segments, roles)
        # "$50 billion dollar market" mentioned
        assert signals.market_size_claim == 50_000_000_000.0
```

**Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_srt_parser.py::TestSegmentPitch tests/test_srt_parser.py::TestExtractSignals -v`
Expected: FAIL — `segment_pitch` and `extract_signals` not defined (or wrong signature).

**Step 3: Implement segment_pitch and extract_signals**

Add to `src/ingestion/srt_parser.py`:

```python
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

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
    """Segment a pitch's blocks using speaker roles and content patterns.

    Priority order: objections > negotiation > product_demo > shark_questions > founder_pitch.
    Narrator lines are excluded from all segments.
    """
    segments = PitchSegments()
    first_shark_question_seen = False

    for block in pitch_blocks:
        role = roles.get(block.speaker, "unknown")
        text = block.text

        # Skip narrator lines
        if role == "narrator":
            continue

        # Objections (highest priority — most specific patterns)
        if _matches_any(text, OBJECTION_PATTERNS):
            segments.objections.append(block)
            continue

        # Negotiation
        if _matches_any(text, NEGOTIATION_PATTERNS):
            segments.negotiation.append(block)
            continue

        # Product demo (entrepreneur lines with demo keywords)
        if role == "entrepreneur" and DEMO_KEYWORDS.search(text):
            segments.product_demo.append(block)
            continue

        # Shark questions (shark lines with ?)
        if role == "shark" and "?" in text:
            segments.shark_questions.append(block)
            first_shark_question_seen = True
            continue

        # Shark statements (non-question shark dialogue)
        if role == "shark":
            segments.shark_questions.append(block)
            first_shark_question_seen = True
            continue

        # Founder pitch (entrepreneur lines before heavy shark interaction)
        if role == "entrepreneur":
            if not first_shark_question_seen:
                segments.founder_pitch.append(block)
            else:
                # After shark questions start, entrepreneur responses
                # go to shark_questions as Q&A context
                segments.shark_questions.append(block)
            continue

    # Closing reason: last blocks after final objection/negotiation
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

    # Revenue: largest $ amount in entrepreneur lines
    entrepreneur_text = " ".join(
        b.text for b in segments.founder_pitch + segments.product_demo
    )
    signals.revenue_mentioned = _extract_max_dollar(entrepreneur_text)

    # Market size: $ amounts near market size keywords
    full_text = " ".join(b.text for b in pitch_blocks)
    for sent in re.split(r"[.!?]", full_text):
        if MARKET_SIZE_PATTERN.search(sent):
            amount = _extract_max_dollar(sent)
            if amount > signals.market_size_claim:
                signals.market_size_claim = amount

    # Founder confidence: VADER on entrepreneur lines
    if entrepreneur_text:
        scores = sia.polarity_scores(entrepreneur_text)
        signals.founder_confidence = round(scores["compound"], 4)

    # Shark enthusiasm: highest VADER across individual shark speakers
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

    # Objection count
    signals.objection_count = len(segments.objections)

    # Negotiation rounds
    signals.negotiation_rounds = len(segments.negotiation)

    return signals
```

**Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_srt_parser.py -v`
Expected: All tests PASS.

**Step 5: Commit**

```bash
git add src/ingestion/srt_parser.py tests/test_srt_parser.py
git commit -m "feat: add pitch segmentation and NLP signal extraction

Segments by role (entrepreneur/shark/narrator) and content patterns.
Extracts revenue, market size, sentiment, objections, negotiations."
```

---

## Task 6: SRT Parser — Public API and CLI

Wire up the full pipeline: `parse_episode` and `parse_all_episodes`.

**Files:**
- Modify: `src/ingestion/srt_parser.py`
- Modify: `tests/test_srt_parser.py`

**Step 1: Write failing tests for public API**

Add to `tests/test_srt_parser.py`:

```python
from src.ingestion.srt_parser import (
    parse_episode,
    parse_all_episodes,
    ParsedPitch,
)


class TestParseEpisode:
    """Test full episode parsing pipeline."""

    def test_returns_parsed_pitches(self, sample_srt_file):
        pitches = parse_episode(sample_srt_file)
        assert len(pitches) == 2
        assert all(isinstance(p, ParsedPitch) for p in pitches)

    def test_episode_code_extracted(self, sample_srt_file):
        pitches = parse_episode(sample_srt_file)
        assert pitches[0].episode == "S01E01"

    def test_entrepreneur_name_extracted(self, sample_srt_file):
        pitches = parse_episode(sample_srt_file)
        assert "Jane Smith" in pitches[0].entrepreneur_name

    def test_pitch_index_sequential(self, sample_srt_file):
        pitches = parse_episode(sample_srt_file)
        assert pitches[0].pitch_index == 0
        assert pitches[1].pitch_index == 1

    def test_signals_populated(self, sample_srt_file):
        pitches = parse_episode(sample_srt_file)
        assert pitches[0].signals.revenue_mentioned > 0
        assert pitches[0].signals.objection_count >= 2

    def test_to_dict_serializable(self, sample_srt_file):
        import json
        pitches = parse_episode(sample_srt_file)
        # Should not raise
        json.dumps(pitches[0].to_dict())


class TestParseAllEpisodes:
    """Test batch episode parsing."""

    def test_parses_multiple_files(self, sample_srt_dir):
        pitches = parse_all_episodes(sample_srt_dir)
        # 2 files * 2 pitches each = 4 total
        assert len(pitches) == 4

    def test_empty_directory(self, tmp_path):
        import pytest
        with pytest.raises(FileNotFoundError):
            parse_all_episodes(tmp_path)
```

**Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_srt_parser.py::TestParseEpisode tests/test_srt_parser.py::TestParseAllEpisodes -v`
Expected: FAIL — `parse_episode` has wrong signature / behavior.

**Step 3: Implement parse_episode and parse_all_episodes**

Add to `src/ingestion/srt_parser.py`:

```python
_EPISODE_CODE_RE = re.compile(r"S(\d{2})E(\d{2})")


def _extract_episode_code(filename: str) -> str:
    """Extract SxxExx from filename like 'Shark.Tank.S01E01_with_speakers.srt'."""
    m = _EPISODE_CODE_RE.search(filename)
    return m.group(0) if m else filename


def _extract_entrepreneur_name(pitch_blocks: list[SubtitleBlock], roles: dict[str, str]) -> str:
    """Extract entrepreneur name from 'My name is ...' or boundary intro line."""
    for block in pitch_blocks:
        # Check "my name is X" pattern
        m = re.search(r"(?:my name is|i'?m)\s+([A-Z][a-z]+ [A-Z][a-z]+)", block.text)
        if m and roles.get(block.speaker) in ("entrepreneur", "narrator", ""):
            return m.group(1)
    # Fallback: check boundary line "First into the tank is X"
    for block in pitch_blocks:
        m = re.search(
            r"(?:into the (?:tank|shark tank)|next up) (?:is|are)\s+(.+?)(?:,|who|\.|$)",
            block.text, re.IGNORECASE,
        )
        if m:
            return m.group(1).strip()
    return "Unknown"


def parse_episode(path: str | Path) -> list[ParsedPitch]:
    """Full pipeline: parse SRT file -> split pitches -> classify -> segment -> signals.

    Args:
        path: Path to an SRT file.

    Returns:
        List of ParsedPitch objects, one per pitch in the episode.
    """
    path = Path(path)
    all_blocks = parse_srt_file(path)
    episode_code = _extract_episode_code(path.name)
    pitch_block_groups = split_into_pitches(all_blocks)

    results: list[ParsedPitch] = []
    for i, pitch_blocks in enumerate(pitch_block_groups):
        roles, confidences = classify_speakers(pitch_blocks, all_blocks)
        segments = segment_pitch(pitch_blocks, roles)
        signals = extract_signals(pitch_blocks, segments, roles)
        name = _extract_entrepreneur_name(pitch_blocks, roles)

        results.append(ParsedPitch(
            episode=episode_code,
            pitch_index=i,
            entrepreneur_name=name,
            segments=segments,
            signals=signals,
            speaker_map=roles,
            confidence_scores=confidences,
            raw_blocks=pitch_blocks,
        ))

    return results


def parse_all_episodes(srt_dir: str | Path) -> list[ParsedPitch]:
    """Parse all SRT files in a directory tree.

    Searches for *.srt files recursively. Returns a flat list
    of all pitches across all episodes, sorted by episode then pitch_index.
    """
    srt_dir = Path(srt_dir)
    srt_files = sorted(srt_dir.rglob("*.srt"))

    if not srt_files:
        raise FileNotFoundError(f"No .srt files found in {srt_dir}")

    all_pitches: list[ParsedPitch] = []
    for srt_file in srt_files:
        try:
            pitches = parse_episode(srt_file)
            all_pitches.extend(pitches)
        except Exception as e:
            print(f"Warning: Failed to parse {srt_file.name}: {e}")

    return all_pitches
```

Also add the CLI at the bottom:

```python
if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 2:
        print("Usage: python srt_parser.py <path-to-srt-or-directory>")
        sys.exit(1)

    target = Path(sys.argv[1])

    if target.is_file():
        pitches = parse_episode(target)
        output = [p.to_dict() for p in pitches]
        print(json.dumps(output, indent=2))
    elif target.is_dir():
        pitches = parse_all_episodes(target)
        output = [p.to_dict() for p in pitches]
        print(json.dumps(output, indent=2))
    else:
        print(f"Error: {target} is not a valid file or directory")
        sys.exit(1)
```

**Step 4: Run all srt_parser tests**

Run: `python3 -m pytest tests/test_srt_parser.py -v`
Expected: All PASS.

**Step 5: Smoke test against real data**

Run: `python3 -m src.ingestion.srt_parser "transcripts/transcripts season 1/Shark.Tank.S01E01_with_speakers.srt" | python3 -m json.tool | head -50`
Expected: JSON output with multiple pitches, each with segments and signals.

**Step 6: Commit**

```bash
git add src/ingestion/srt_parser.py tests/test_srt_parser.py
git commit -m "feat: add parse_episode and parse_all_episodes public API

Full pipeline: SRT -> pitch split -> role classify -> segment -> signals.
Extracts episode codes and entrepreneur names from filenames/text."
```

---

## Task 7: Kaggle Loader

Build `src/ingestion/kaggle_loader.py`. Since the CSV isn't available yet, build the loader with a well-defined interface that can be tested with synthetic data.

**Files:**
- Create: `src/ingestion/kaggle_loader.py`
- Create: `tests/test_kaggle_loader.py`

**Step 1: Write failing tests**

Create `tests/test_kaggle_loader.py`:

```python
"""Tests for the Kaggle data loader."""

import pandas as pd
import pytest

from src.ingestion.kaggle_loader import (
    DealRecord,
    load_kaggle_csv,
    clean_and_engineer,
    link_srt_pitches,
)


@pytest.fixture
def sample_csv(tmp_path):
    """Create a minimal Kaggle-like CSV."""
    data = {
        "Season Number": [1, 1],
        "Episode Number": [1, 1],
        "Pitchers": ["Jane Smith", "Bob Lee"],
        "Company/Brand": ["FreshBites", "HomeBot"],
        "Industry": ["Food", "Technology"],
        "Deal or No Deal": ["Deal", "No Deal"],
        "Ask Amount (in USD)": [200000, 1000000],
        "Equity Requested (%)": [10.0, 5.0],
        "Deal Amount (in USD)": [200000, None],
        "Deal Equity (%)": [22.0, None],
        "Number of Sharks in Deal": [1, 0],
        "Sharks in Deal": ["Barbara Corcoran", None],
        "Yearly Revenue (in USD)": [500000, 100000],
        "Number of Pitchers": [1, 1],
    }
    df = pd.DataFrame(data)
    csv_path = tmp_path / "shark_tank_us_dataset.csv"
    df.to_csv(csv_path, index=False)
    return csv_path


class TestLoadKaggleCsv:
    def test_loads_csv(self, sample_csv):
        df = load_kaggle_csv(sample_csv)
        assert len(df) == 2

    def test_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_kaggle_csv(tmp_path / "missing.csv")


class TestCleanAndEngineer:
    def test_implied_valuation(self, sample_csv):
        df = load_kaggle_csv(sample_csv)
        records = clean_and_engineer(df)
        # 200000 / 0.10 = 2000000
        assert records[0].implied_valuation == 2_000_000.0

    def test_deal_closed_flag(self, sample_csv):
        df = load_kaggle_csv(sample_csv)
        records = clean_and_engineer(df)
        assert records[0].deal_closed is True
        assert records[1].deal_closed is False

    def test_missing_deal_amount_is_none(self, sample_csv):
        df = load_kaggle_csv(sample_csv)
        records = clean_and_engineer(df)
        assert records[1].final_deal_amount is None

    def test_returns_deal_records(self, sample_csv):
        df = load_kaggle_csv(sample_csv)
        records = clean_and_engineer(df)
        assert all(isinstance(r, DealRecord) for r in records)


class TestLinkSrtPitches:
    def test_links_by_episode(self, sample_csv, sample_srt_file):
        from src.ingestion.srt_parser import parse_episode

        df = load_kaggle_csv(sample_csv)
        records = clean_and_engineer(df)
        pitches = parse_episode(sample_srt_file)
        linked = link_srt_pitches(records, pitches)
        # At least one record should get SRT signals populated
        has_signals = any(r.pitch_sentiment_score is not None for r in linked)
        assert has_signals
```

**Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_kaggle_loader.py -v`
Expected: FAIL — module not found.

**Step 3: Implement kaggle_loader.py**

Create `src/ingestion/kaggle_loader.py`:

```python
"""kaggle_loader.py — Load and clean the Kaggle Shark Tank dataset.

Loads shark_tank_us_dataset.csv, cleans it, engineers features,
and links records to SRT-parsed pitches by episode.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd

from src.ingestion.srt_parser import ParsedPitch


@dataclass
class DealRecord:
    """A single Kaggle deal record with engineered features."""
    season: int
    episode: int
    company_name: str
    industry: str
    entrepreneur_name: str
    ask_amount: float
    equity_offered_pct: float
    implied_valuation: float
    revenue_trailing_12m: float
    founder_count: int
    deal_closed: bool
    final_deal_amount: Optional[float]
    final_equity_pct: Optional[float]
    shark_ids: list[str]
    # SRT-derived (populated by link_srt_pitches)
    pitch_sentiment_score: Optional[float] = None
    shark_enthusiasm_max: Optional[float] = None
    objection_count: Optional[int] = None
    negotiation_rounds: Optional[int] = None


def load_kaggle_csv(path: str | Path) -> pd.DataFrame:
    """Load the Kaggle CSV file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")
    return pd.read_csv(path)


def clean_and_engineer(df: pd.DataFrame) -> list[DealRecord]:
    """Clean the dataframe and produce DealRecord objects."""
    records: list[DealRecord] = []

    for _, row in df.iterrows():
        ask = float(row.get("Ask Amount (in USD)", 0) or 0)
        equity = float(row.get("Equity Requested (%)", 0) or 0)
        implied_val = ask / (equity / 100) if equity > 0 else 0.0

        deal_str = str(row.get("Deal or No Deal", "No Deal"))
        deal_closed = deal_str.strip().lower() == "deal"

        deal_amount_raw = row.get("Deal Amount (in USD)")
        deal_amount = float(deal_amount_raw) if pd.notna(deal_amount_raw) else None

        deal_equity_raw = row.get("Deal Equity (%)")
        deal_equity = float(deal_equity_raw) if pd.notna(deal_equity_raw) else None

        revenue_raw = row.get("Yearly Revenue (in USD)", 0)
        revenue = float(revenue_raw) if pd.notna(revenue_raw) else 0.0

        sharks_raw = row.get("Sharks in Deal", "")
        shark_ids = [s.strip() for s in str(sharks_raw).split(",")] if pd.notna(sharks_raw) else []

        founder_count = int(row.get("Number of Pitchers", 1) or 1)

        records.append(DealRecord(
            season=int(row.get("Season Number", 0)),
            episode=int(row.get("Episode Number", 0)),
            company_name=str(row.get("Company/Brand", "Unknown")),
            industry=str(row.get("Industry", "Unknown")),
            entrepreneur_name=str(row.get("Pitchers", "Unknown")),
            ask_amount=ask,
            equity_offered_pct=equity,
            implied_valuation=implied_val,
            revenue_trailing_12m=revenue,
            founder_count=founder_count,
            deal_closed=deal_closed,
            final_deal_amount=deal_amount,
            final_equity_pct=deal_equity,
            shark_ids=shark_ids,
        ))

    return records


def link_srt_pitches(
    records: list[DealRecord],
    pitches: list[ParsedPitch],
) -> list[DealRecord]:
    """Link DealRecords to ParsedPitches by episode and name similarity.

    Populates the SRT-derived fields on matched DealRecords.
    """
    # Index pitches by episode code
    pitch_by_episode: dict[str, list[ParsedPitch]] = {}
    for pitch in pitches:
        pitch_by_episode.setdefault(pitch.episode, []).append(pitch)

    for record in records:
        episode_code = f"S{record.season:02d}E{record.episode:02d}"
        episode_pitches = pitch_by_episode.get(episode_code, [])

        # Try to match by entrepreneur name
        best_match: Optional[ParsedPitch] = None
        for pitch in episode_pitches:
            name_lower = record.entrepreneur_name.lower()
            pitch_name_lower = pitch.entrepreneur_name.lower()
            # Simple substring match
            if (name_lower in pitch_name_lower
                    or pitch_name_lower in name_lower
                    or record.company_name.lower() in " ".join(
                        b.text.lower() for b in pitch.raw_blocks)):
                best_match = pitch
                break

        # Fallback: match by pitch index (first deal in episode = first pitch, etc.)
        if best_match is None and episode_pitches:
            # Find the pitch index that hasn't been claimed yet
            for pitch in episode_pitches:
                best_match = pitch
                break

        if best_match:
            record.pitch_sentiment_score = best_match.signals.founder_confidence
            record.shark_enthusiasm_max = best_match.signals.shark_enthusiasm_max
            record.objection_count = best_match.signals.objection_count
            record.negotiation_rounds = best_match.signals.negotiation_rounds

    return records
```

**Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_kaggle_loader.py -v`
Expected: All PASS.

**Step 5: Commit**

```bash
git add src/ingestion/kaggle_loader.py tests/test_kaggle_loader.py
git commit -m "feat: add Kaggle CSV loader with SRT pitch linking

Loads, cleans, and feature-engineers Kaggle deal data.
Links records to SRT pitches by episode code and name matching."
```

---

## Task 8: Embedding Pipeline

Build `src/embeddings/embed_pipeline.py` for chunking pitches and storing in Pinecone.

**Files:**
- Create: `src/embeddings/__init__.py`
- Create: `src/embeddings/embed_pipeline.py`
- Create: `tests/test_embed_pipeline.py`

**Step 1: Write failing tests**

Create `tests/test_embed_pipeline.py`:

```python
"""Tests for the embedding pipeline."""

import pytest

from src.embeddings.embed_pipeline import (
    chunk_pitch,
    PitchChunk,
)
from src.ingestion.srt_parser import parse_srt, split_into_pitches, classify_speakers, segment_pitch


class TestChunkPitch:
    """Test pitch chunking into embeddable segments."""

    def test_returns_chunks(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        pitches = split_into_pitches(blocks)
        roles, _ = classify_speakers(pitches[0], blocks)
        segments = segment_pitch(pitches[0], roles)
        chunks = chunk_pitch(segments, episode="S01E01", pitch_index=0, company_name="FreshBites")
        assert len(chunks) > 0
        assert all(isinstance(c, PitchChunk) for c in chunks)

    def test_chunk_has_metadata(self, sample_srt_bracket):
        blocks = parse_srt(sample_srt_bracket)
        pitches = split_into_pitches(blocks)
        roles, _ = classify_speakers(pitches[0], blocks)
        segments = segment_pitch(pitches[0], roles)
        chunks = chunk_pitch(segments, episode="S01E01", pitch_index=0, company_name="FreshBites")
        chunk = chunks[0]
        assert chunk.episode == "S01E01"
        assert chunk.company_name == "FreshBites"
        assert chunk.segment_type in (
            "founder_pitch", "product_demo", "shark_questions",
            "objections", "negotiation", "closing_reason",
        )

    def test_empty_segments_skipped(self):
        from src.ingestion.srt_parser import PitchSegments
        segments = PitchSegments()  # all empty
        chunks = chunk_pitch(segments, episode="S01E01", pitch_index=0, company_name="Test")
        assert len(chunks) == 0
```

**Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_embed_pipeline.py -v`
Expected: FAIL — module not found.

**Step 3: Implement embed_pipeline.py**

Create `src/embeddings/__init__.py` (empty) and `src/embeddings/embed_pipeline.py`:

```python
"""embed_pipeline.py — Chunk pitches and embed into Pinecone.

Chunks each pitch by segment type, embeds with OpenAI text-embedding-3-large,
and upserts into Pinecone with metadata for filtered retrieval.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Optional

from src.ingestion.srt_parser import PitchSegments, ParsedPitch


SEGMENT_NAMES = [
    "founder_pitch", "product_demo", "shark_questions",
    "objections", "negotiation", "closing_reason",
]

MAX_CHUNK_TOKENS = 8000
OVERLAP_TOKENS = 200


@dataclass
class PitchChunk:
    """A single embeddable chunk from a pitch segment."""
    text: str
    episode: str
    pitch_index: int
    company_name: str
    segment_type: str
    chunk_index: int = 0


def _estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 chars per token."""
    return len(text) // 4


def _split_text(text: str, max_tokens: int, overlap_tokens: int) -> list[str]:
    """Split text into chunks with overlap if it exceeds max_tokens."""
    if _estimate_tokens(text) <= max_tokens:
        return [text]

    # Split by sentences first
    import re
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[str] = []
    current: list[str] = []
    current_tokens = 0

    for sentence in sentences:
        sent_tokens = _estimate_tokens(sentence)
        if current_tokens + sent_tokens > max_tokens and current:
            chunks.append(" ".join(current))
            # Keep overlap
            overlap_text = " ".join(current)
            overlap_chars = overlap_tokens * 4
            if len(overlap_text) > overlap_chars:
                overlap_start = overlap_text[-overlap_chars:]
                current = [overlap_start]
                current_tokens = overlap_tokens
            else:
                current = list(current)
                current_tokens = _estimate_tokens(" ".join(current))
        current.append(sentence)
        current_tokens += sent_tokens

    if current:
        chunks.append(" ".join(current))

    return chunks if chunks else [text]


def chunk_pitch(
    segments: PitchSegments,
    episode: str,
    pitch_index: int,
    company_name: str,
) -> list[PitchChunk]:
    """Split a pitch's segments into embeddable chunks."""
    chunks: list[PitchChunk] = []

    for seg_name in SEGMENT_NAMES:
        blocks = getattr(segments, seg_name, [])
        if not blocks:
            continue

        full_text = " ".join(b.text for b in blocks)
        if not full_text.strip():
            continue

        text_parts = _split_text(full_text, MAX_CHUNK_TOKENS, OVERLAP_TOKENS)
        for i, part in enumerate(text_parts):
            chunks.append(PitchChunk(
                text=part,
                episode=episode,
                pitch_index=pitch_index,
                company_name=company_name,
                segment_type=seg_name,
                chunk_index=i,
            ))

    return chunks


def embed_chunks(chunks: list[PitchChunk]) -> list[tuple[PitchChunk, list[float]]]:
    """Embed chunks using OpenAI text-embedding-3-large.

    Requires OPENAI_API_KEY in environment.
    Returns list of (chunk, embedding_vector) tuples.
    """
    from openai import OpenAI

    client = OpenAI()
    results: list[tuple[PitchChunk, list[float]]] = []

    # Batch in groups of 100 (OpenAI limit)
    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        texts = [c.text for c in batch]

        response = client.embeddings.create(
            model="text-embedding-3-large",
            input=texts,
        )

        for chunk, embedding_data in zip(batch, response.data):
            results.append((chunk, embedding_data.embedding))

        # Rate limiting
        if i + batch_size < len(chunks):
            time.sleep(0.5)

    return results


def upsert_to_pinecone(
    embedded_chunks: list[tuple[PitchChunk, list[float]]],
    index_name: Optional[str] = None,
) -> int:
    """Upsert embedded chunks into Pinecone.

    Requires PINECONE_API_KEY in environment.
    Returns count of vectors upserted.
    """
    from pinecone import Pinecone

    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    idx_name = index_name or os.environ.get("PINECONE_INDEX_NAME", "shark-tank-engine")
    index = pc.Index(idx_name)

    vectors = []
    for chunk, embedding in embedded_chunks:
        vector_id = f"{chunk.episode}_p{chunk.pitch_index}_{chunk.segment_type}_c{chunk.chunk_index}"
        metadata = {
            "episode": chunk.episode,
            "pitch_index": chunk.pitch_index,
            "company_name": chunk.company_name,
            "segment_type": chunk.segment_type,
            "text": chunk.text[:1000],  # Pinecone metadata limit
        }
        vectors.append({"id": vector_id, "values": embedding, "metadata": metadata})

    # Batch upsert (Pinecone limit: 100 vectors)
    batch_size = 100
    total = 0
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i + batch_size]
        index.upsert(vectors=batch)
        total += len(batch)

    return total


def run_pipeline(pitches: list[ParsedPitch]) -> int:
    """Full embedding pipeline: chunk -> embed -> upsert.

    Returns total vectors upserted.
    """
    all_chunks: list[PitchChunk] = []
    for pitch in pitches:
        chunks = chunk_pitch(
            pitch.segments,
            episode=pitch.episode,
            pitch_index=pitch.pitch_index,
            company_name=pitch.entrepreneur_name,
        )
        all_chunks.extend(chunks)

    if not all_chunks:
        return 0

    embedded = embed_chunks(all_chunks)
    return upsert_to_pinecone(embedded)
```

**Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_embed_pipeline.py -v`
Expected: All PASS (only chunking is tested — embed/upsert require API keys).

**Step 5: Commit**

```bash
git add src/embeddings/__init__.py src/embeddings/embed_pipeline.py tests/test_embed_pipeline.py
git commit -m "feat: add embedding pipeline with chunking and Pinecone upsert

Chunks pitches by segment type, embeds with OpenAI, upserts to Pinecone
with episode/company/segment metadata for filtered retrieval."
```

---

## Task 9: Deal Predictor

Build `src/models/deal_predictor.py` with XGBoost training and prediction.

**Files:**
- Create: `src/models/__init__.py`
- Create: `src/models/deal_predictor.py`
- Create: `tests/test_predictor.py`

**Step 1: Write failing tests**

Create `tests/test_predictor.py`:

```python
"""Tests for the deal predictor model."""

import numpy as np
import pytest

from src.models.deal_predictor import (
    prepare_features,
    train_model,
    predict,
    DealPrediction,
)
from src.ingestion.kaggle_loader import DealRecord


@pytest.fixture
def sample_records():
    """Create a set of synthetic deal records for training."""
    records = []
    for i in range(50):
        deal = i % 3 != 0  # 2/3 deals close
        records.append(DealRecord(
            season=1, episode=i // 4 + 1,
            company_name=f"Company_{i}",
            industry=["Food", "Technology", "Health"][i % 3],
            entrepreneur_name=f"Founder_{i}",
            ask_amount=100_000 + i * 10_000,
            equity_offered_pct=5 + (i % 20),
            implied_valuation=(100_000 + i * 10_000) / ((5 + i % 20) / 100),
            revenue_trailing_12m=50_000 + i * 5_000,
            founder_count=1 + i % 3,
            deal_closed=deal,
            final_deal_amount=100_000 + i * 8_000 if deal else None,
            final_equity_pct=10 + (i % 15) if deal else None,
            shark_ids=["Mark Cuban"] if deal else [],
            pitch_sentiment_score=0.5 + (i % 10) / 20,
            shark_enthusiasm_max=0.3 + (i % 10) / 20,
            objection_count=i % 5,
            negotiation_rounds=i % 4,
        ))
    return records


class TestPrepareFeatures:
    def test_returns_array_and_labels(self, sample_records):
        X, y, feature_names = prepare_features(sample_records)
        assert X.shape[0] == len(sample_records)
        assert y.shape[0] == len(sample_records)
        assert len(feature_names) == X.shape[1]

    def test_labels_are_binary(self, sample_records):
        _, y, _ = prepare_features(sample_records)
        assert set(np.unique(y)).issubset({0, 1})


class TestTrainAndPredict:
    def test_train_returns_model(self, sample_records):
        X, y, feature_names = prepare_features(sample_records)
        model, metrics = train_model(X, y)
        assert model is not None
        assert "auc_roc" in metrics

    def test_predict_returns_prediction(self, sample_records):
        X, y, feature_names = prepare_features(sample_records)
        model, _ = train_model(X, y)
        pred = predict(model, X[0:1], feature_names)
        assert isinstance(pred, DealPrediction)
        assert 0.0 <= pred.deal_probability <= 1.0
        assert 1 <= pred.deal_score <= 10
```

**Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_predictor.py -v`
Expected: FAIL — module not found.

**Step 3: Implement deal_predictor.py**

Create `src/models/__init__.py` (empty) and `src/models/deal_predictor.py`:

```python
"""deal_predictor.py — XGBoost deal prediction model.

Trains on Kaggle + SRT features to predict deal_closed (binary).
Provides SHAP-based feature importance for interpretability.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics import roc_auc_score
from xgboost import XGBClassifier

from src.ingestion.kaggle_loader import DealRecord


NUMERIC_FEATURES = [
    "ask_amount",
    "equity_offered_pct",
    "implied_valuation",
    "revenue_trailing_12m",
    "founder_count",
    "pitch_sentiment_score",
    "shark_enthusiasm_max",
    "objection_count",
    "negotiation_rounds",
]


@dataclass
class DealPrediction:
    """Prediction result for a single deal."""
    deal_probability: float
    deal_score: int  # 1-10
    feature_importances: dict[str, float] = field(default_factory=dict)


def prepare_features(records: list[DealRecord]) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Convert DealRecords into feature matrix and label vector."""
    feature_names = list(NUMERIC_FEATURES)
    X_rows: list[list[float]] = []
    y_labels: list[int] = []

    for record in records:
        row = [
            record.ask_amount,
            record.equity_offered_pct,
            record.implied_valuation,
            record.revenue_trailing_12m,
            float(record.founder_count),
            float(record.pitch_sentiment_score or 0.0),
            float(record.shark_enthusiasm_max or 0.0),
            float(record.objection_count or 0),
            float(record.negotiation_rounds or 0),
        ]
        X_rows.append(row)
        y_labels.append(1 if record.deal_closed else 0)

    return np.array(X_rows), np.array(y_labels), feature_names


def train_model(
    X: np.ndarray,
    y: np.ndarray,
    n_folds: int = 5,
) -> tuple[XGBClassifier, dict[str, float]]:
    """Train XGBoost classifier with cross-validation.

    Returns the trained model and evaluation metrics.
    """
    model = XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        eval_metric="logloss",
        use_label_encoder=False,
        random_state=42,
    )

    # Cross-validation
    cv = StratifiedKFold(n_splits=min(n_folds, len(y) // 2), shuffle=True, random_state=42)
    scores = cross_val_score(model, X, y, cv=cv, scoring="roc_auc")

    # Train on full data
    model.fit(X, y)

    metrics = {
        "auc_roc": float(np.mean(scores)),
        "auc_roc_std": float(np.std(scores)),
    }

    return model, metrics


def predict(
    model: XGBClassifier,
    X: np.ndarray,
    feature_names: list[str],
) -> DealPrediction:
    """Predict deal outcome for a single input."""
    prob = float(model.predict_proba(X)[0, 1])
    score = max(1, min(10, round(prob * 10)))

    importances = dict(zip(feature_names, model.feature_importances_))

    return DealPrediction(
        deal_probability=round(prob, 4),
        deal_score=score,
        feature_importances=importances,
    )
```

**Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_predictor.py -v`
Expected: All PASS.

**Step 5: Commit**

```bash
git add src/models/__init__.py src/models/deal_predictor.py tests/test_predictor.py
git commit -m "feat: add XGBoost deal predictor with cross-validation

Trains on Kaggle + SRT features, predicts deal probability,
returns 1-10 score with feature importances."
```

---

## Task 10: RAG Retrieval Chain

Build `src/rag/retrieval_chain.py` with LangChain + Pinecone + Claude.

**Files:**
- Create: `src/rag/__init__.py`
- Create: `src/rag/retrieval_chain.py`
- Create: `tests/test_rag.py`

**Step 1: Write failing tests**

Create `tests/test_rag.py`:

```python
"""Tests for the RAG retrieval chain (unit tests with mocks)."""

import pytest

from src.rag.retrieval_chain import (
    build_analysis_prompt,
    SYSTEM_PROMPT,
)


class TestBuildPrompt:
    def test_includes_system_prompt(self):
        prompt = build_analysis_prompt("What are the best food pitches?", [])
        assert SYSTEM_PROMPT in prompt

    def test_includes_user_query(self):
        prompt = build_analysis_prompt("What are the best food pitches?", [])
        assert "What are the best food pitches?" in prompt

    def test_includes_context(self):
        context = [
            {"text": "FreshBites had $500K revenue", "episode": "S01E01"},
        ]
        prompt = build_analysis_prompt("Tell me about food startups", context)
        assert "FreshBites" in prompt
        assert "S01E01" in prompt
```

**Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_rag.py -v`
Expected: FAIL — module not found.

**Step 3: Implement retrieval_chain.py**

Create `src/rag/__init__.py` (empty) and `src/rag/retrieval_chain.py`:

```python
"""retrieval_chain.py — RAG pipeline over Shark Tank pitch data.

Retrieves relevant pitch segments from Pinecone, augments with
structured data from PostgreSQL, and synthesizes analysis via Claude.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

SYSTEM_PROMPT = """You are a Shark Tank market analyst with deep expertise in startup evaluation,
deal negotiation patterns, and investor psychology. You have access to a comprehensive
database of every Shark Tank pitch, including transcripts, deal outcomes, and market data.

When answering questions:
- Ground your analysis in specific data from retrieved pitches
- Cite episode numbers and company names
- Provide quantitative evidence (deal amounts, success rates, margins)
- Identify patterns across multiple pitches when relevant
- Give actionable insights for founders or investors

Format your response with clear sections and bullet points when appropriate."""


@dataclass
class SourceCitation:
    """A citation reference from the RAG response."""
    episode: str
    company_name: str
    segment_type: str
    text_snippet: str


@dataclass
class AnalysisResult:
    """Result from the RAG analysis pipeline."""
    answer: str
    sources: list[SourceCitation]
    query: str


def build_analysis_prompt(query: str, context_docs: list[dict]) -> str:
    """Build the full prompt with system prompt, context, and query."""
    context_parts: list[str] = []
    for doc in context_docs:
        episode = doc.get("episode", "Unknown")
        company = doc.get("company_name", "Unknown")
        segment = doc.get("segment_type", "")
        text = doc.get("text", "")
        context_parts.append(
            f"[{episode} - {company} ({segment})]\n{text}"
        )

    context_str = "\n\n".join(context_parts) if context_parts else "No relevant context found."

    return f"""{SYSTEM_PROMPT}

## Retrieved Context

{context_str}

## User Query

{query}

## Instructions

Answer the user's query using the retrieved context above. Cite specific episodes and companies.
If the context doesn't contain relevant information, say so and provide general insights."""


def retrieve_context(
    query: str,
    top_k: int = 5,
    filters: Optional[dict] = None,
) -> list[dict]:
    """Retrieve relevant pitch segments from Pinecone.

    Requires OPENAI_API_KEY and PINECONE_API_KEY in environment.
    """
    from openai import OpenAI
    from pinecone import Pinecone

    # Embed query
    openai_client = OpenAI()
    response = openai_client.embeddings.create(
        model="text-embedding-3-large",
        input=[query],
    )
    query_embedding = response.data[0].embedding

    # Search Pinecone
    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    index_name = os.environ.get("PINECONE_INDEX_NAME", "shark-tank-engine")
    index = pc.Index(index_name)

    query_params = {
        "vector": query_embedding,
        "top_k": top_k,
        "include_metadata": True,
    }
    if filters:
        query_params["filter"] = filters

    results = index.query(**query_params)

    context_docs = []
    for match in results.get("matches", []):
        metadata = match.get("metadata", {})
        context_docs.append({
            "text": metadata.get("text", ""),
            "episode": metadata.get("episode", ""),
            "company_name": metadata.get("company_name", ""),
            "segment_type": metadata.get("segment_type", ""),
            "score": match.get("score", 0.0),
        })

    return context_docs


def analyze(
    query: str,
    top_k: int = 5,
    filters: Optional[dict] = None,
) -> AnalysisResult:
    """Full RAG pipeline: retrieve -> prompt -> synthesize.

    Requires ANTHROPIC_API_KEY, OPENAI_API_KEY, and PINECONE_API_KEY.
    """
    import anthropic

    # Retrieve context
    context_docs = retrieve_context(query, top_k=top_k, filters=filters)

    # Build prompt
    prompt = build_analysis_prompt(query, context_docs)

    # Call Claude
    client = anthropic.Anthropic()
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )

    answer = message.content[0].text

    # Build citations
    sources = [
        SourceCitation(
            episode=doc.get("episode", ""),
            company_name=doc.get("company_name", ""),
            segment_type=doc.get("segment_type", ""),
            text_snippet=doc.get("text", "")[:200],
        )
        for doc in context_docs
    ]

    return AnalysisResult(answer=answer, sources=sources, query=query)
```

**Step 4: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_rag.py -v`
Expected: All PASS (only prompt building is tested — API calls require keys).

**Step 5: Commit**

```bash
git add src/rag/__init__.py src/rag/retrieval_chain.py tests/test_rag.py
git commit -m "feat: add RAG retrieval chain with Claude synthesis

Retrieves from Pinecone, builds grounded prompt with shark analyst
persona, synthesizes via Claude API with source citations."
```

---

## Task 11: FastAPI Endpoints

Build `src/api/main.py` and `src/api/schemas.py`.

**Files:**
- Create: `src/api/__init__.py`
- Create: `src/api/schemas.py`
- Create: `src/api/main.py`
- Create: `tests/test_api.py`

**Step 1: Write failing tests**

Create `tests/test_api.py`:

```python
"""Tests for FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from src.api.main import app
    return TestClient(app)


class TestHealthEndpoint:
    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestPredictEndpoint:
    def test_predict_returns_200(self, client):
        payload = {
            "ask_amount": 200000,
            "equity_offered_pct": 10.0,
            "revenue_trailing_12m": 500000,
            "industry": "Food",
            "founder_count": 1,
        }
        response = client.post("/predict", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "deal_probability" in data
        assert "deal_score" in data

    def test_predict_validates_input(self, client):
        response = client.post("/predict", json={})
        assert response.status_code == 422
```

**Step 2: Run tests to verify they fail**

Run: `python3 -m pytest tests/test_api.py -v`
Expected: FAIL — module not found.

**Step 3: Create schemas.py**

Create `src/api/__init__.py` (empty) and `src/api/schemas.py`:

```python
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
```

**Step 4: Create main.py**

Create `src/api/main.py`:

```python
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
    XGBClassifier,
)

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
```

**Step 5: Run tests to verify they pass**

Run: `python3 -m pytest tests/test_api.py -v`
Expected: All PASS.

**Step 6: Commit**

```bash
git add src/api/__init__.py src/api/schemas.py src/api/main.py tests/test_api.py
git commit -m "feat: add FastAPI endpoints for predict, analyze, and comps

/predict: deal probability from features with heuristic fallback.
/analyze: RAG-powered analysis via Claude (requires API keys).
/comps: semantic search for comparable past pitches."
```

---

## Task 12: Integration Smoke Test

Run the full parser against real data and verify the API starts.

**Files:** None new — validation only.

**Step 1: Run all tests**

Run: `python3 -m pytest tests/ -v`
Expected: All PASS.

**Step 2: Smoke test parser on real S01E01**

Run: `python3 -m src.ingestion.srt_parser "transcripts/transcripts season 1/Shark.Tank.S01E01_with_speakers.srt" 2>&1 | python3 -m json.tool | head -80`
Expected: JSON with multiple pitches, each with segments and signals.

**Step 3: Smoke test parser on S03E01 (colon format)**

Run: `python3 -m src.ingestion.srt_parser "transcripts/transcripts season 3/Shark.Tank.S03E01.srt" 2>&1 | python3 -m json.tool | head -80`
Expected: Same structure, different data.

**Step 4: Start the API server**

Run: `python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 &`
Then: `curl -X POST http://localhost:8000/predict -H 'Content-Type: application/json' -d '{"ask_amount": 200000, "equity_offered_pct": 10, "revenue_trailing_12m": 500000}'`
Expected: JSON response with deal_probability and deal_score.

**Step 5: Stop the server and commit final state**

```bash
kill %1
git add -A
git status
git commit -m "feat: complete Phase 1 pipeline - SRT parser through FastAPI

Phase 1 includes: SRT parser (multi-pitch, role classification),
Kaggle loader, embedding pipeline, XGBoost predictor,
RAG retrieval chain, and FastAPI API endpoints."
```

---

## Summary

| Task | Component | Tests |
|------|-----------|-------|
| 1 | Project setup & dependencies | conftest fixtures |
| 2 | SRT parsing + speaker extraction | TestParseSrt, TestParseSrtFile |
| 3 | Pitch splitting | TestSplitIntoPitches |
| 4 | Role classification | TestClassifySpeakers |
| 5 | Segmentation + signals | TestSegmentPitch, TestExtractSignals |
| 6 | Public API + CLI | TestParseEpisode, TestParseAllEpisodes |
| 7 | Kaggle loader | TestLoadKaggleCsv, TestCleanAndEngineer, TestLinkSrtPitches |
| 8 | Embedding pipeline | TestChunkPitch |
| 9 | Deal predictor | TestPrepareFeatures, TestTrainAndPredict |
| 10 | RAG chain | TestBuildPrompt |
| 11 | FastAPI endpoints | TestHealthEndpoint, TestPredictEndpoint |
| 12 | Integration smoke test | Manual verification |
