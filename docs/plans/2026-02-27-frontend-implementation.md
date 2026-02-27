# Shark Tank AI Engine — Frontend + Backend Wiring Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a professional 4-page Next.js frontend and wire the FastAPI backend to serve real parsed SRT data, all fully functional end-to-end.

**Architecture:** Next.js 14 App Router frontend (port 3000) consuming a FastAPI backend (port 8000). Backend parses 292 real SRT transcripts at startup, caches as JSON, and serves via new `/data/*` endpoints. Frontend proxies API calls through Next.js rewrites.

**Tech Stack:** Next.js 14 (TypeScript), Tailwind CSS v3, Framer Motion, Recharts, Lucide React icons. Backend: FastAPI, Python 3.11+, existing SRT parser + predictor.

**Design Doc:** `docs/plans/2026-02-26-frontend-design.md`

---

## Task 1: Backend — Parse & Cache Real SRT Data

Build a data pipeline that parses all 292 SRT files into JSON cache on startup.

**Files:**
- Create: `src/data/cache.py`
- Create: `src/data/__init__.py`
- Create: `data/processed/.gitkeep`

**Step 1: Create the data cache module**

Create `src/data/__init__.py` (empty) and `src/data/cache.py`:

```python
"""cache.py — Parse all SRT transcripts and cache as JSON.

Parses once, serves from memory. Rebuild cache with rebuild_cache().
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from src.ingestion.srt_parser import parse_episode, parse_all_episodes, ParsedPitch

logger = logging.getLogger(__name__)

TRANSCRIPT_DIR = Path("transcripts")
CACHE_FILE = Path("data/processed/all_pitches.json")

# In-memory cache
_cached_pitches: list[dict] | None = None
_cached_stats: dict | None = None


def rebuild_cache(transcript_dir: Path | None = None) -> list[dict]:
    """Parse all SRT files and write JSON cache."""
    srt_dir = transcript_dir or TRANSCRIPT_DIR
    logger.info("Parsing all SRT files from %s...", srt_dir)

    pitches = parse_all_episodes(srt_dir)
    logger.info("Parsed %d pitches from SRT files", len(pitches))

    pitch_dicts = [p.to_dict() for p in pitches]

    # Write cache file
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
            episodes[ep] = {
                "episode": ep,
                "pitch_count": 0,
                "deal_count": 0,
                "pitches": [],
            }
        episodes[ep]["pitches"].append(pitch)
        episodes[ep]["pitch_count"] += 1

    return sorted(episodes.values(), key=lambda e: e["episode"])


def get_episode(code: str) -> dict | None:
    """Get a single episode by code (e.g., 'S01E01')."""
    episodes = get_episodes()
    for ep in episodes:
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

    total_pitches = len(pitches)
    total_episodes = len(episodes)

    # Revenue stats
    revenues = [p["signals"]["revenue_mentioned"] for p in pitches if p["signals"]["revenue_mentioned"] > 0]
    avg_revenue = sum(revenues) / len(revenues) if revenues else 0

    # Objection stats
    objections = [p["signals"]["objection_count"] for p in pitches]
    avg_objections = sum(objections) / len(objections) if objections else 0

    # Sentiment stats
    sentiments = [p["signals"]["founder_confidence"] for p in pitches]
    avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0

    # By-season breakdown
    season_data: dict[str, dict] = {}
    for pitch in pitches:
        season = pitch["episode"][:3]  # "S01"
        if season not in season_data:
            season_data[season] = {"season": season, "pitch_count": 0, "episodes": set()}
        season_data[season]["pitch_count"] += 1
        season_data[season]["episodes"].add(pitch["episode"])

    seasons = []
    for s in sorted(season_data.values(), key=lambda x: x["season"]):
        seasons.append({
            "season": s["season"],
            "pitch_count": s["pitch_count"],
            "episode_count": len(s["episodes"]),
        })

    _cached_stats = {
        "total_pitches": total_pitches,
        "total_episodes": total_episodes,
        "total_seasons": len(seasons),
        "avg_revenue_mentioned": round(avg_revenue, 2),
        "avg_objection_count": round(avg_objections, 2),
        "avg_founder_confidence": round(avg_sentiment, 4),
        "seasons": seasons,
    }

    return _cached_stats
```

**Step 2: Run to verify it works**

Run: `python3 -c "from src.data.cache import rebuild_cache; pitches = rebuild_cache(); print(f'Parsed {len(pitches)} pitches')"`
Expected: Parses all SRT files, prints count, creates `data/processed/all_pitches.json`.

**Step 3: Commit**

```bash
git add src/data/__init__.py src/data/cache.py data/processed/.gitkeep
git commit -m "feat: add SRT data cache layer for parsed pitch data"
```

---

## Task 2: Backend — New Data Endpoints

Add `/data/episodes`, `/data/episodes/{code}`, and `/data/stats` endpoints.

**Files:**
- Modify: `src/api/main.py`
- Modify: `src/api/schemas.py`
- Modify: `tests/test_api.py`

**Step 1: Add new schemas to `src/api/schemas.py`**

Append to existing file:

```python
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
```

**Step 2: Add new endpoints to `src/api/main.py`**

Add imports and endpoints:

```python
from src.data.cache import get_all_pitches, get_episodes, get_episode, get_stats

from src.api.schemas import (
    # ... existing imports ...
    EpisodeSummary,
    EpisodeDetail,
    StatsResponse,
)


@app.get("/data/episodes")
def list_episodes():
    """List all parsed episodes with pitch counts."""
    episodes = get_episodes()
    return episodes


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
    return {
        "total": len(pitches),
        "pitches": pitches[offset:offset + limit],
    }
```

**Step 3: Add CORS middleware to `src/api/main.py`**

Add near the top after `app = FastAPI(...)`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Step 4: Add tests to `tests/test_api.py`**

```python
class TestDataEndpoints:
    def test_stats(self, client):
        response = client.get("/data/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_pitches" in data
        assert "total_episodes" in data

    def test_episodes_list(self, client):
        response = client.get("/data/episodes")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_pitches_paginated(self, client):
        response = client.get("/data/pitches?limit=5&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "pitches" in data
```

**Step 5: Run tests**

Run: `python3 -m pytest tests/test_api.py -v`
Expected: All tests pass (3 existing + 3 new).

**Step 6: Commit**

```bash
git add src/api/main.py src/api/schemas.py tests/test_api.py
git commit -m "feat: add data endpoints for episodes, stats, and pitches"
```

---

## Task 3: Backend — Streaming Analysis Endpoint

Add SSE streaming for the SharkBot chat experience.

**Files:**
- Modify: `src/api/main.py`
- Modify: `src/rag/retrieval_chain.py`

**Step 1: Add streaming analyze function to `src/rag/retrieval_chain.py`**

