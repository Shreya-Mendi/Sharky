"use client";

import { Sparkles } from "lucide-react";
import type { Industry } from "@/lib/api";

interface Props {
  industry: Industry;
  allIndustries: Industry[];
}

export default function IndustryBrief({ industry, allIndustries }: Props) {
  const totalDeals = allIndustries.reduce((s, i) => s + i.deal_count, 0);
  const totalPitches = allIndustries.reduce((s, i) => s + i.pitch_count, 0);
  const avgSuccessRate =
    allIndustries.length > 0
      ? allIndustries.reduce((s, i) => s + i.success_rate, 0) / allIndustries.length
      : 0;
  const avgRevenue =
    allIndustries.length > 0
      ? allIndustries.reduce((s, i) => s + i.avg_revenue, 0) / allIndustries.length
      : 0;

  function formatCurrency(value: number): string {
    if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
    if (value >= 1_000) return `$${(value / 1_000).toFixed(0)}K`;
    return `$${value.toFixed(0)}`;
  }

  function generateBrief(): string[] {
    if (industry.industry === "All Industries") {
      return [
        `Across all industries, there are ${totalDeals.toLocaleString()} deals from ${totalPitches.toLocaleString()} total pitches spanning ${allIndustries.length} industry categories.`,
        `The overall average success rate is ${(avgSuccessRate * 100).toFixed(1)}%, with an average revenue of ${formatCurrency(avgRevenue)} per company at the time of pitching.`,
        `Use the industry selector above to drill into specific sectors and compare their performance against these market-wide benchmarks.`,
      ];
    }

    const pctOfTotal = totalDeals > 0 ? ((industry.deal_count / totalDeals) * 100).toFixed(1) : "0";
    const successComparison =
      industry.success_rate > avgSuccessRate
        ? `${((industry.success_rate - avgSuccessRate) * 100).toFixed(1)} percentage points above`
        : industry.success_rate < avgSuccessRate
          ? `${((avgSuccessRate - industry.success_rate) * 100).toFixed(1)} percentage points below`
          : "exactly at";
    const revenueComparison =
      industry.avg_revenue > avgRevenue
        ? `${((industry.avg_revenue / avgRevenue - 1) * 100).toFixed(0)}% higher than`
        : industry.avg_revenue < avgRevenue
          ? `${((1 - industry.avg_revenue / avgRevenue) * 100).toFixed(0)}% lower than`
          : "equal to";

    return [
      `The ${industry.industry} sector represents ${industry.deal_count.toLocaleString()} deals (${pctOfTotal}% of total), drawn from ${industry.pitch_count.toLocaleString()} pitches.`,
      `Its success rate of ${(industry.success_rate * 100).toFixed(1)}% is ${successComparison} the market average.`,
      `Average revenue at pitch time is ${formatCurrency(industry.avg_revenue)}, which is ${revenueComparison} the cross-industry average of ${formatCurrency(avgRevenue)}.`,
      `Companies in this sector typically ask for ${formatCurrency(industry.avg_ask)} in funding.`,
    ];
  }

  const sentences = generateBrief();

  return (
    <div className="glass p-6">
      <h3 className="text-sm font-semibold text-white/60 uppercase tracking-wide mb-4 flex items-center gap-2">
        <Sparkles size={16} className="text-amber-400" />
        AI Industry Brief
      </h3>
      <div className="space-y-3">
        {sentences.map((sentence, i) => (
          <p key={i} className="text-sm text-slate-300 leading-relaxed">
            {sentence}
          </p>
        ))}
      </div>
    </div>
  );
}
