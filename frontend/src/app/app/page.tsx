"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { ArrowRight, BrainCircuit, ClipboardCheck, Globe2, TrendingUp } from "lucide-react";
import { fetchIndustries, fetchStats } from "@/lib/api";
import type { Industry } from "@/lib/api";
import { clearSavedAnalyses, clearWatchlist, loadSavedAnalyses, loadWatchlist, type SavedAnalysis } from "@/lib/persistence";

interface StatsShape {
  total_pitches: number;
  total_episodes: number;
  total_seasons: number;
  avg_revenue_mentioned: number;
  avg_objection_count: number;
  avg_founder_confidence: number;
}

const ENGINE_CARDS = [
  {
    href: "/app/market",
    title: "Industry Intelligence Engine",
    description: "Quantify which patterns drive success in each sector.",
    icon: TrendingUp,
  },
  {
    href: "/app/simulator",
    title: "Startup Readiness Engine",
    description: "Benchmark startup readiness against successful peers.",
    icon: ClipboardCheck,
  },
  {
    href: "/app/deals",
    title: "Market Fit Recommender",
    description: "Rank regions, sectors, and growth avenues with confidence.",
    icon: Globe2,
  },
];

export default function EngineHubPage() {
  const [stats, setStats] = useState<StatsShape | null>(null);
  const [industries, setIndustries] = useState<Industry[]>([]);
  const [loading, setLoading] = useState(true);
  const [savedAnalyses, setSavedAnalyses] = useState<SavedAnalysis[]>([]);
  const [watchlist, setWatchlist] = useState<string[]>([]);

  useEffect(() => {
    Promise.all([fetchStats(), fetchIndustries()])
      .then(([statsData, industriesData]) => {
        setStats(statsData as StatsShape);
        setIndustries(industriesData);
        setSavedAnalyses(loadSavedAnalyses());
        setWatchlist(loadWatchlist());
      })
      .finally(() => setLoading(false));
  }, []);

  const topIndustry = useMemo(() => {
    if (industries.length === 0) return "N/A";
    return industries.reduce((a, b) => (a.deal_count >= b.deal_count ? a : b)).industry;
  }, [industries]);

  if (loading) {
    return <div className="py-20 text-center text-[var(--text-muted)]">Loading intelligence engines...</div>;
  }

  return (
    <div className="space-y-8">
      <section className="rounded-2xl border border-white/10 bg-[var(--bg-surface)] p-7 md:p-9">
        <div className="flex items-start justify-between gap-6">
          <div>
            <p className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-black/20 px-3 py-1 text-xs uppercase tracking-[0.18em] text-[var(--text-muted)]">
              <BrainCircuit size={14} className="text-[var(--accent-blue)]" />
              Engine-First Platform
            </p>
            <h1 className="mt-4 text-3xl md:text-4xl font-semibold tracking-tight">
              Decision intelligence for VCs and founders
            </h1>
            <p className="mt-3 max-w-3xl text-[var(--text-muted)] leading-relaxed">
              Pattern intelligence from a corpus of real pitch transcripts — three engines for sector analysis,
              startup readiness benchmarking, and market-fit ranking. Signals are derived from pitch dynamics
              (confidence, objections, negotiation depth) rather than generic VC heuristics.
            </p>
          </div>
        </div>
      </section>

      <section className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard label="Records Parsed" value={String(stats?.total_pitches ?? 0)} />
        <MetricCard label="Source Episodes" value={String(stats?.total_episodes ?? 0)} />
        <MetricCard label="Top Sector" value={topIndustry} />
        <MetricCard label="Avg Revenue Signal" value={`$${Math.round((stats?.avg_revenue_mentioned ?? 0) / 1000)}K`} />
      </section>

      <section className="grid lg:grid-cols-3 gap-4">
        {ENGINE_CARDS.map((engine) => (
          <Link
            key={engine.title}
            href={engine.href}
            className="group rounded-2xl border border-white/12 bg-[var(--bg-surface)] p-6 hover:border-white/30 transition-colors"
          >
            <engine.icon size={20} className="text-[var(--accent-blue)]" />
            <h2 className="mt-4 text-xl font-semibold">{engine.title}</h2>
            <p className="mt-2 text-sm leading-relaxed text-[var(--text-muted)]">{engine.description}</p>
            <div className="mt-6 inline-flex items-center gap-1 text-sm font-medium text-white/80 group-hover:text-white">
              Open engine <ArrowRight size={14} />
            </div>
          </Link>
        ))}
      </section>

      <section className="grid lg:grid-cols-3 gap-4">
        <div className="rounded-2xl border border-white/12 bg-[var(--bg-surface)] p-5">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Watchlists</h2>
            <button
              className="text-xs border border-white/20 rounded-lg px-2 py-1"
              onClick={() => {
                clearWatchlist();
                setWatchlist([]);
              }}
            >
              Clear
            </button>
          </div>
          <ul className="mt-3 space-y-2 text-sm text-[var(--text-muted)]">
            {watchlist.length === 0 ? <li>No watchlist items yet.</li> : watchlist.map((w) => <li key={w}>- {w}</li>)}
          </ul>
        </div>

        <div className="rounded-2xl border border-white/12 bg-[var(--bg-surface)] p-5">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Saved Analyses</h2>
            <button
              className="text-xs border border-white/20 rounded-lg px-2 py-1"
              onClick={() => {
                clearSavedAnalyses();
                setSavedAnalyses([]);
              }}
            >
              Clear
            </button>
          </div>
          <ul className="mt-3 space-y-2 text-sm text-[var(--text-muted)]">
            {savedAnalyses.length === 0 ? (
              <li>No saved analyses yet.</li>
            ) : (
              savedAnalyses.slice(0, 5).map((a) => (
                <li key={a.id}>- {a.title} ({new Date(a.created_at).toLocaleDateString()})</li>
              ))
            )}
          </ul>
        </div>

        <div className="rounded-2xl border border-white/12 bg-[var(--bg-surface)] p-5 flex flex-col justify-between">
          <div>
            <h2 className="text-lg font-semibold">Integrations</h2>
            <p className="mt-2 text-sm text-[var(--text-muted)]">
              Connect DealScope to your existing workflow via webhook, export to IC memo, or configure API access.
            </p>
          </div>
          <Link
            href="/app/settings"
            className="mt-5 inline-flex items-center gap-1.5 rounded-lg border border-white/20 px-3 py-2 text-sm hover:bg-white/5 transition-colors w-fit"
          >
            Open Integrations Settings <ArrowRight size={13} />
          </Link>
        </div>
      </section>
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-white/10 bg-black/20 px-5 py-4">
      <p className="text-xs uppercase tracking-[0.18em] text-[var(--text-muted)]">{label}</p>
      <p className="mt-2 text-2xl font-semibold">{value}</p>
    </div>
  );
}