```python
def analyze_stream(
    query: str,
    top_k: int = 5,
    filters: Optional[dict] = None,
):
    """Streaming RAG pipeline. Yields chunks of Claude's response.

    Requires ANTHROPIC_API_KEY, OPENAI_API_KEY, and PINECONE_API_KEY.
    """
    import anthropic

    context_docs = retrieve_context(query, top_k=top_k, filters=filters)
    prompt = build_analysis_prompt(query, context_docs)

    client = anthropic.Anthropic()

    # Build source citations for metadata
    sources = [
        {
            "episode": doc.get("episode", ""),
            "company_name": doc.get("company_name", ""),
            "segment_type": doc.get("segment_type", ""),
            "text_snippet": doc.get("text", "")[:200],
        }
        for doc in context_docs
    ]

    # Yield sources first as a metadata event
    yield {"type": "sources", "data": sources}

    # Stream Claude response
    with client.messages.stream(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            yield {"type": "text", "data": text}
```

**Step 2: Add SSE endpoint to `src/api/main.py`**

```python
from fastapi.responses import StreamingResponse
import json as json_module


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
```

**Step 3: Commit**

```bash
git add src/api/main.py src/rag/retrieval_chain.py
git commit -m "feat: add SSE streaming endpoint for SharkBot chat"
```

---

## Task 4: Frontend — Scaffold Next.js Project

Initialize the Next.js app with Tailwind, TypeScript, and project structure.

**Files:**
- Create: `frontend/` directory with Next.js scaffold
- Modify: `.claude/launch.json`

**Step 1: Scaffold Next.js**

Run:
```bash
cd /Users/shreyamendi/sharky
npx create-next-app@latest frontend --typescript --tailwind --eslint --app --src-dir --no-import-alias
```

Accept defaults when prompted.

**Step 2: Install dependencies**

Run:
```bash
cd /Users/shreyamendi/sharky/frontend
npm install framer-motion recharts lucide-react
```

**Step 3: Configure API proxy in `frontend/next.config.ts`**

Replace contents:

```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/:path*",
      },
    ];
  },
};

export default nextConfig;
```

**Step 4: Update launch.json**

Replace `.claude/launch.json`:

```json
{
  "version": "0.0.1",
  "configurations": [
    {
      "name": "shark-tank-api",
      "runtimeExecutable": "python3",
      "runtimeArgs": ["-m", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"],
      "port": 8000
    },
    {
      "name": "shark-tank-frontend",
      "runtimeExecutable": "npm",
      "runtimeArgs": ["run", "dev", "--prefix", "frontend"],
      "port": 3000
    }
  ]
}
```

**Step 5: Set up global styles in `frontend/src/app/globals.css`**

Replace contents:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --bg-primary: #0a0a0f;
  --bg-surface: rgba(255, 255, 255, 0.05);
  --accent-blue: #3b82f6;
  --accent-amber: #f59e0b;
  --accent-emerald: #10b981;
  --accent-rose: #f43f5e;
}

body {
  background-color: var(--bg-primary);
  color: #ffffff;
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
}

/* Glassmorphism utility */
.glass {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
}

.glass-hover:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.2);
}

/* Glow effect for CTAs */
.glow-blue {
  box-shadow: 0 0 20px rgba(59, 130, 246, 0.3);
}

.glow-amber {
  box-shadow: 0 0 20px rgba(245, 158, 11, 0.3);
}
```

**Step 6: Create API client in `frontend/src/lib/api.ts`**

```typescript
const API_BASE = "/api";

export async function fetchStats() {
  const res = await fetch(`${API_BASE}/data/stats`);
  if (!res.ok) throw new Error("Failed to fetch stats");
  return res.json();
}

export async function fetchEpisodes() {
  const res = await fetch(`${API_BASE}/data/episodes`);
  if (!res.ok) throw new Error("Failed to fetch episodes");
  return res.json();
}

export async function fetchEpisode(code: string) {
  const res = await fetch(`${API_BASE}/data/episodes/${code}`);
  if (!res.ok) throw new Error(`Failed to fetch episode ${code}`);
  return res.json();
}

export async function fetchPitches(limit = 50, offset = 0) {
  const res = await fetch(`${API_BASE}/data/pitches?limit=${limit}&offset=${offset}`);
  if (!res.ok) throw new Error("Failed to fetch pitches");
  return res.json();
}

export interface PredictRequest {
  ask_amount: number;
  equity_offered_pct: number;
  revenue_trailing_12m?: number;
  industry?: string;
  founder_count?: number;
  pitch_sentiment_score?: number;
  shark_enthusiasm_max?: number;
  objection_count?: number;
  negotiation_rounds?: number;
}

export interface PredictResponse {
  deal_probability: number;
  deal_score: number;
  strengths: string[];
  risks: string[];
}

export async function predictDeal(data: PredictRequest): Promise<PredictResponse> {
  const res = await fetch(`${API_BASE}/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Prediction failed");
  return res.json();
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  sources?: Array<{
    episode: string;
    company_name: string;
    segment_type: string;
    text_snippet: string;
  }>;
}

export async function* streamAnalysis(query: string, topK = 5) {
  const res = await fetch(`${API_BASE}/analyze/stream?query=${encodeURIComponent(query)}&top_k=${topK}`);
  if (!res.ok) throw new Error("Analysis failed");

  const reader = res.body?.getReader();
  const decoder = new TextDecoder();
  if (!reader) throw new Error("No reader");

  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        const data = JSON.parse(line.slice(6));
        yield data;
      }
    }
  }
}
```

**Step 7: Create shared components directory structure**

Run:
```bash
mkdir -p frontend/src/components/ui
mkdir -p frontend/src/components/layout
mkdir -p frontend/src/hooks
```

**Step 8: Create layout component `frontend/src/components/layout/Navbar.tsx`**

```tsx
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { BarChart3, Bot, Home, Zap } from "lucide-react";

const links = [
  { href: "/", label: "Home", icon: Home },
  { href: "/simulator", label: "Simulator", icon: Zap },
  { href: "/hub", label: "Intelligence Hub", icon: BarChart3 },
  { href: "/chat", label: "SharkBot", icon: Bot },
];

export default function Navbar() {
  const pathname = usePathname();

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 glass border-b border-white/10">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          <span className="text-xl font-bold bg-gradient-to-r from-blue-400 to-blue-600 bg-clip-text text-transparent">
            🦈 SharkTank AI
          </span>
        </Link>

        <div className="hidden md:flex items-center gap-1">
          {links.map(({ href, label, icon: Icon }) => {
            const isActive = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                className={`relative px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2 ${
                  isActive ? "text-white" : "text-slate-400 hover:text-white"
                }`}
              >
                <Icon size={16} />
                {label}
                {isActive && (
                  <motion.div
                    layoutId="navbar-indicator"
                    className="absolute inset-0 bg-white/10 rounded-lg"
                    transition={{ type: "spring", duration: 0.5 }}
                  />
                )}
              </Link>
            );
          })}
        </div>

        <Link
          href="/simulator"
          className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors glow-blue"
        >
          Try Simulator
        </Link>
      </div>
    </nav>
  );
}
```

**Step 9: Update root layout `frontend/src/app/layout.tsx`**

```tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/layout/Navbar";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "SharkTank AI Engine",
  description: "AI-powered Shark Tank pitch analysis, deal prediction, and market intelligence.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} antialiased`}>
        <Navbar />
        <main className="pt-16">{children}</main>
      </body>
    </html>
  );
}
```

**Step 10: Verify it runs**

Run: Start both servers via launch.json and verify Next.js loads at localhost:3000.

**Step 11: Commit**

```bash
cd /Users/shreyamendi/sharky
git add frontend/ .claude/launch.json
git commit -m "feat: scaffold Next.js frontend with Tailwind, Framer Motion, API client"
```

---

## Task 5: Frontend — Landing Page

Build the hero page with animated counters, intelligence cards, and live demo strip.

**Files:**
- Create: `frontend/src/app/page.tsx`
- Create: `frontend/src/components/ui/AnimatedCounter.tsx`
- Create: `frontend/src/components/ui/DealScoreGauge.tsx`

**Step 1: Create AnimatedCounter component**

Create `frontend/src/components/ui/AnimatedCounter.tsx`:

```tsx
"use client";

