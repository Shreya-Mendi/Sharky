"use client";

import { BarChart3, DollarSign, TrendingUp, Mic } from "lucide-react";
import type { Industry } from "@/lib/api";

interface Props {
  industry: Industry;
}

function formatCurrency(value: number): string {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `$${(value / 1_000).toFixed(0)}K`;
  return `$${value.toFixed(0)}`;
}

export default function IndustryMetrics({ industry }: Props) {
  const metrics = [
    {
      label: "Deal Count",
      value: industry.deal_count.toLocaleString(),
      icon: BarChart3,
      color: "text-blue-400",
    },
    {
      label: "Avg Revenue",
      value: formatCurrency(industry.avg_revenue),
      icon: DollarSign,
      color: "text-emerald-400",
    },
    {
      label: "Success Rate",
      value: `${(industry.success_rate * 100).toFixed(1)}%`,
      icon: TrendingUp,
      color: "text-amber-400",
    },
    {
      label: "Pitch Count",
      value: industry.pitch_count.toLocaleString(),
      icon: Mic,
      color: "text-rose-400",
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {metrics.map((m) => (
        <div key={m.label} className="kpi-card">
          <div className="flex items-center gap-2 mb-2">
            <m.icon size={16} className={m.color} />
            <span className="text-xs text-white/40 uppercase tracking-wide">{m.label}</span>
          </div>
          <div className="text-2xl font-bold">{m.value}</div>
        </div>
      ))}
    </div>
  );
}
