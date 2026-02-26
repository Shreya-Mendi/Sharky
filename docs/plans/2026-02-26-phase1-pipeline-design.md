# Shark Tank AI Engine - Phase 1 Pipeline Design

**Date:** 2026-02-26
**Status:** Approved
**Scope:** Full Phase 1 — SRT Parser through FastAPI endpoints

## Architecture Decision

**Approach:** Monolithic Python pipeline with clean module separation.
**Storage:** PostgreSQL (structured data) + Pinecone (vector embeddings). Neo4j deferred to Phase 2.

Build order: `srt_parser` -> `kaggle_loader` -> `embed_pipeline` -> `deal_predictor` -> `retrieval_chain` -> `api`

## Intelligence Layers

The system delivers three layers of analysis:

| Layer | Question | Example |
|---|---|---|
| 1st order | What happened? | "Pitch X asked $500K for 10%, got deal from Cuban at 20%" |
| 2nd order | What patterns emerge? | "Sharks who express skepticism about valuation but ask follow-up questions close 73% of the time" |
| 3rd order | What does this predict? | "A food-tech startup with $800K revenue asking $1M should pitch to Lori, avoid Kevin, and expect a 3x equity counter" |

## Critical Design Decisions (from brainstorming)

1. **Multiple pitches per episode** — SRT files contain 3-4 pitches each. Parser must split them using narrator boundary detection.
2. **Anonymous speaker labels** — SRT files use `Speaker_N` not real names. Parser classifies roles (narrator/shark/entrepreneur) with confidence scores. Specific shark identity comes from Kaggle data.
3. **Kaggle-SRT linking** — matched by season + episode number, validated by company/entrepreneur name.
4. **Neo4j deferred** — knowledge graph adds value but isn't critical for Phase 1 RAG + prediction. Reduces sync complexity.

---

## Section 1: SRT Parser (`src/ingestion/srt_parser.py`)

### Input

SRT files from `transcripts/` directory across 13+ seasons. Two speaker label formats:
- `[Speaker_N] text` (Seasons 1, 2, 5+)
- `Speaker_N: text` (Seasons 3, 4)

Also available: `.txt` files (same content, no timestamps). SRT files are the primary source.

### Processing Pipeline

```
SRT File -> Parse blocks -> Detect format -> Extract Speaker_N labels
  -> Split into pitches (narrator boundary detection)
  -> Per pitch:
      -> Identify narrator speaker (most lines in intro/outro)
      -> Identify entrepreneur speaker ("My name is...", dominates early lines)
      -> Remaining speakers = sharks
      -> Assign confidence scores to each classification
      -> Segment using roles + patterns
      -> Extract signals (only from high-confidence lines)
  -> Output: list[ParsedPitch]
```

### Pitch Boundary Detection

Narrator lines matching these patterns mark pitch boundaries:
- `"First into the shark tank is..."`
- `"Next up is..."`
- `"Next into the shark tank is..."`
- `"Our next entrepreneur..."`

### Role Classification

| Role | Detection Heuristic |
|---|---|
| Narrator | Speaker with most lines in intro/outro segments; delivers transition lines |
| Entrepreneur | Speaker who says "My name is...", "I'm asking for $X", dominates early pitch lines |
| Shark | All other speakers during pitch segments |

Each classification gets a confidence score (0-1). Lines below 0.6 confidence are excluded from signal extraction.

### Segmentation (per-pitch, role-based)

| Segment | Rule |
|---|---|
| `founder_pitch` | Entrepreneur lines before first shark question |
| `product_demo` | Entrepreneur lines with demo keywords (demo, watch, show, taste, try, sample) |
| `shark_questions` | Shark lines containing `?` |
| `objections` | Lines matching objection patterns ("I'm out", "too risky", "overvalued", etc.) |
| `negotiation` | Lines matching offer/counter patterns ("I'll offer", "would you take", equity %) |
| `closing_reason` | Final lines after last objection/negotiation |

### Extracted Signals (per-pitch)

| Signal | Method |
|---|---|
| `revenue_mentioned` | Regex `$` amount extraction from entrepreneur lines |
| `market_size_claim` | Market size keyword + largest `$` amount in context |
| `founder_confidence` | VADER sentiment on entrepreneur lines (compound score) |
| `shark_enthusiasm_max` | Highest VADER compound score across shark speakers |
| `objection_count` | Count of objection-matched blocks |
| `negotiation_rounds` | Count of negotiation-matched blocks |

### Output Schema

```python
@dataclass
class ParsedPitch:
    episode: str           # "S01E01"
    pitch_index: int       # 0-based within episode
    entrepreneur_name: str # extracted from "My name is..." or narrator intro
    segments: PitchSegments
    signals: ExtractedSignals
    speaker_map: dict[str, str]  # {"Speaker_3": "entrepreneur", "Speaker_5": "shark", ...}
    confidence_scores: dict[str, float]  # per-speaker confidence
    raw_blocks: list[SubtitleBlock]
```

---

## Section 2: Kaggle Loader (`src/ingestion/kaggle_loader.py`)

### Input
`shark_tank_us_dataset.csv` from Kaggle.

### Processing
- Load CSV with pandas, validate expected columns
- Clean: handle missing values, normalize currency strings, parse season/episode numbers
- Feature engineering:
  - `implied_valuation = ask_amount / equity_offered_pct`
  - One-hot encode `industry_category`
  - Boolean flags: `has_patent`, `multiple_sharks`
- Link to SRT pitches by season + episode number