import { useEffect, useRef, useState } from "react";
import { motion, useInView } from "framer-motion";

interface AnimatedCounterProps {
  target: number;
  prefix?: string;
  suffix?: string;
  duration?: number;
}

export default function AnimatedCounter({
  target,
  prefix = "",
  suffix = "",
  duration = 2,
}: AnimatedCounterProps) {
  const [count, setCount] = useState(0);
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true });

  useEffect(() => {
    if (!isInView) return;

    let start = 0;
    const step = target / (duration * 60);
    const timer = setInterval(() => {
      start += step;
      if (start >= target) {
        setCount(target);
        clearInterval(timer);
      } else {
        setCount(Math.floor(start));
      }
    }, 1000 / 60);

    return () => clearInterval(timer);
  }, [isInView, target, duration]);

  return (
    <motion.span
      ref={ref}
      initial={{ opacity: 0, y: 20 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.6 }}
      className="tabular-nums"
    >
      {prefix}{count.toLocaleString()}{suffix}
    </motion.span>
  );
}
```

**Step 2: Create DealScoreGauge component**

Create `frontend/src/components/ui/DealScoreGauge.tsx`:

```tsx
"use client";

import { motion } from "framer-motion";

interface DealScoreGaugeProps {
  score: number; // 1-10
  size?: number;
  animated?: boolean;
}

export default function DealScoreGauge({ score, size = 120, animated = true }: DealScoreGaugeProps) {
  const percentage = score / 10;
  const circumference = 2 * Math.PI * 45;
  const strokeDashoffset = circumference * (1 - percentage);

  const getColor = () => {
    if (score <= 3) return "#f43f5e";
    if (score <= 6) return "#f59e0b";
    return "#10b981";
  };

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg viewBox="0 0 100 100" className="transform -rotate-90" style={{ width: size, height: size }}>
        <circle cx="50" cy="50" r="45" fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="8" />
        <motion.circle
          cx="50"
          cy="50"
          r="45"
          fill="none"
          stroke={getColor()}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={animated ? { strokeDashoffset: circumference } : { strokeDashoffset }}
          animate={{ strokeDashoffset }}
          transition={{ duration: 1.5, ease: "easeOut", delay: 0.5 }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <motion.span
          className="text-2xl font-bold"
          style={{ color: getColor() }}
          initial={animated ? { opacity: 0 } : { opacity: 1 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1 }}
        >
          {score}
        </motion.span>
        <span className="text-xs text-slate-400">/10</span>
      </div>
    </div>
  );
}
```

**Step 3: Build the landing page**

Replace `frontend/src/app/page.tsx`:

```tsx
"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowRight, BarChart3, Brain, TrendingUp } from "lucide-react";
import AnimatedCounter from "@/components/ui/AnimatedCounter";
import DealScoreGauge from "@/components/ui/DealScoreGauge";

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.15, duration: 0.6 },
  }),
};

const intelligenceLayers = [
  {
    icon: BarChart3,
    order: "1st Order",
    title: "What Happened",
    example: '"Pitch X asked $500K for 10%, got deal from Cuban at 20%"',
    color: "text-blue-400",
    borderColor: "border-blue-500/30",
  },
  {
    icon: Brain,
    order: "2nd Order",
    title: "What Patterns Emerge",
    example: '"Sharks who express skepticism but ask follow-up questions close 73% of the time"',
    color: "text-amber-400",
    borderColor: "border-amber-500/30",
  },
  {
    icon: TrendingUp,
    order: "3rd Order",
    title: "What This Predicts",
    example: '"A food-tech startup with $800K revenue should pitch to Lori and expect a 3x equity counter"',
    color: "text-emerald-400",
    borderColor: "border-emerald-500/30",
  },
];

