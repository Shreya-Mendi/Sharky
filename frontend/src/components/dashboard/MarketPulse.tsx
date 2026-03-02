"use client";

import { Sparkles } from "lucide-react";
import type { Industry } from "@/lib/api";

interface Props {
  stats: any;
  industries: Industry[];
}

export default function MarketPulse({ stats, industries }: Props) {
  const totalPitches = stats?.total_pitches ?? 0;
  const avgRevenue = stats?.avg_revenue_mentioned ?? 0;
  const totalEpisodes = stats?.total_episodes ?? 0;

  const topIndustry = industries.length > 0
    ? [...industries].sort((a, b) => b.deal_count - a.deal_count)[0]
    : null;

  const sentences = [
    `Across ${totalPitches.toLocaleString()} analyzed deals, the average cited revenue is $${(avgRevenue / 1000).toFixed(0)}K.`,
    totalEpisodes > 0
      ? `Data spans ${totalEpisodes} episodes across ${stats?.seasons?.length ?? 0} seasons of Shark Tank.`
      : null,
    topIndustry
      ? `${topIndustry.industry} leads with ${topIndustry.deal_count} deals and a ${(topIndustry.success_rate * 100).toFixed(0)}% success rate.`
      : null,
  ].filter(Boolean);

  return (
    <div className="glass p-5">
      <div className="flex items-center gap-2 mb-4">
        <Sparkles size={16} className="text-amber-400" />
        <h3 className="text-sm font-semibold text-white/50">Market Pulse</h3>
      </div>
      <div className="space-y-3">
        {sentences.map((sentence, i) => (
          <p key={i} className="text-sm text-white/70 leading-relaxed">
            {sentence}
          </p>
        ))}
      </div>
    </div>
  );
}
