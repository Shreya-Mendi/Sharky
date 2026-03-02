"use client";

import Link from "next/link";
import { SlidersHorizontal, Bot, Search, TrendingUp } from "lucide-react";
import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";

interface QuickAction {
  label: string;
  href: string;
  icon: LucideIcon;
  color: string;
}

const actions: QuickAction[] = [
  { label: "Simulate a Deal", href: "/app/simulator", icon: SlidersHorizontal, color: "text-blue-400 bg-blue-500/15" },
  { label: "Research a Market", href: "/app/agent", icon: Bot, color: "text-emerald-400 bg-emerald-500/15" },
  { label: "Browse Deals", href: "/app/deals", icon: Search, color: "text-amber-400 bg-amber-500/15" },
  { label: "View Trends", href: "/app/market", icon: TrendingUp, color: "text-purple-400 bg-purple-500/15" },
];

export default function QuickActions() {
  return (
    <div className="glass p-5">
      <h3 className="text-sm font-semibold text-white/50 mb-4">Quick Actions</h3>
      <div className="grid grid-cols-2 gap-3">
        {actions.map((action, i) => (
          <motion.div
            key={action.href}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
          >
            <Link
              href={action.href}
              className="flex flex-col items-center gap-2 p-4 rounded-xl border border-white/8 hover:border-white/20 hover:bg-white/5 transition-all text-center"
            >
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${action.color}`}>
                <action.icon size={20} />
              </div>
              <span className="text-xs text-white/70">{action.label}</span>
            </Link>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