export default function HomePage() {
  const [demoAsk, setDemoAsk] = useState(250000);
  const [demoRevenue, setDemoRevenue] = useState(500000);

  const demoScore = Math.max(1, Math.min(10, Math.round(
    (Math.min(demoRevenue / 1_000_000, 1) * 4 +
    Math.max(0, 1 - (demoAsk / 0.1) / 10_000_000) * 3 +
    0.5 * 3)
  )));

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="min-h-screen flex flex-col items-center justify-center px-6 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-blue-950/20 via-transparent to-transparent" />

        <motion.div
          className="text-center max-w-4xl relative z-10"
          initial="hidden"
          animate="visible"
        >
          <motion.h1
            variants={fadeUp}
            custom={0}
            className="text-5xl md:text-7xl font-bold mb-6 bg-gradient-to-r from-white via-blue-100 to-blue-300 bg-clip-text text-transparent"
          >
            Know Your Odds Before You Enter the Tank
          </motion.h1>
          <motion.p
            variants={fadeUp}
            custom={1}
            className="text-xl text-slate-400 mb-10"
          >
            AI-powered pitch analysis across 15 seasons of Shark Tank data
          </motion.p>

          <motion.div variants={fadeUp} custom={2} className="flex gap-4 justify-center mb-16">
            <Link
              href="/simulator"
              className="bg-blue-600 hover:bg-blue-500 text-white px-8 py-3 rounded-xl text-lg font-semibold transition-all glow-blue flex items-center gap-2"
            >
              Simulate Your Pitch <ArrowRight size={20} />
            </Link>
            <Link
              href="/hub"
              className="border border-white/20 hover:border-white/40 text-white px-8 py-3 rounded-xl text-lg font-semibold transition-all"
            >
              Explore the Data
            </Link>
          </motion.div>

          {/* Animated Stats */}
          <motion.div variants={fadeUp} custom={3} className="flex gap-12 justify-center text-center">
            {[
              { target: 292, suffix: "", label: "Episodes Analyzed" },
              { target: 1200, suffix: "+", label: "Pitches Parsed" },
              { target: 2, prefix: "$", suffix: ".4B", label: "In Deals Tracked" },
            ].map(({ target, prefix, suffix, label }) => (
              <div key={label} className="flex flex-col">
                <span className="text-3xl font-bold text-white">
                  <AnimatedCounter target={target} prefix={prefix} suffix={suffix} />
                </span>
                <span className="text-sm text-slate-500 mt-1">{label}</span>
              </div>
            ))}
          </motion.div>
        </motion.div>
      </section>

      {/* Intelligence Layers */}
      <section className="py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <motion.h2
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-3xl font-bold text-center mb-16"
          >
            Three Layers of Intelligence
          </motion.h2>

          <div className="grid md:grid-cols-3 gap-8">
            {intelligenceLayers.map((layer, i) => (
              <motion.div
                key={layer.order}
                initial={{ opacity: 0, y: 40 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.2, duration: 0.6 }}
                className={`glass p-8 ${layer.borderColor} border`}
              >
                <layer.icon className={`${layer.color} mb-4`} size={32} />
                <span className={`text-sm font-semibold ${layer.color}`}>{layer.order}</span>
                <h3 className="text-xl font-bold mt-1 mb-4">{layer.title}</h3>
                <p className="text-slate-400 text-sm italic">{layer.example}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Live Demo Strip */}
      <section className="py-24 px-6 border-t border-white/5">
        <div className="max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="glass p-10"
          >
            <h2 className="text-2xl font-bold mb-2">Try It Now</h2>
            <p className="text-slate-400 mb-8">Drag the sliders and watch the deal score update in real time.</p>

            <div className="grid md:grid-cols-3 gap-8 items-center">
              <div>
                <label className="text-sm text-slate-400 block mb-2">Ask Amount</label>
                <input
                  type="range"
                  min={10000}
                  max={5000000}
                  step={10000}
                  value={demoAsk}
                  onChange={(e) => setDemoAsk(Number(e.target.value))}
                  className="w-full accent-blue-500"
                />
                <span className="text-lg font-bold text-white">${(demoAsk / 1000).toFixed(0)}K</span>
              </div>

              <div>
                <label className="text-sm text-slate-400 block mb-2">Revenue (12mo)</label>
                <input
                  type="range"
                  min={0}
                  max={10000000}
                  step={50000}
                  value={demoRevenue}
                  onChange={(e) => setDemoRevenue(Number(e.target.value))}
                  className="w-full accent-blue-500"
                />
                <span className="text-lg font-bold text-white">${(demoRevenue / 1000).toFixed(0)}K</span>
              </div>

              <div className="flex flex-col items-center">
                <DealScoreGauge score={demoScore} animated={false} />
                <span className="text-sm text-slate-400 mt-2">Deal Score</span>
              </div>
            </div>

            <div className="mt-8 text-center">
              <Link
                href="/simulator"
                className="text-blue-400 hover:text-blue-300 text-sm font-medium inline-flex items-center gap-1"
              >
                The full simulator goes deeper <ArrowRight size={14} />
              </Link>
            </div>
          </motion.div>
        </div>
      </section>
    </div>
  );
}
```

**Step 4: Verify it renders**

Start both servers and check `http://localhost:3000`. Should see dark hero page with animated text, counters, intelligence cards, and interactive demo strip.

**Step 5: Commit**

```bash
git add frontend/src/
git commit -m "feat: build landing page with hero, intelligence cards, and live demo"
```

---

## Task 6: Frontend — Pitch Simulator Page

Build the 4-step interactive wizard.

**Files:**
- Create: `frontend/src/app/simulator/page.tsx`
- Create: `frontend/src/components/simulator/StepCompany.tsx`
- Create: `frontend/src/components/simulator/StepAsk.tsx`
- Create: `frontend/src/components/simulator/StepTraction.tsx`
- Create: `frontend/src/components/simulator/StepVerdict.tsx`

**Step 1: Create step components**

Create `frontend/src/components/simulator/StepCompany.tsx`:

```tsx
"use client";

interface StepCompanyProps {
  data: { companyName: string; industry: string; founderCount: number };
  onChange: (data: Partial<StepCompanyProps["data"]>) => void;
}

const industries = [
  "Food & Beverage", "Technology", "Health & Wellness", "Fashion & Beauty",
  "Home & Garden", "Children & Education", "Fitness & Sports", "Entertainment",
  "Automotive", "Pet Products", "Other",
];

export default function StepCompany({ data, onChange }: StepCompanyProps) {
  return (
    <div className="space-y-8">
      <div>
        <label className="block text-sm text-slate-400 mb-2">Company Name</label>
        <input
          type="text"
          value={data.companyName}
          onChange={(e) => onChange({ companyName: e.target.value })}
          placeholder="Enter your company name"
          className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
        />
      </div>

      <div>
        <label className="block text-sm text-slate-400 mb-2">Industry</label>
        <select
          value={data.industry}
          onChange={(e) => onChange({ industry: e.target.value })}
          className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-blue-500 transition-colors"
        >
          {industries.map((ind) => (
            <option key={ind} value={ind} className="bg-slate-900">{ind}</option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm text-slate-400 mb-2">Number of Founders</label>
        <div className="flex gap-3">
          {[1, 2, 3, 4].map((n) => (
            <button
              key={n}
              onClick={() => onChange({ founderCount: n })}
              className={`w-14 h-14 rounded-xl font-bold text-lg transition-all ${
                data.founderCount === n
                  ? "bg-blue-600 text-white glow-blue"
                  : "bg-white/5 text-slate-400 hover:bg-white/10"
              }`}
            >
              {n}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
```

Create `frontend/src/components/simulator/StepAsk.tsx`:

```tsx
"use client";

interface StepAskProps {
  data: { askAmount: number; equityPct: number };
  onChange: (data: Partial<StepAskProps["data"]>) => void;
}

function formatCurrency(n: number) {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  return `$${(n / 1000).toFixed(0)}K`;
}

export default function StepAsk({ data, onChange }: StepAskProps) {
  const impliedValuation = data.equityPct > 0 ? data.askAmount / (data.equityPct / 100) : 0;

  const valuationColor =
    impliedValuation <= 2_000_000 ? "text-emerald-400" :
    impliedValuation <= 5_000_000 ? "text-amber-400" :
    "text-rose-400";

  return (
    <div className="space-y-8">
      <div>
        <div className="flex justify-between mb-2">
          <label className="text-sm text-slate-400">Ask Amount</label>
          <span className="text-lg font-bold text-white">{formatCurrency(data.askAmount)}</span>
        </div>
        <input
          type="range"
          min={10000} max={5000000} step={10000}
          value={data.askAmount}
          onChange={(e) => onChange({ askAmount: Number(e.target.value) })}
          className="w-full accent-blue-500"
        />
        <div className="flex justify-between text-xs text-slate-500 mt-1">
          <span>$10K</span><span>$5M</span>
        </div>
      </div>

      <div>
        <div className="flex justify-between mb-2">
          <label className="text-sm text-slate-400">Equity Offered</label>
          <span className="text-lg font-bold text-white">{data.equityPct}%</span>
        </div>
        <input
          type="range"
          min={1} max={50} step={1}
          value={data.equityPct}
          onChange={(e) => onChange({ equityPct: Number(e.target.value) })}
          className="w-full accent-blue-500"
        />
        <div className="flex justify-between text-xs text-slate-500 mt-1">
          <span>1%</span><span>50%</span>
        </div>
      </div>

      <div className="glass p-6 text-center">
        <span className="text-sm text-slate-400">Implied Valuation</span>
        <div className={`text-3xl font-bold mt-1 ${valuationColor}`}>
          {formatCurrency(impliedValuation)}
        </div>
      </div>
    </div>
  );
}
```

Create `frontend/src/components/simulator/StepTraction.tsx`:

```tsx
"use client";

interface StepTractionProps {
  data: { revenue: number; confidence: number; showAdvanced: boolean; objections: number; negotiations: number };
  onChange: (data: Partial<StepTractionProps["data"]>) => void;
}

function formatCurrency(n: number) {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`;
  return `$${(n / 1000).toFixed(0)}K`;
}

