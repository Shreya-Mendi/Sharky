# DealScope — AI-Powered Business Intelligence Platform

## Design Document (Approved 2026-03-01)

### Vision

Rebrand from "SharkTank AI Engine" to **DealScope** — an all-in-one BI suite that transforms 741+ parsed Shark Tank pitches into actionable business intelligence for entrepreneurs. The focus shifts from Shark Tank trivia to **market analysis, deal benchmarking, and AI-powered research** that helps founders make better decisions.

### Design Reference

Visual style inspired by [magic-receipt.ai](https://magic-receipt.ai/) — dark theme, neon accent gradients, dashboard-first layout, polished SaaS feel.

---

## Section 1: Landing Page

**Route:** `/`

A marketing scroll page designed to convert visitors into product users.

### Structure

1. **Hero Block**
   - Headline: "Turn Data Into Deal-Ready Intelligence"
   - Subline: "AI-powered market analysis from 741+ real venture pitches"
   - Two CTAs: "Start Analyzing" (primary, blue glow) | "See How It Works" (ghost)
   - Background: subtle animated gradient mesh (blue → purple → dark)

2. **Stats Strip** (animated counters on scroll)
   - 741+ Deals Analyzed | 15 Seasons of Data | $2.4B in Deals Tracked | 292 Episodes Parsed

3. **Three-Feature Showcase** (cards with icons + short copy)
   - **Market Analysis** — "Deep-dive into industry trends, deal success rates, and valuation benchmarks"
   - **Deal Simulator** — "Test your pitch parameters against real historical outcomes"
   - **Research Agent** — "AI agent that autonomously researches market patterns and generates reports"

4. **How It Works** (3-step horizontal flow)
   - Step 1: "Choose your industry" → Step 2: "AI analyzes 741+ deals" → Step 3: "Get actionable insights"

5. **Dashboard Preview** (glassmorphic screenshot/mockup of the dashboard)
   - Shows a peek of the actual dashboard UI with blurred/faded edges

6. **CTA Footer**
   - "Ready to make data-driven decisions?"
   - "Launch DealScope" button

### Visual Style
- Dark background (#0a0a0f)
- Electric blue (#3b82f6) primary accent
- Amber (#f59e0b) secondary accent
- Glassmorphism cards
- Smooth framer-motion scroll animations

---

## Section 2: App Shell & Dashboard

### App Shell Architecture

**Layout:** Collapsible sidebar (240px expanded / 64px collapsed) + main content area

**Sidebar Navigation:**
| Icon | Label | Route |
|------|-------|-------|
| LayoutDashboard | Dashboard | `/app` |
| TrendingUp | Market Analysis | `/app/market` |
| Sliders | Deal Simulator | `/app/simulator` |
| Bot | Research Agent | `/app/agent` |
| Search | Deal Explorer | `/app/deals` |

**Sidebar Footer:** User avatar placeholder, settings gear, collapse toggle

**Top Bar:** Page title + breadcrumb, global search input, notification bell placeholder

### Dashboard Page (`/app`)

The default landing after entering the app shell.

#### Layout (2-column grid)

**KPI Strip** (full width, 4 cards):
- Total Deals: 741 (with trend arrow)
- Avg Deal Size: calculated from data
- Success Rate: % of deals that closed
- Top Industry: most common category

**Left Column (60%):**
- **Deal Flow Over Time** — Recharts area chart showing deals per season
- **Industry Heatmap** — Grid of industry tiles, color-coded by deal success rate (green = high, red = low), sized by deal count

**Right Column (40%):**
- **Market Pulse** — AI-generated 3-sentence summary of current market patterns (calls `/data/stats` + heuristic)
- **Quick Actions** — 4 shortcut buttons: "Simulate a Deal", "Research a Market", "Browse Deals", "View Trends"
- **Recent Deals** — Last 5 pitches from the database as compact cards

---

## Section 3: Multi-Step Research Agent

**Route:** `/app/agent`

### Architecture

A Claude-powered autonomous research agent that uses tool-calling to investigate market questions.

#### Backend: `/api/agent/research` (POST, SSE streaming)

**Request:**
```json
{
  "query": "What makes food-tech startups successful on Shark Tank?",
  "depth": "standard" | "deep"
}
```

**Agent Tools (5):**

| Tool | Description | Data Source |
|------|-------------|------------|
| `search_deals` | Semantic search across 741 pitches | Pitch database (text matching) |
| `predict_deal` | Run deal prediction model | XGBoost / heuristic |
| `get_market_stats` | Aggregate stats by industry/season | Cached stats |
| `web_search` | Search for current market trends | Web search API |
| `analyze_patterns` | Cross-reference multiple data points | Computed analysis |

**Streaming Response (SSE):**
```
event: step
data: {"type": "tool_call", "tool": "search_deals", "input": {...}, "result": {...}}

event: step
data: {"type": "tool_call", "tool": "get_market_stats", "input": {...}, "result": {...}}

event: step
data: {"type": "thinking", "content": "Analyzing patterns across 23 food-tech deals..."}

event: step
data: {"type": "tool_call", "tool": "web_search", "input": {...}, "result": {...}}

event: answer
data: {"type": "answer", "content": "Based on my analysis..."}

event: done
data: {"type": "done"}
```

### Frontend UI

**Layout:** Two-panel (60/40 split)

**Left Panel — Chat Interface:**
- Message input with "Research this..." placeholder
- Starter prompt pills: "Food-tech market analysis", "Best equity structures", "Revenue benchmarks by industry", "Emerging categories"
- Chat history with markdown-rendered AI responses
- Typing indicator during streaming

**Right Panel — Research Steps:**
- Real-time display of agent tool calls as they happen
- Each tool call renders as a card:
  - Tool icon + name
  - Input parameters (collapsible)
  - Result summary
  - Status indicator (spinning → checkmark)
- "Sources Used" section at bottom listing referenced deals

### Agent Behavior
1. Receives user query
2. Plans research steps autonomously
3. Executes 2-5 tool calls to gather data
4. Synthesizes findings into a comprehensive answer
5. Cites specific deals and statistics
6. Streams everything in real-time via SSE

---

## Section 4: Market Analysis & Deal Explorer

### Market Analysis (`/app/market`)

**Layout:** Industry selector at top → content below

**Industry Selector:** Horizontal scrollable pill/chip bar with all industries from the dataset (Food & Beverage, Technology, Health & Wellness, Fashion, etc.) + "All Industries" default

**Content Grid (selected industry):**

1. **Deal Success Rate** — Large donut chart (deals closed vs. not)
2. **Key Metrics** — 4 stat cards: Avg Ask, Avg Equity, Avg Valuation, Deal Count
3. **Revenue Distribution** — Histogram of trailing 12-month revenue at time of pitch
4. **Valuation vs. Outcome** — Scatter plot (ask amount vs. equity, color = deal/no deal)
5. **AI Industry Brief** — 3-4 sentence AI-generated summary of industry patterns (pre-computed or on-demand)
6. **Top Deals in Category** — Sortable mini-table of top 10 deals by deal amount

### Deal Explorer (`/app/deals`)

**Layout:** Full-width filterable data table

**Filters Bar:**
- Industry dropdown
- Season/Episode range
- Deal outcome (Got Deal / No Deal)
- Ask amount range slider
- Revenue range slider
- Search by company name

**Table Columns:**
| Company | Industry | Season | Ask | Equity | Revenue | Outcome | Deal Amount |
|---------|----------|--------|-----|--------|---------|---------|-------------|

**Features:**
- Sortable columns (click header)
- Expandable rows (click to see full pitch details, sharks involved, notes)
- Pagination (25 per page)
- Export button placeholder
- Total results count

---

## Technical Architecture

### Frontend Stack
- Next.js 16 (App Router)
- TypeScript
- Tailwind CSS v4
- Framer Motion (animations)
- Recharts (charts/graphs)
- Lucide React (icons)

### Backend Stack
- FastAPI (Python)
- XGBoost (deal prediction, with heuristic fallback)
- Anthropic Claude API (research agent)
- SSE streaming (agent responses)

### Route Structure
```
/                    → Landing page (marketing)
/app                 → Dashboard (app shell)
/app/market          → Market Analysis
/app/simulator       → Deal Simulator
/app/agent           → Research Agent
/app/deals           → Deal Explorer
```

### New API Endpoints
```
POST /agent/research     → SSE streaming research agent
GET  /data/industries    → List industries with stats
GET  /data/deals         → Filterable deal list (replaces /data/pitches)
```

### Data Flow
1. 741 pitches loaded from SRT cache at startup
2. Stats computed and cached
3. Industry aggregations computed on demand (or cached)
4. Research agent queries Claude API with tool definitions
5. Agent tools query the cached pitch data
6. Results streamed back via SSE

---

## Migration from Current State

### What Changes
- Landing page: Complete redesign (new copy, new layout, new components)
- Navbar: Replaced by sidebar in app shell; landing page gets its own minimal nav
- `/simulator`: Moves to `/app/simulator`, enhanced with industry context
- `/hub`: Split into `/app/market` (analytics) + `/app/deals` (episodes/search)
- `/chat`: Becomes `/app/agent` with tool-calling architecture
- Layout: App shell with sidebar replaces current full-width + top nav
- Branding: "SharkTank AI" → "DealScope" everywhere

### What Stays
- API client (`lib/api.ts`) — extended, not replaced
- DealScoreGauge component — reused in simulator
- AnimatedCounter — reused on landing page
- Dark theme + glassmorphism CSS — enhanced, not replaced
- All backend endpoints — extended with new ones
- Data cache — unchanged