### Output Schema

```python
@dataclass
class DealRecord:
    season: int
    episode: int
    company_name: str
    industry: str
    ask_amount: float
    equity_offered_pct: float
    implied_valuation: float
    revenue_trailing_12m: float
    gross_margin_pct: float
    years_in_business: int
    founder_count: int
    has_patent: bool
    deal_closed: bool
    final_deal_amount: float | None
    final_equity_pct: float | None
    shark_ids: list[str]
    # SRT-derived (populated after linking)
    pitch_sentiment_score: float | None
    shark_enthusiasm_max: float | None
    objection_count: int | None
    negotiation_rounds: int | None
```

---

## Section 3: Embedding Pipeline (`src/embeddings/embed_pipeline.py`)

### Chunking Strategy
- Each pitch is chunked by segment (founder_pitch, shark_questions, objections, negotiation, closing_reason)
- Each segment = one chunk (~200-500 tokens)
- Segments exceeding 8000 tokens are split with 200-token overlap

### Embedding
- Model: OpenAI `text-embedding-3-large` (3072 dimensions)
- Batch processing with rate limiting

### Storage
- Pinecone upsert with metadata:
  ```json
  {
    "episode": "S01E01",
    "pitch_index": 0,
    "company_name": "Mr. Todd's Pies",
    "segment_type": "founder_pitch",
    "industry": "food",
    "season": 1
  }
  ```
- Metadata filtering enabled on: `season`, `segment_type`, `industry`

---

## Section 4: Deal Predictor (`src/models/deal_predictor.py`)

### Features
**Kaggle-derived:**
- ask_amount, equity_offered_pct, implied_valuation
- revenue_trailing_12m, gross_margin_pct
- years_in_business, industry_category (one-hot)
- founder_count, has_patent

**SRT-derived:**
- pitch_sentiment_score, shark_enthusiasm_max
- objection_count, negotiation_rounds

### Models
- **Primary:** XGBoost classifier for `deal_closed` (binary)
- **Secondary:** XGBoost regressors for `final_deal_amount` and `final_equity_pct`

### Training
- Stratified k-fold cross-validation (k=5)
- SHAP explanations for feature importance
- Evaluation: AUC-ROC, precision, recall, F1

---

## Section 5: RAG Pipeline (`src/rag/retrieval_chain.py`)

### Query Flow
1. User query -> embed with OpenAI `text-embedding-3-large`
2. Pinecone similarity search -> top-k (default 5) relevant pitch segments
3. PostgreSQL lookup -> structured deal facts for matched pitches
4. Construct prompt: shark analyst system prompt + retrieved context + user query
5. Claude API -> synthesized response with source citations

### Intelligence Layer Support
- **1st order:** Direct PostgreSQL fact retrieval
- **2nd order:** Pattern queries across multiple retrieved pitches
- **3rd order:** XGBoost prediction + retrieved context + LLM reasoning

### LangChain Integration
- `RetrievalQA` chain with Pinecone retriever
- Custom prompt template with shark analyst persona
- Claude API as LLM backend

---

## Section 6: FastAPI Endpoints (`src/api/main.py`)

### Endpoints

| Endpoint | Method | Input | Output |
|---|---|---|---|
| `/analyze` | POST | `{query: str}` | RAG-generated analysis with citations |
| `/predict` | POST | `{ask_amount, equity, revenue, industry, ...}` | `{deal_probability, deal_score, risk_factors, strengths}` |
| `/comps` | POST | `{company_name or industry}` | Top-k similar past pitches with outcomes |

### Response Schemas

```python
class AnalyzeResponse(BaseModel):
    answer: str
    sources: list[SourceCitation]
    confidence: float

class PredictResponse(BaseModel):
    deal_probability: float
    deal_score: int  # 1-10
    strengths: list[str]
    risks: list[str]
    shark_match: dict[str, float]  # shark_name -> affinity score
    comps: list[CompDeal]

class CompsResponse(BaseModel):
    matches: list[CompDeal]
    # CompDeal: company, season, episode, ask, deal, outcome, similarity_score
```

---

## Directory Structure (Phase 1)

```
sharky/
    docs/plans/                     <- This design doc
    data/
        raw/
            kaggle/                 <- shark_tank_us_dataset.csv
            srt/                    <- symlink or copy from transcripts/
        processed/                  <- cleaned outputs
    transcripts/                    <- source SRT/TXT files (13 seasons)
    src/
        __init__.py
        ingestion/
            __init__.py
            srt_parser.py           <- Rewrite (Section 1)
            kaggle_loader.py        <- New (Section 2)
        embeddings/
            __init__.py
            embed_pipeline.py       <- New (Section 3)
        models/
            __init__.py
            deal_predictor.py       <- New (Section 4)
        rag/
            __init__.py
            retrieval_chain.py      <- New (Section 5)
        api/
            __init__.py
            main.py                 <- New (Section 6)
            schemas.py              <- New (Section 6)
    tests/
        test_srt_parser.py
        test_kaggle_loader.py
        test_predictor.py
    requirements.txt
    .env.example
```

## Dependencies

```
# Core
pandas
numpy
scikit-learn
xgboost
shap

# NLP
spacy
vaderSentiment

# Embeddings & Vector Store
openai
pinecone-client

# RAG
langchain
langchain-anthropic
langchain-openai
langchain-pinecone

# API
fastapi
uvicorn
pydantic

# Database
sqlalchemy
psycopg2-binary
alembic

# Dev
pytest
httpx
python-dotenv
```
