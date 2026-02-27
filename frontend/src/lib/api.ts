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
