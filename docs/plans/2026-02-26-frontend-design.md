# Shark Tank AI Engine — Frontend Design

## Overview

A professional, interactive frontend for the Shark Tank AI Analysis Engine. Built with Next.js + Tailwind CSS + Framer Motion. Dark premium aesthetic with glassmorphism, scroll-driven animations, and real-time data from the FastAPI backend.

**Target Users:** Aspiring entrepreneurs preparing pitches AND investors/analysts studying deal patterns. Dual-purpose with different entry points.

**Intelligence Layer Flow:** Pages map to the three intelligence layers:
- 1st Order → "What happened?" → Intelligence Hub (Episodes tab)
- 2nd Order → "What patterns emerge?" → Intelligence Hub (Analytics tab)
- 3rd Order → "What does this predict?" → Pitch Simulator + SharkBot

---

## Architecture

**Approach:** Monorepo with separate frontend and backend processes.

```
sharky/
├── frontend/              # Next.js app
│   ├── src/
│   │   ├── app/           # Next.js App Router pages
│   │   ├── components/    # Reusable UI components
│   │   ├── lib/           # API client, utilities
│   │   └── hooks/         # Custom React hooks
│   ├── public/            # Static assets
│   ├── package.json
│   ├── tailwind.config.ts
│   └── tsconfig.json
├── src/                   # Python backend (existing)
├── .claude/launch.json    # Both servers configured
└── ...
```

**Dev servers (launch.json):**
- `shark-tank-api`: FastAPI on port 8000
- `shark-tank-frontend`: Next.js on port 3000, proxies `/api/*` to port 8000

**Tech Stack:**
- Next.js 14+ (App Router)
- TypeScript
- Tailwind CSS v3
- Framer Motion for animations
- Recharts for data visualization
- Lucide React for icons

---

## Design Language

- **Base:** #0a0a0f (near-black), deep navy gradients
- **Surface:** rgba(255,255,255,0.05) glassmorphism with backdrop-blur
- **Primary accent:** Electric blue #3b82f6
- **Secondary accent:** Amber/gold #f59e0b (deal scores, warnings)
- **Success:** Emerald #10b981
- **Danger:** Rose #f43f5e
- **Text:** White #ffffff (headings), #94a3b8 (body), #64748b (muted)
- **Typography:** Inter (sans-serif), bold headings, clean body text
- **Cards:** Glassmorphism with subtle border glow (border: 1px solid rgba(255,255,255,0.1))
- **Animations:** Framer Motion — page transitions (fade+slide), scroll-triggered reveals, number counters, gauge animations

---

## Page 1: Landing / Hero

