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

export interface Industry {
  industry: string;
  deal_count: number;
  success_rate: number;
  avg_ask: number;
  avg_revenue: number;
  pitch_count: number;
}

export interface Deal {
  episode: string;
  company_name: string;
  industry: string;
  season: string;
  revenue: number;
  objection_count: number;
  negotiation_rounds: number;
  founder_confidence: number;
  shark_enthusiasm: number;
  has_deal: boolean;
}

export interface DealsResponse {
  total: number;
  deals: Deal[];
}

export async function fetchIndustries(): Promise<Industry[]> {
  const res = await fetch("/api/data/industries");
  if (!res.ok) throw new Error("Failed to fetch industries");
  return res.json();
}

export async function fetchDeals(params?: {
  limit?: number;
  offset?: number;
  industry?: string;
  has_deal?: boolean;
  search?: string;
}): Promise<DealsResponse> {
  const searchParams = new URLSearchParams();
  if (params?.limit) searchParams.set("limit", String(params.limit));
  if (params?.offset) searchParams.set("offset", String(params.offset));
  if (params?.industry) searchParams.set("industry", params.industry);
  if (params?.has_deal !== undefined) searchParams.set("has_deal", String(params.has_deal));
  if (params?.search) searchParams.set("search", params.search);
  const res = await fetch(`/api/data/deals?${searchParams}`);
  if (!res.ok) throw new Error("Failed to fetch deals");
  return res.json();
}

export interface ToolCallEvent {
  type: "tool_call" | "tool_result" | "thinking" | "answer" | "error" | "done";
  tool?: string;
  input?: Record<string, unknown>;
  result?: unknown;
  content?: string;
  data?: string;
  status?: string;
}

export async function* streamResearch(query: string, depth: string = "standard"): AsyncGenerator<ToolCallEvent> {
  const res = await fetch(`/api/agent/research?query=${encodeURIComponent(query)}&depth=${encodeURIComponent(depth)}`);
  if (!res.ok) throw new Error("Research agent unavailable");
  const reader = res.body?.getReader();
  if (!reader) return;
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";
    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          yield JSON.parse(line.slice(6));
        } catch {}
      }
    }
  }
}
