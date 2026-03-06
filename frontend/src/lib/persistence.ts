"use client";

export interface SavedAnalysis {
  id: string;
  type: "vc" | "founder" | "market-fit";
  title: string;
  created_at: string;
  summary: string;
  payload: Record<string, unknown>;
}

const ANALYSIS_KEY = "dealscope_saved_analyses";
const WATCHLIST_KEY = "dealscope_watchlist";

export function loadSavedAnalyses(): SavedAnalysis[] {
  try {
    const raw = localStorage.getItem(ANALYSIS_KEY);
    return raw ? (JSON.parse(raw) as SavedAnalysis[]) : [];
  } catch {
    return [];
  }
}

export function saveAnalysis(entry: SavedAnalysis) {
  const all = [entry, ...loadSavedAnalyses()].slice(0, 50);
  localStorage.setItem(ANALYSIS_KEY, JSON.stringify(all));
}

export function clearSavedAnalyses() {
  localStorage.removeItem(ANALYSIS_KEY);
}

export function loadWatchlist(): string[] {
  try {
    const raw = localStorage.getItem(WATCHLIST_KEY);
    return raw ? (JSON.parse(raw) as string[]) : [];
  } catch {
    return [];
  }
}

export function addToWatchlist(item: string) {
  const next = Array.from(new Set([item, ...loadWatchlist()])).slice(0, 100);
  localStorage.setItem(WATCHLIST_KEY, JSON.stringify(next));
}

export function removeFromWatchlist(item: string) {
  const next = loadWatchlist().filter((x) => x !== item);
  localStorage.setItem(WATCHLIST_KEY, JSON.stringify(next));
}

export function clearWatchlist() {
  localStorage.removeItem(WATCHLIST_KEY);
}