export default function StepTraction({ data, onChange }: StepTractionProps) {
  return (
    <div className="space-y-8">
      <div>
        <div className="flex justify-between mb-2">
          <label className="text-sm text-slate-400">Trailing 12-Month Revenue</label>
          <span className="text-lg font-bold text-white">{formatCurrency(data.revenue)}</span>
        </div>
        <input
          type="range"
          min={0} max={10000000} step={50000}
          value={data.revenue}
          onChange={(e) => onChange({ revenue: Number(e.target.value) })}
          className="w-full accent-blue-500"
        />
      </div>

      <div>
        <div className="flex justify-between mb-2">
          <label className="text-sm text-slate-400">Founder Confidence</label>
          <span className="text-lg font-bold text-white">{((data.confidence + 1) / 2 * 100).toFixed(0)}%</span>
        </div>
        <input
          type="range"
          min={-100} max={100} step={1}
          value={data.confidence * 100}
          onChange={(e) => onChange({ confidence: Number(e.target.value) / 100 })}
          className="w-full accent-blue-500"
        />
      </div>

      <button
        onClick={() => onChange({ showAdvanced: !data.showAdvanced })}
        className="text-blue-400 text-sm hover:text-blue-300"
      >
        {data.showAdvanced ? "Hide" : "Show"} advanced options
      </button>

      {data.showAdvanced && (
        <div className="space-y-6 pt-4 border-t border-white/10">
          <div>
            <div className="flex justify-between mb-2">
              <label className="text-sm text-slate-400">Expected Objections</label>
              <span className="font-bold">{data.objections}</span>
            </div>
            <input
              type="range" min={0} max={10} step={1}
              value={data.objections}
              onChange={(e) => onChange({ objections: Number(e.target.value) })}
              className="w-full accent-amber-500"
            />
          </div>
          <div>
            <div className="flex justify-between mb-2">
              <label className="text-sm text-slate-400">Negotiation Rounds</label>
              <span className="font-bold">{data.negotiations}</span>
            </div>
            <input
              type="range" min={0} max={8} step={1}
              value={data.negotiations}
              onChange={(e) => onChange({ negotiations: Number(e.target.value) })}
              className="w-full accent-amber-500"
            />
          </div>
        </div>
      )}
    </div>
  );
}
```

Create `frontend/src/components/simulator/StepVerdict.tsx`:

```tsx
"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowRight, CheckCircle, AlertTriangle } from "lucide-react";
import DealScoreGauge from "@/components/ui/DealScoreGauge";
import type { PredictResponse } from "@/lib/api";

interface StepVerdictProps {
  result: PredictResponse | null;
  companyName: string;
  industry: string;
  loading: boolean;
}

