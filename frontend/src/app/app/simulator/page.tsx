"use client";

import { useEffect, useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { fetchIndustries, fetchStartupStrategy } from "@/lib/api";
import type { Industry, StartupStrategyResponse } from "@/lib/api";
import { exportICMemoPdf } from "@/lib/exportMemo";
import { addToWatchlist, saveAnalysis } from "@/lib/persistence";

type ModelType = "b2b" | "b2c" | "hybrid";

interface ReadinessForm {
  company_name: string;
  industry: string;
  ask_amount: number;
  equity_offered_pct: number;
  revenue_trailing_12m: number;
  founder_count: number;
  growth_rate_qoq: number;
  monthly_burn: number;
  gross_margin_pct: number;
  business_model: ModelType;
  // Advanced / scenario fields
  price_change_pct: number;
  gtm_efficiency_delta: number;
  cac_delta: number;
  hiring_plan_delta: number;
  localization_readiness: number;
}

const DEFAULT_FORM: ReadinessForm = {
  company_name: "",
  industry: "Technology",
  ask_amount: 350000,
  equity_offered_pct: 10,
  revenue_trailing_12m: 500000,
  founder_count: 2,
  growth_rate_qoq: 0.12,
  monthly_burn: 60000,
  gross_margin_pct: 55,
  business_model: "hybrid",
  // Advanced defaults — calibrated to "neutral" scenario
  price_change_pct: 0.0,
  gtm_efficiency_delta: 0.0,
  cac_delta: 0.0,
  hiring_plan_delta: 0.0,
  localization_readiness: 0.5,
};

export default function StartupReadinessPage() {
  const [industries, setIndustries] = useState<Industry[]>([]);
  const [form, setForm] = useState<ReadinessForm>(DEFAULT_FORM);
  const [result, setResult] = useState<StartupStrategyResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showAdvanced, setShowAdvanced] = useState(false);

  useEffect(() => {
    fetchIndustries().then((data) => {
      setIndustries(data);
      if (data.length > 0) {
        setForm((prev) => ({ ...prev, industry: data[0].industry }));
      }
    });
  }, []);

  async function runEngine() {
    if (!form.company_name.trim()) {
      setError("Company name is required.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetchStartupStrategy(form);
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to run Startup Readiness Engine.");
    } finally {
      setLoading(false);
    }
  }

  function updateForm<K extends keyof ReadinessForm>(key: K, value: ReadinessForm[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function updateNumber<K extends keyof ReadinessForm>(key: K, value: string) {
    updateForm(key, Number(value) as ReadinessForm[K]);
  }

  function handleSave() {
    if (!result) return;
    saveAnalysis({
      id: `${Date.now()}`,
      type: "founder",
      title: `${result.company_name} readiness`,
      created_at: new Date().toISOString(),
      summary: `Readiness ${result.readiness_score}/100, deal probability ${Math.round(result.deal_probability * 100)}%`,
      payload: result as unknown as Record<string, unknown>,
    });
  }

  function handleExportMemo() {
    if (!result) return;
    exportICMemoPdf(`IC Memo: ${result.company_name}`, [
      {
        title: "Readiness Summary",
        body: `Readiness score: ${result.readiness_score}/100\nDeal probability: ${Math.round(result.deal_probability * 100)}%\nStage: ${result.stage}`,
      },
      {
        title: "Top Drivers",
        body: result.recommendation.top_5_drivers.map((d) => `- ${d.driver}: ${d.impact}`).join("\n"),
      },
      {
        title: "Gaps & Recommendations",
        body: [...result.gaps.map((x) => `Gap: ${x}`), ...result.recommendations.map((x) => `Action: ${x}`)].join("\n"),
      },
    ]);
  }

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-white/12 bg-[var(--bg-surface)] p-6 md:p-7">
        <h1 className="text-2xl font-semibold">Startup Readiness Engine</h1>
        <p className="mt-2 text-sm text-[var(--text-muted)]">
          Benchmark your profile against top pitch peers, surface gaps, and get a ranked US market recommendation.
          Patterns are derived from a corpus of real pitch transcripts — signals reflect what drove successful outcomes
          in high-stakes pitch environments, not generic VC heuristics.
        </p>

        {/* Core fields — always visible */}
        <div className="mt-5 grid md:grid-cols-2 lg:grid-cols-3 gap-3">
          <Input
            label="Company Name *"
            value={form.company_name}
            onChange={(v) => updateForm("company_name", v)}
            placeholder="e.g. Nova Freight"
          />

          <label className="space-y-2">
            <span className="text-xs uppercase tracking-[0.12em] text-[var(--text-muted)]">Industry</span>
            <select
              value={form.industry}
              onChange={(e) => updateForm("industry", e.target.value)}
              className="w-full rounded-xl border border-white/15 bg-black/25 px-3 py-2.5 text-sm"
            >
              {industries.map((ind) => (
                <option key={ind.industry} value={ind.industry} className="bg-[#171919]">
                  {ind.industry}
                </option>
              ))}
            </select>
          </label>

          <label className="space-y-2">
            <span className="text-xs uppercase tracking-[0.12em] text-[var(--text-muted)]">Business Model</span>
            <select
              value={form.business_model}
              onChange={(e) => updateForm("business_model", e.target.value as ModelType)}
              className="w-full rounded-xl border border-white/15 bg-black/25 px-3 py-2.5 text-sm"
            >
              <option value="b2b" className="bg-[#171919]">B2B — sells to businesses</option>
              <option value="b2c" className="bg-[#171919]">B2C — sells to consumers</option>
              <option value="hybrid" className="bg-[#171919]">Hybrid — both channels</option>
            </select>
          </label>

          <NumberInput
            label="Investment Ask (USD)"
            hint="How much you're raising in this round"
            value={form.ask_amount}
            onChange={(v) => updateNumber("ask_amount", v)}
          />
          <NumberInput
            label="Equity Offered (%)"
            hint="Percentage of company offered for the ask"
            value={form.equity_offered_pct}
            onChange={(v) => updateNumber("equity_offered_pct", v)}
            step={0.5}
          />
          <NumberInput
            label="Trailing 12M Revenue (USD)"
            hint="Total revenue in the last 12 months"
            value={form.revenue_trailing_12m}
            onChange={(v) => updateNumber("revenue_trailing_12m", v)}
          />
          <NumberInput
            label="Founder Count"
            hint="Number of co-founders on the team"
            value={form.founder_count}
            onChange={(v) => updateNumber("founder_count", v)}
            step={1}
          />
          <NumberInput
            label="QoQ Growth Rate"
            hint="Quarter-over-quarter growth as decimal (0.15 = 15%)"
            value={form.growth_rate_qoq}
            onChange={(v) => updateNumber("growth_rate_qoq", v)}
            step={0.01}
          />
          <NumberInput
            label="Monthly Burn (USD)"
            hint="Total cash spent per month including salaries"
            value={form.monthly_burn}
            onChange={(v) => updateNumber("monthly_burn", v)}
          />
          <NumberInput
            label="Gross Margin (%)"
            hint="Revenue minus direct costs as a percentage of revenue"
            value={form.gross_margin_pct}
            onChange={(v) => updateNumber("gross_margin_pct", v)}
            step={1}
          />
        </div>

        {/* Advanced / scenario fields — collapsible */}
        <div className="mt-4">
          <button
            onClick={() => setShowAdvanced((v) => !v)}
            className="flex items-center gap-2 text-sm text-[var(--text-muted)] hover:text-white transition-colors"
          >
            {showAdvanced ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            {showAdvanced ? "Hide" : "Show"} scenario inputs
            <span className="text-xs opacity-50">(optional — defaults to neutral baseline)</span>
          </button>

          {showAdvanced && (
            <div className="mt-4 grid md:grid-cols-2 lg:grid-cols-3 gap-3 border border-white/8 rounded-xl p-4 bg-black/10">
              <p className="col-span-full text-xs text-[var(--text-muted)] mb-1">
                These fields drive the scenario testing table. If you leave them at 0, the engine uses a neutral
                baseline and still produces readiness scores, gaps, and market recommendations.
              </p>
              <NumberInput
                label="Price Change Scenario"
                hint="Planned price change as decimal (0.10 = +10%)"
                value={form.price_change_pct}
                onChange={(v) => updateNumber("price_change_pct", v)}
                step={0.01}
              />
              <NumberInput
                label="GTM Efficiency Delta"
                hint="Expected improvement in sales efficiency (0.08 = 8%)"
                value={form.gtm_efficiency_delta}
                onChange={(v) => updateNumber("gtm_efficiency_delta", v)}
                step={0.01}
              />
              <NumberInput
                label="CAC Delta"
                hint="Change in customer acquisition cost (-0.05 = 5% reduction)"
                value={form.cac_delta}
                onChange={(v) => updateNumber("cac_delta", v)}
                step={0.01}
              />
              <NumberInput
                label="Hiring Plan Delta"
                hint="Planned headcount growth as decimal (0.10 = 10% growth)"
                value={form.hiring_plan_delta}
                onChange={(v) => updateNumber("hiring_plan_delta", v)}
                step={0.01}
              />
              <NumberInput
                label="Localization Readiness (0–1)"
                hint="How ready you are to expand to a new US region (1 = fully ready)"
                value={form.localization_readiness}
                onChange={(v) => updateNumber("localization_readiness", v)}
                step={0.05}
              />
            </div>
          )}
        </div>

        <div className="mt-5 flex items-center gap-3">
          <button
            onClick={runEngine}
            disabled={loading}
            className="rounded-xl border border-white/25 bg-white/10 px-5 py-2.5 text-sm font-semibold hover:bg-white/15 disabled:opacity-40"
          >
            {loading ? "Running..." : "Run Startup Readiness"}
          </button>
          {error && <p className="text-sm text-rose-300">{error}</p>}
        </div>
      </section>

      {result && (
        <>
          <section className="grid md:grid-cols-4 gap-3">
            <Stat label="Readiness Score" value={`${result.readiness_score}/100`} />
            <Stat label="Pitch-Dynamics Probability" value={`${Math.round(result.deal_probability * 100)}%`} />
            <Stat label="Company Stage" value={result.stage} />
            <Stat label="News Sentiment" value={result.news_signals.sentiment_hint} />
          </section>

          <section className="grid lg:grid-cols-3 gap-4">
            <ListCard title="Strengths" items={result.strengths} tone="emerald" />
            <ListCard title="Gaps" items={result.gaps} tone="rose" />
            <ListCard title="Recommendations" items={result.recommendations} tone="blue" />
          </section>

          <section className="rounded-2xl border border-white/12 bg-[var(--bg-surface)] p-5">
            <div className="flex flex-wrap gap-2 items-center justify-between">
              <h2 className="text-lg font-semibold">Evidence-Based Recommendation</h2>
              <div className="flex gap-2">
                <button onClick={handleSave} className="rounded-lg border border-white/20 px-3 py-1.5 text-xs">Save Analysis</button>
                <button onClick={handleExportMemo} className="rounded-lg border border-white/20 px-3 py-1.5 text-xs">Export IC Memo (PDF)</button>
                <button onClick={() => addToWatchlist(result.industry)} className="rounded-lg border border-white/20 px-3 py-1.5 text-xs">Add Industry Watchlist</button>
              </div>
            </div>
            <p className="mt-2 text-sm text-[var(--text-muted)]">Score {result.recommendation.score} • Confidence {result.recommendation.confidence_level}</p>
            <div className="mt-3 grid md:grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-xs uppercase tracking-[0.12em] text-[var(--text-muted)]">Top 5 Drivers</p>
                <ul className="mt-2 space-y-1">
                  {result.recommendation.top_5_drivers.map((d) => <li key={d.driver}>- {d.driver}: {d.impact}</li>)}
                </ul>
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.12em] text-[var(--text-muted)]">Citations</p>
                <ul className="mt-2 space-y-1 text-[var(--text-muted)]">
                  {result.citations.map((c) => <li key={`${c.source}-${c.industry}`}>- {c.source} ({c.industry || "US"})</li>)}
                </ul>
              </div>
            </div>
          </section>

          <section className="rounded-2xl border border-white/12 bg-[var(--bg-surface)] p-5">
            <h2 className="text-lg font-semibold">What To Improve Before Expansion</h2>
            <ul className="mt-3 space-y-2 text-sm">
              {result.improvement_checklist.map((item) => (
                <li key={item.item} className="flex items-center justify-between border border-white/10 rounded-lg px-3 py-2">
                  <span>{item.item}</span>
                  <span className={item.status === "done" ? "text-emerald-300" : "text-amber-300"}>{item.status}</span>
                </li>
              ))}
            </ul>
          </section>

          <section className="rounded-2xl border border-white/12 bg-[var(--bg-surface)] p-5">
            <h2 className="text-lg font-semibold">Scenario Testing</h2>
            <div className="mt-3 overflow-x-auto">
              <table className="min-w-full text-sm matrix-table">
                <thead className="text-[var(--text-muted)]">
                  <tr>
                    <th className="text-left py-2 pr-4">Scenario</th>
                    <th className="text-left py-2 pr-4">Input Delta</th>
                    <th className="text-left py-2 pr-4">Projected Score</th>
                    <th className="text-left py-2 pr-4">Confidence</th>
                  </tr>
                </thead>
                <tbody>
                  {result.scenario_testing.map((item) => (
                    <tr key={item.scenario} className="border-t border-white/10">
                      <td className="py-3 pr-4">{item.scenario}</td>
                      <td className="py-3 pr-4">{item.input_delta}</td>
                      <td className="py-3 pr-4">{item.projected_readiness_score}</td>
                      <td className="py-3 pr-4">{item.confidence}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="rounded-2xl border border-white/12 bg-[var(--bg-surface)] p-5">
            <h2 className="text-lg font-semibold">US Market Recommendations</h2>
            <p className="mt-1 text-sm text-[var(--text-muted)]">{result.news_signals.summary}</p>
            <div className="mt-3 overflow-x-auto">
              <table className="min-w-full text-sm matrix-table">
                <thead className="text-[var(--text-muted)]">
                  <tr>
                    <th className="text-left py-2 pr-4">Market</th>
                    <th className="text-left py-2 pr-4">Region</th>
                    <th className="text-left py-2 pr-4">Fit Score</th>
                    <th className="text-left py-2 pr-4">Confidence</th>
                    <th className="text-left py-2 pr-4">Rationale</th>
                  </tr>
                </thead>
                <tbody>
                  {result.us_market_recommendations.map((item) => (
                    <tr key={`${item.market}-${item.region}`} className="border-t border-white/10">
                      <td className="py-3 pr-4">{item.market}</td>
                      <td className="py-3 pr-4">{item.region}</td>
                      <td className="py-3 pr-4">{item.fit_score}</td>
                      <td className="py-3 pr-4">{item.confidence}%</td>
                      <td className="py-3 pr-4 text-[var(--text-muted)]">{item.rationale}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-white/12 bg-black/20 px-4 py-4">
      <p className="text-xs uppercase tracking-[0.12em] text-[var(--text-muted)]">{label}</p>
      <p className="mt-2 text-2xl font-semibold">{value}</p>
    </div>
  );
}

function Input({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}) {
  return (
    <label className="space-y-2">
      <span className="text-xs uppercase tracking-[0.12em] text-[var(--text-muted)]">{label}</span>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded-xl border border-white/15 bg-black/25 px-3 py-2.5 text-sm"
      />
    </label>
  );
}

function NumberInput({
  label,
  hint,
  value,
  onChange,
  step = 1000,
}: {
  label: string;
  hint?: string;
  value: number;
  onChange: (value: string) => void;
  step?: number;
}) {
  return (
    <label className="space-y-2">
      <span className="text-xs uppercase tracking-[0.12em] text-[var(--text-muted)]">{label}</span>
      {hint && <span className="block text-[10px] text-white/30 -mt-1">{hint}</span>}
      <input
        type="number"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        step={step}
        className="w-full rounded-xl border border-white/15 bg-black/25 px-3 py-2.5 text-sm"
      />
    </label>
  );
}

function ListCard({
  title,
  items,
  tone,
}: {
  title: string;
  items: string[];
  tone: "emerald" | "rose" | "blue";
}) {
  const toneClass =
    tone === "emerald" ? "text-emerald-200/90" : tone === "rose" ? "text-rose-200/90" : "text-blue-200/90";
  return (
    <div className="rounded-2xl border border-white/12 bg-[var(--bg-surface)] p-5">
      <h2 className="text-lg font-semibold">{title}</h2>
      <ul className={`mt-3 space-y-2 text-sm ${toneClass}`}>
        {(items.length > 0 ? items : ["No major signals yet."]).map((item) => (
          <li key={item}>- {item}</li>
        ))}
      </ul>
    </div>
  );
}
