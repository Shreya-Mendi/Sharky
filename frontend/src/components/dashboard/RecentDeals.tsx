"use client";

import { motion } from "framer-motion";
import type { Deal } from "@/lib/api";

interface Props {
  deals: Deal[];
}

function formatRevenue(revenue: number): string {
  if (revenue >= 1_000_000) return `$${(revenue / 1_000_000).toFixed(1)}M`;
  if (revenue >= 1_000) return `$${(revenue / 1_000).toFixed(0)}K`;
  return `$${revenue.toLocaleString()}`;
}

export default function RecentDeals({ deals }: Props) {
  if (deals.length === 0) {
    return (
      <div className="glass p-5">
        <h3 className="text-sm font-semibold text-white/50 mb-4">Recent Deals</h3>
        <p className="text-sm text-white/30">No deals to display.</p>
      </div>
    );
  }

  return (
    <div className="glass p-5">
      <h3 className="text-sm font-semibold text-white/50 mb-4">Recent Deals</h3>
      <div className="space-y-2">
        {deals.map((deal, i) => (
          <motion.div
            key={`${deal.episode}-${deal.company_name}`}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.05 }}
            className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-white/5 transition-colors"
          >
            <div className="flex items-center gap-3 min-w-0">
              <div className="min-w-0">
                <div className="text-sm font-medium truncate">{deal.company_name}</div>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className="text-xs px-2 py-0.5 rounded-full bg-white/10 text-white/50 truncate">
                    {deal.industry}
                  </span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3 flex-shrink-0">
              <span className="text-xs text-white/40">{formatRevenue(deal.revenue)}</span>
              <span
                className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                  deal.has_deal
                    ? "bg-emerald-500/20 text-emerald-400"
                    : "bg-white/10 text-white/40"
                }`}
              >
                {deal.has_deal ? "Deal" : "No Deal"}
              </span>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