export default function StepVerdict({ result, companyName, industry, loading }: StepVerdictProps) {
  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <motion.div
          animate={{ opacity: [0.3, 1, 0.3] }}
          transition={{ duration: 1.5, repeat: Infinity }}
          className="text-2xl font-bold text-slate-400"
        >
          Analyzing your pitch...
        </motion.div>
      </div>
    );
  }

  if (!result) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.3 }}
      className="space-y-8"
    >
      <div className="flex flex-col items-center py-8">
        <DealScoreGauge score={result.deal_score} size={160} />
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.5 }}
          className="text-center mt-4"
        >
          <span className="text-4xl font-bold">{(result.deal_probability * 100).toFixed(1)}%</span>
          <span className="text-slate-400 block text-sm mt-1">Deal Probability</span>
        </motion.div>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {result.strengths.length > 0 && (
          <div className="glass p-6">
            <h3 className="text-emerald-400 font-semibold mb-3 flex items-center gap-2">
              <CheckCircle size={18} /> Strengths
            </h3>
            <ul className="space-y-2">
              {result.strengths.map((s, i) => (
                <li key={i} className="text-sm text-slate-300 flex items-start gap-2">
                  <span className="text-emerald-400 mt-0.5">•</span> {s}
                </li>
              ))}
            </ul>
          </div>
        )}

        {result.risks.length > 0 && (
          <div className="glass p-6">
            <h3 className="text-amber-400 font-semibold mb-3 flex items-center gap-2">
              <AlertTriangle size={18} /> Risks
            </h3>
            <ul className="space-y-2">
              {result.risks.map((r, i) => (
                <li key={i} className="text-sm text-slate-300 flex items-start gap-2">
                  <span className="text-amber-400 mt-0.5">•</span> {r}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div className="flex gap-4 justify-center pt-4">
        <Link
          href={`/chat?context=${encodeURIComponent(`I just simulated a pitch for ${companyName} in ${industry}. Deal score was ${result.deal_score}/10. What should I know?`)}`}
          className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-3 rounded-xl font-medium transition-all glow-blue flex items-center gap-2"
        >
          Ask SharkBot for Advice <ArrowRight size={16} />
        </Link>
        <Link
          href="/hub"
          className="border border-white/20 hover:border-white/40 text-white px-6 py-3 rounded-xl font-medium transition-all"
        >
          See Comparable Deals
        </Link>
      </div>
    </motion.div>
  );
}
```

**Step 2: Create the simulator page**

Create `frontend/src/app/simulator/page.tsx`:

```tsx
"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowLeft, ArrowRight } from "lucide-react";
import StepCompany from "@/components/simulator/StepCompany";
import StepAsk from "@/components/simulator/StepAsk";
import StepTraction from "@/components/simulator/StepTraction";
import StepVerdict from "@/components/simulator/StepVerdict";
import { predictDeal, type PredictResponse } from "@/lib/api";

const STEPS = ["Your Company", "The Ask", "Your Traction", "The Verdict"];

export default function SimulatorPage() {
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PredictResponse | null>(null);

  const [company, setCompany] = useState({ companyName: "", industry: "Food & Beverage", founderCount: 1 });
  const [ask, setAsk] = useState({ askAmount: 200000, equityPct: 10 });
  const [traction, setTraction] = useState({ revenue: 500000, confidence: 0.5, showAdvanced: false, objections: 0, negotiations: 0 });

  const canProceed = step === 0 ? company.companyName.length > 0 : true;

  async function handleSubmit() {
    setStep(3);
    setLoading(true);
    try {
      const res = await predictDeal({
        ask_amount: ask.askAmount,
        equity_offered_pct: ask.equityPct,
        revenue_trailing_12m: traction.revenue,
        industry: company.industry,
        founder_count: company.founderCount,
        pitch_sentiment_score: traction.confidence,
        objection_count: traction.objections,
        negotiation_rounds: traction.negotiations,
      });
      setResult(res);
    } catch (err) {
      console.error("Prediction failed:", err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-6 py-20">
      <div className="w-full max-w-2xl">
        {/* Progress Bar */}
        <div className="flex gap-2 mb-8">
          {STEPS.map((label, i) => (
            <div key={label} className="flex-1">
              <div className={`h-1 rounded-full transition-colors ${i <= step ? "bg-blue-500" : "bg-white/10"}`} />
              <span className={`text-xs mt-1 block ${i <= step ? "text-blue-400" : "text-slate-600"}`}>{label}</span>
            </div>
          ))}
        </div>

        {/* Step Title */}
        <h1 className="text-3xl font-bold mb-8">{STEPS[step]}</h1>

        {/* Step Content */}
        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
          >
            {step === 0 && <StepCompany data={company} onChange={(d) => setCompany({ ...company, ...d })} />}
            {step === 1 && <StepAsk data={ask} onChange={(d) => setAsk({ ...ask, ...d })} />}
            {step === 2 && <StepTraction data={traction} onChange={(d) => setTraction({ ...traction, ...d })} />}
            {step === 3 && <StepVerdict result={result} companyName={company.companyName} industry={company.industry} loading={loading} />}
          </motion.div>
        </AnimatePresence>

        {/* Navigation */}
        {step < 3 && (
          <div className="flex justify-between mt-10">
            <button
              onClick={() => setStep(Math.max(0, step - 1))}
              disabled={step === 0}
              className="flex items-center gap-2 text-slate-400 hover:text-white disabled:opacity-30 transition-colors"
            >
              <ArrowLeft size={16} /> Back
            </button>

            {step < 2 ? (
              <button
                onClick={() => setStep(step + 1)}
                disabled={!canProceed}
                className="bg-blue-600 hover:bg-blue-500 disabled:opacity-30 text-white px-6 py-3 rounded-xl font-medium transition-all flex items-center gap-2"
              >
                Next <ArrowRight size={16} />
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                className="bg-blue-600 hover:bg-blue-500 text-white px-8 py-3 rounded-xl font-semibold transition-all glow-blue flex items-center gap-2"
              >
                Get My Score <ArrowRight size={16} />
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
```

**Step 3: Verify it works**

Navigate to `http://localhost:3000/simulator`, go through all 4 steps, verify deal score appears.

**Step 4: Commit**

```bash
git add frontend/src/
git commit -m "feat: build pitch simulator with 4-step wizard and real API prediction"
```

---

## Task 7: Frontend — Intelligence Hub Page

Build the tabbed dashboard with analytics, episodes, and comparables.

**Files:**
- Create: `frontend/src/app/hub/page.tsx`
- Create: `frontend/src/components/hub/AnalyticsTab.tsx`
- Create: `frontend/src/components/hub/EpisodesTab.tsx`
- Create: `frontend/src/components/hub/ComparablesTab.tsx`

**Step 1: Create AnalyticsTab component**

Create `frontend/src/components/hub/AnalyticsTab.tsx`:

```tsx
"use client";

import { useMemo } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line } from "recharts";

interface AnalyticsTabProps {
  pitches: Array<Record<string, any>>;
  stats: Record<string, any> | null;
}

export default function AnalyticsTab({ pitches, stats }: AnalyticsTabProps) {
  const seasonData = useMemo(() => {
    return stats?.seasons?.map((s: any) => ({
      name: s.season,
      pitches: s.pitch_count,
      episodes: s.episode_count,
    })) || [];
  }, [stats]);

  const signalDistribution = useMemo(() => {
    const buckets: Record<string, { total: number; count: number }> = {};
    for (const p of pitches) {
      const objections = p.signals?.objection_count ?? 0;
      const bucket = objections <= 1 ? "0-1" : objections <= 3 ? "2-3" : objections <= 5 ? "4-5" : "6+";
      if (!buckets[bucket]) buckets[bucket] = { total: 0, count: 0 };
      buckets[bucket].count++;
    }
    return ["0-1", "2-3", "4-5", "6+"].map((b) => ({ name: `${b} objections`, count: buckets[b]?.count || 0 }));
  }, [pitches]);

  return (
    <div className="space-y-8">
      {/* Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Total Pitches", value: stats?.total_pitches?.toLocaleString() ?? "—" },
          { label: "Total Episodes", value: stats?.total_episodes?.toLocaleString() ?? "—" },
          { label: "Avg Revenue Cited", value: stats ? `$${(stats.avg_revenue_mentioned / 1000).toFixed(0)}K` : "—" },
          { label: "Avg Confidence", value: stats ? `${(stats.avg_founder_confidence * 100).toFixed(1)}%` : "—" },
        ].map(({ label, value }) => (
          <div key={label} className="glass p-6 text-center">
            <div className="text-2xl font-bold text-white">{value}</div>
            <div className="text-xs text-slate-400 mt-1">{label}</div>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="glass p-6">
          <h3 className="text-sm font-semibold text-slate-400 mb-4">Pitches by Season</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={seasonData}>
              <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 12 }} />
              <YAxis tick={{ fill: "#94a3b8", fontSize: 12 }} />
              <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8 }} />
              <Bar dataKey="pitches" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="glass p-6">
          <h3 className="text-sm font-semibold text-slate-400 mb-4">Objection Distribution</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={signalDistribution}>
              <XAxis dataKey="name" tick={{ fill: "#94a3b8", fontSize: 12 }} />
              <YAxis tick={{ fill: "#94a3b8", fontSize: 12 }} />
              <Tooltip contentStyle={{ background: "#1e293b", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8 }} />
              <Bar dataKey="count" fill="#f59e0b" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
```

**Step 2: Create EpisodesTab**

Create `frontend/src/components/hub/EpisodesTab.tsx`:

```tsx
"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, ChevronUp, User, MessageSquare } from "lucide-react";

interface EpisodesTabProps {
  episodes: Array<Record<string, any>>;
}

const segmentColors: Record<string, string> = {
  founder_pitch: "bg-blue-500",
  product_demo: "bg-purple-500",
  shark_questions: "bg-cyan-500",
  objections: "bg-rose-500",
  negotiation: "bg-amber-500",
  closing_reason: "bg-slate-500",
};

export default function EpisodesTab({ episodes }: EpisodesTabProps) {
  const [expanded, setExpanded] = useState<string | null>(null);

  return (
    <div className="space-y-3">
      {episodes.map((ep) => (
        <div key={ep.episode} className="glass overflow-hidden">
          <button
            onClick={() => setExpanded(expanded === ep.episode ? null : ep.episode)}
            className="w-full flex items-center justify-between px-6 py-4 hover:bg-white/5 transition-colors"
          >
            <div className="flex items-center gap-4">
              <span className="text-blue-400 font-mono font-bold">{ep.episode}</span>
              <span className="text-sm text-slate-400">{ep.pitch_count} pitches</span>
            </div>
            {expanded === ep.episode ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>

          <AnimatePresence>
            {expanded === ep.episode && (
              <motion.div
                initial={{ height: 0 }}
                animate={{ height: "auto" }}
                exit={{ height: 0 }}
                className="overflow-hidden"
              >
                <div className="px-6 pb-6 space-y-4 border-t border-white/5 pt-4">
                  {ep.pitches?.map((pitch: any, i: number) => (
                    <div key={i} className="bg-white/5 rounded-xl p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <User size={14} className="text-blue-400" />
                          <span className="font-medium">{pitch.entrepreneur_name}</span>
                        </div>
                        <div className="flex gap-2 text-xs">
                          <span className="bg-blue-500/20 text-blue-300 px-2 py-0.5 rounded-full">
                            Revenue: ${(pitch.signals?.revenue_mentioned / 1000 || 0).toFixed(0)}K
                          </span>
                          <span className="bg-rose-500/20 text-rose-300 px-2 py-0.5 rounded-full">
                            {pitch.signals?.objection_count || 0} objections
                          </span>
                        </div>
                      </div>

                      {/* Segment bar */}
                      <div className="flex gap-0.5 h-2 rounded-full overflow-hidden">
                        {Object.entries(segmentColors).map(([seg, color]) => {
                          const texts = pitch.segments?.[seg] || [];
                          if (texts.length === 0) return null;
                          return (
                            <div
                              key={seg}
                              className={`${color} flex-grow`}
                              style={{ flexGrow: texts.length }}
                              title={`${seg}: ${texts.length} blocks`}
                            />
                          );
                        })}
                      </div>
                      <div className="flex gap-3 mt-2 flex-wrap">
                        {Object.entries(segmentColors).map(([seg, color]) => {
                          const texts = pitch.segments?.[seg] || [];
                          if (texts.length === 0) return null;
                          return (
                            <span key={seg} className="text-xs text-slate-500 flex items-center gap-1">
                              <span className={`w-2 h-2 rounded-full ${color}`} />
                              {seg.replace("_", " ")}
                            </span>
                          );
                        })}
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      ))}
    </div>
  );
}
```

**Step 3: Create ComparablesTab**

Create `frontend/src/components/hub/ComparablesTab.tsx`:

```tsx
"use client";

import { useState } from "react";
import { Search } from "lucide-react";

export default function ComparablesTab() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  async function handleSearch() {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const res = await fetch(`/api/comps`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, top_k: 10 }),
      });
      const data = await res.json();
      setResults(data.matches || []);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex gap-3">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          placeholder="Describe your pitch or company..."
          className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
        />
        <button
          onClick={handleSearch}
          disabled={loading}
          className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-3 rounded-xl font-medium transition-all flex items-center gap-2"
        >
          <Search size={16} /> {loading ? "Searching..." : "Find Comps"}
        </button>
      </div>

      {results.length > 0 && (
        <div className="space-y-3">
          {results.map((r, i) => (
            <div key={i} className="glass p-5">
              <div className="flex justify-between items-start">
                <div>
                  <span className="text-blue-400 font-mono text-sm">{r.episode}</span>
                  <span className="mx-2 text-slate-600">·</span>
                  <span className="font-medium">{r.company_name || "Unknown"}</span>
                </div>
                {r.score && (
                  <span className="text-xs bg-blue-500/20 text-blue-300 px-2 py-1 rounded-full">
                    {(r.score * 100).toFixed(0)}% match
                  </span>
                )}
              </div>
              <p className="text-sm text-slate-400 mt-2 line-clamp-2">{r.text}</p>
              <span className="text-xs text-slate-500 mt-1 block">{r.segment_type}</span>
            </div>
          ))}
        </div>
      )}

      {results.length === 0 && !loading && (
        <p className="text-center text-slate-500 py-12">
          Search for comparable pitches using natural language. Requires API keys for vector search.
        </p>
      )}
    </div>
  );
}
```

**Step 4: Create the Hub page**

Create `frontend/src/app/hub/page.tsx`:

```tsx
"use client";

import { useState, useEffect } from "react";
import { BarChart3, Tv, Search } from "lucide-react";
import AnalyticsTab from "@/components/hub/AnalyticsTab";
import EpisodesTab from "@/components/hub/EpisodesTab";
import ComparablesTab from "@/components/hub/ComparablesTab";
import { fetchEpisodes, fetchStats, fetchPitches } from "@/lib/api";

const tabs = [
  { key: "analytics", label: "Analytics", icon: BarChart3 },
  { key: "episodes", label: "Episodes", icon: Tv },
  { key: "comps", label: "Comparables", icon: Search },
];

export default function HubPage() {
  const [activeTab, setActiveTab] = useState("analytics");
  const [episodes, setEpisodes] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [pitches, setPitches] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [episodeData, statsData, pitchData] = await Promise.all([
          fetchEpisodes(),
          fetchStats(),
          fetchPitches(9999, 0),
        ]);
        setEpisodes(episodeData);
        setStats(statsData);
        setPitches(pitchData.pitches || []);
      } catch (err) {
        console.error("Failed to load data:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-slate-400 animate-pulse text-lg">Loading intelligence data...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen px-6 py-20">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-2">Intelligence Hub</h1>
        <p className="text-slate-400 mb-8">Explore patterns and facts across {stats?.total_episodes || 0} episodes</p>

        {/* Tabs */}
        <div className="flex gap-1 mb-8 bg-white/5 rounded-xl p-1 w-fit">
          {tabs.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setActiveTab(key)}
              className={`px-5 py-2.5 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
                activeTab === key ? "bg-blue-600 text-white" : "text-slate-400 hover:text-white"
              }`}
            >
              <Icon size={16} /> {label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        {activeTab === "analytics" && <AnalyticsTab pitches={pitches} stats={stats} />}
        {activeTab === "episodes" && <EpisodesTab episodes={episodes} />}
        {activeTab === "comps" && <ComparablesTab />}
      </div>
    </div>
  );
}
```

**Step 5: Verify it works**

Navigate to `http://localhost:3000/hub`. Charts should render with real data from parsed transcripts. Episode cards should expand showing pitches with segment bars.

**Step 6: Commit**

```bash
git add frontend/src/
git commit -m "feat: build Intelligence Hub with analytics charts, episode explorer, and comps search"
```

---

## Task 8: Frontend — SharkBot Chat Page

Build the RAG-powered conversational interface.

**Files:**
- Create: `frontend/src/app/chat/page.tsx`
- Create: `frontend/src/components/chat/ChatMessage.tsx`
- Create: `frontend/src/components/chat/SourcesPanel.tsx`

**Step 1: Create ChatMessage component**

Create `frontend/src/components/chat/ChatMessage.tsx`:

```tsx
"use client";

import { Bot, User } from "lucide-react";

interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
}

export default function ChatMessage({ role, content }: ChatMessageProps) {
  const isBot = role === "assistant";

  return (
    <div className={`flex gap-3 ${isBot ? "" : "flex-row-reverse"}`}>
      <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
        isBot ? "bg-blue-600" : "bg-slate-700"
      }`}>
        {isBot ? <Bot size={16} /> : <User size={16} />}
      </div>
      <div className={`max-w-[70%] rounded-2xl px-5 py-3 ${
        isBot ? "glass" : "bg-blue-600/20 border border-blue-500/20"
      }`}>
        <div className="text-sm leading-relaxed whitespace-pre-wrap">{content}</div>
      </div>
    </div>
  );
}
```

**Step 2: Create SourcesPanel component**

Create `frontend/src/components/chat/SourcesPanel.tsx`:

```tsx
"use client";

import { FileText, ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";

interface Source {
  episode: string;
  company_name: string;
  segment_type: string;
  text_snippet: string;
}

interface SourcesPanelProps {
  sources: Source[];
}

export default function SourcesPanel({ sources }: SourcesPanelProps) {
  const [expanded, setExpanded] = useState<number | null>(null);

  if (sources.length === 0) {
    return (
      <div className="h-full flex items-center justify-center text-slate-500 text-sm">
        Sources will appear here after your first question.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold text-slate-400 mb-3 flex items-center gap-2">
        <FileText size={14} /> Sources ({sources.length})
      </h3>
      {sources.map((src, i) => (
        <div key={i} className="bg-white/5 rounded-lg overflow-hidden">
          <button
            onClick={() => setExpanded(expanded === i ? null : i)}
            className="w-full flex items-center justify-between px-3 py-2 text-left hover:bg-white/5"
          >
            <div>
              <span className="text-blue-400 font-mono text-xs">{src.episode}</span>
              <span className="text-slate-400 text-xs ml-2">{src.company_name}</span>
            </div>
            {expanded === i ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          </button>
          {expanded === i && (
            <div className="px-3 pb-3">
              <span className="text-xs text-slate-500 block mb-1">{src.segment_type}</span>
              <p className="text-xs text-slate-400">{src.text_snippet}</p>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
```

**Step 3: Create the Chat page**

Create `frontend/src/app/chat/page.tsx`:

```tsx
"use client";

import { useState, useRef, useEffect } from "react";
import { useSearchParams } from "next/navigation";
import { Send } from "lucide-react";
import ChatMessage from "@/components/chat/ChatMessage";
import SourcesPanel from "@/components/chat/SourcesPanel";
import { streamAnalysis, type ChatMessage as ChatMessageType } from "@/lib/api";

const STARTERS = [
  "What industries get the most deals?",
  "Compare food vs tech pitch success rates",
  "What should I ask for with $500K revenue?",
  "Show me the biggest deals ever made",
  "What patterns do failed pitches have?",
  "Analyze objection patterns across seasons",
];

export default function ChatPage() {
  const searchParams = useSearchParams();
  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [sources, setSources] = useState<any[]>([]);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Pre-load context from simulator
  useEffect(() => {
    const context = searchParams.get("context");
    if (context && messages.length === 0) {
      setInput(context);
    }
  }, [searchParams, messages.length]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend(text?: string) {
    const query = text || input.trim();
    if (!query || streaming) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: query }]);
    setStreaming(true);

    let assistantContent = "";
    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

    try {
      for await (const chunk of streamAnalysis(query)) {
        if (chunk.type === "sources") {
          setSources(chunk.data);
        } else if (chunk.type === "text") {
          assistantContent += chunk.data;
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = { role: "assistant", content: assistantContent };
            return updated;
          });
        } else if (chunk.type === "error") {
          assistantContent = `I couldn't complete the analysis: ${chunk.data}. This likely means API keys (ANTHROPIC_API_KEY, OPENAI_API_KEY, PINECONE_API_KEY) aren't configured. You can still use the Simulator and Intelligence Hub which work with local data.`;
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = { role: "assistant", content: assistantContent };
            return updated;
          });
        }
      }
    } catch (err) {
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: "assistant",
          content: "Connection error. Make sure the API server is running on port 8000.",
        };
        return updated;
      });
    } finally {
      setStreaming(false);
    }
  }

  return (
    <div className="h-[calc(100vh-4rem)] flex">
      {/* Chat */}
      <div className="flex-1 flex flex-col">
        <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center">
              <h2 className="text-2xl font-bold mb-2">🦈 SharkBot</h2>
              <p className="text-slate-400 mb-8 text-center max-w-md">
                Ask me anything about Shark Tank pitches, deal patterns, and market intelligence.
              </p>
              <div className="grid grid-cols-2 gap-3 max-w-lg">
                {STARTERS.map((s) => (
                  <button
                    key={s}
                    onClick={() => handleSend(s)}
                    className="glass glass-hover px-4 py-3 text-sm text-left text-slate-300 hover:text-white transition-colors"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg, i) => <ChatMessage key={i} role={msg.role} content={msg.content} />)
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Input */}
        <div className="border-t border-white/10 px-6 py-4">
          <div className="flex gap-3 max-w-4xl mx-auto">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              placeholder="Ask about Shark Tank pitches..."
              disabled={streaming}
              className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 disabled:opacity-50"
            />
            <button
              onClick={() => handleSend()}
              disabled={streaming || !input.trim()}
              className="bg-blue-600 hover:bg-blue-500 disabled:opacity-30 text-white p-3 rounded-xl transition-all"
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </div>

      {/* Sources Panel */}
      <div className="w-80 border-l border-white/10 p-4 overflow-y-auto hidden lg:block">
        <SourcesPanel sources={sources} />
      </div>
    </div>
  );
}
```

**Step 4: Verify it works**

Navigate to `http://localhost:3000/chat`. Starters should show. Without API keys, sending a message should show a graceful error explaining what keys are needed.

**Step 5: Commit**

```bash
git add frontend/src/
git commit -m "feat: build SharkBot chat page with streaming SSE and sources panel"
```

---

## Task 9: Build Data Cache & Wire Everything End-to-End

Parse all real transcripts, verify all pages work with real data.

**Files:**
- No new files — integration verification

**Step 1: Build the data cache**

Run: `python3 -c "from src.data.cache import rebuild_cache; pitches = rebuild_cache(); print(f'Cached {len(pitches)} pitches')"`
Expected: Parses all 292 SRT files, creates `data/processed/all_pitches.json`.

**Step 2: Start both servers**

Use launch.json to start `shark-tank-api` and `shark-tank-frontend`.

**Step 3: Verify Landing Page**

Navigate to `http://localhost:3000`. Verify:
- Hero section renders with animated counters
- Intelligence cards scroll in
- Live demo strip sliders work

**Step 4: Verify Simulator**

Navigate to `http://localhost:3000/simulator`. Complete all 4 steps. Verify:
- Form inputs work
- Implied valuation updates live
- Deal score appears after submission
- Strengths/risks are populated

**Step 5: Verify Intelligence Hub**

Navigate to `http://localhost:3000/hub`. Verify:
- Analytics tab shows real charts with data from parsed transcripts
- Episodes tab shows real episodes that expand to show pitches
- Segment color bars render

**Step 6: Verify SharkBot**

Navigate to `http://localhost:3000/chat`. Verify:
- Starter pills render
- Clicking a starter sends the message
- Without API keys, shows graceful error

**Step 7: Commit the cache file**

```bash
echo "data/processed/all_pitches.json" >> .gitignore
git add .gitignore data/processed/.gitkeep
git commit -m "feat: complete end-to-end wiring with real SRT data cache"
```

---

## Summary

| Task | Component | New Tests |
|------|-----------|-----------|
| 1 | Data cache layer | Manual verify |
| 2 | Data endpoints (/data/*) + CORS | 3 API tests |
| 3 | Streaming SSE endpoint | Manual verify |
| 4 | Next.js scaffold + layout + API client | Manual verify |
| 5 | Landing page (hero + cards + demo) | Visual verify |
| 6 | Pitch Simulator (4-step wizard) | Visual verify |
| 7 | Intelligence Hub (analytics + episodes + comps) | Visual verify |
| 8 | SharkBot chat (streaming + sources) | Visual verify |
| 9 | End-to-end wiring with real data | Full smoke test |
