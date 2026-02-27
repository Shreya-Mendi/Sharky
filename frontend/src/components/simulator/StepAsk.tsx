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