### Hero Section (full viewport)
- Dark gradient background (#0a0a0f → #0f172a)
- Headline: **"Know Your Odds Before You Enter the Tank"**
- Subtitle: "AI-powered pitch analysis across 15 seasons of Shark Tank data"
- Animated counter stats (tick up on scroll): `292 Episodes Analyzed` · `1,200+ Pitches Parsed` · `$2.4B in Deals Tracked`
- Primary CTA: glowing blue button → "Simulate Your Pitch" → /simulator
- Secondary CTA: outlined button → "Explore the Data" → /hub

### Three Intelligence Cards (scroll-triggered)
- Three glassmorphism cards slide in with staggered animation
- 1st Order card: "What Happened" — sample fact with episode citation
- 2nd Order card: "What Patterns Emerge" — sample insight with percentage
- 3rd Order card: "What This Predicts" — sample prediction with deal score gauge
- Maps to the user's intelligence layer design

### Live Demo Strip
- Compact inline mini-predictor
- Two sliders (Ask Amount, Revenue) → instant animated deal score gauge
- Text: "This is just a taste. The full simulator goes deeper →"

### Footer
- Tech stack badges (XGBoost, Claude, Pinecone)
- Navigation links
- GitHub link

---

## Page 2: Pitch Simulator (/simulator)

Interactive 4-step wizard with animated transitions between steps.

### Step 1: "Your Company"
- Company name (text input)
- Industry (dropdown with category icons)
- Number of founders (1-4 stepper)
- Background: animated shark silhouettes

### Step 2: "The Ask"
- Ask Amount: styled slider $10K → $5M
- Equity Offered: slider 1% → 50%
- Live computed card: "Implied Valuation: $X" updates in real-time
- Valuation meter: color zones (green = reasonable, yellow = aggressive, red = outrageous)

### Step 3: "Your Traction"
- Trailing 12-month Revenue: slider $0 → $10M
- Founder Confidence: slider (maps to pitch_sentiment_score)
- Advanced toggles (expandable): Shark Enthusiasm, Objection Count, Negotiation Rounds

### Step 4: "The Verdict" (animated reveal)
- Dramatic dark pause (800ms)
- Deal Score gauge: animates 0 → final (1-10) with particle effects
- Deal Probability: counter ticks up to percentage
- Strengths: green check icons
- Risks: amber warning icons
- CTAs: "Ask SharkBot for advice →" (pre-loads context), "See comparable deals →" (filters Hub)

**API:** POST `/predict` with form values.

---

## Page 3: Intelligence Hub (/hub)

### Global Filters (top bar)
- Season range selector (S1–S15)
- Industry multi-select chips
- Deal outcome toggle (All / Deals / No Deals)
- Search bar (company/entrepreneur name)

### Tab 1: "Analytics" (2nd Order)
- **Deal Rate by Industry:** Horizontal bar chart, sorted by success rate
- **Ask vs. Outcome Scatter:** Bubble chart — X: ask, Y: equity, bubble size: revenue, color: deal/no-deal
- **Season Trends:** Line chart — deal rate and average ask over time
- **Key Stats Row:** 4 glassmorphism cards — Total Deals, Avg Ask, Avg Equity Given, Top Industry
- Charts are interactive: click a bar to filter the data table below

### Tab 2: "Episodes" (1st Order)
- Card grid of parsed episodes
- Each card: episode code, pitch count badge, deal count badge
- Click → detail panel:
  - Per-pitch horizontal timeline with colored segment bars (founder_pitch=blue, objections=red, negotiation=amber)
  - Extracted signals: revenue, objection count, sentiment score
  - Transcript viewer with segments color-coded by type
  - Speaker role badges (Narrator, Entrepreneur, Shark)

### Tab 3: "Comparables"
- Text input: "Describe your pitch or company..."
- Results: cards of most similar past pitches
- Each card: company name, episode, ask, outcome, similarity score
- API: POST `/comps`

---

## Page 4: SharkBot (/chat)

### Layout: Split-panel
- Left 60%: Chat interface
- Right 40%: Sources panel (collapsible on mobile)

### Chat Interface
- User messages: dark-blue bubble, right-aligned
- Bot messages: glassmorphism card, left-aligned, SharkBot avatar (shark fin icon)
- Rich markdown rendering: bullet points, bold stats, section headers
- Inline citations: `[S03E05 - FreshBites]` — hover highlights source in right panel
- Typing indicator with animated dots during generation
- Streaming responses via SSE for real-time feel

### Suggested Starters (before first message)
Six clickable pills:
1. "What industries get the most deals?"
2. "Compare food vs tech pitch success rates"
3. "What should I ask for with $500K revenue?"
4. "Show me the biggest deals ever made"
5. "What patterns do failed pitches have?"
6. "Analyze objection patterns across seasons"

### Sources Panel (right side)
- Retrieved chunks as collapsible cards:
  - Episode badge, Company name, Segment type tag
  - Text snippet (expandable)
  - Relevance score bar

### Context Passing
- From Simulator: pre-loads "I just simulated a pitch: [details]. Deal score was [N]/10. What should I know?"
- From Intelligence Hub: pre-loads "Tell me more about [Company] from [Episode]"

### Real-time Industry Context
- Web search augmentation: when query mentions an industry, fetch recent news/trends
- Inject into RAG prompt alongside Pinecone results
- Display as "Market Context" section in bot response

### Backend Changes Required
- New endpoint: `GET /analyze/stream` — SSE streaming version of `/analyze`
- Web search integration in retrieval_chain.py

---

## Backend Enhancements Required

### 1. Data Pipeline Endpoint
New endpoint to parse real SRT data and return structured results:
```
GET  /data/episodes          → list of parsed episodes with signals
GET  /data/episodes/{code}   → single episode detail
GET  /data/stats             → aggregate statistics for dashboard
```

### 2. Streaming Analysis
```
GET  /analyze/stream?query=...&top_k=5  → SSE stream
```

### 3. Real-time Industry Context
Add web search step to retrieval_chain.py:
- Query → embed → Pinecone search + web search → merge context → Claude synthesis

### 4. Parse and Cache Real Data
- On startup or via CLI: parse all SRT transcripts and cache as JSON
- Serve cached data via the `/data/*` endpoints
- No database needed initially — JSON file cache is sufficient

---

## Responsive Design

- **Desktop (1280+):** Full layout as described
- **Tablet (768-1279):** Stack Intelligence Hub tabs vertically, SharkBot sources panel collapses to bottom drawer
- **Mobile (< 768):** Single column, hamburger nav, simulator steps are full-width cards, SharkBot sources accessible via "View Sources" button

---

## Data Flow Summary

```
┌──────────────────────────────────────────────────────────┐
│                    NEXT.JS FRONTEND                      │
│                                                          │
│  Landing ──→ Simulator ──→ Intelligence Hub ──→ SharkBot │
│    (CTA)     (POST /predict)  (GET /data/*)   (SSE /analyze/stream) │
└──────────────┬───────────────────────────────────────────┘
               │ HTTP (port 3000 proxies to 8000)
┌──────────────▼───────────────────────────────────────────┐
│                   FASTAPI BACKEND                        │
│                                                          │
│  /predict    /data/episodes   /analyze/stream   /comps   │
│  /health     /data/stats      /analyze                   │
│                                                          │
│  Backed by: XGBoost model, parsed SRT cache,            │
│  Pinecone vectors, Claude API                            │
└──────────────────────────────────────────────────────────┘
```
