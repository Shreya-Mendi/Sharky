"use client";

import { motion } from "framer-motion";
import { LucideIcon } from "lucide-react";

interface Props {
  label: string;
  value: string;
  change?: string;
  changeType?: "up" | "down" | "neutral";
  icon: LucideIcon;
  color: string;
}

export default function KPICard({ label, value, change, changeType = "neutral", icon: Icon, color }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="kpi-card"
    >
      <div className="flex items-start justify-between mb-3">
        <span className="text-sm text-white/50">{label}</span>
        <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${color}`}>
          <Icon size={18} />
        </div>
      </div>
      <div className="text-2xl font-bold">{value}</div>
      {change && (
        <span className={`text-xs mt-1 ${
          changeType === "up" ? "text-emerald-400" : changeType === "down" ? "text-rose-400" : "text-white/40"
        }`}>
          {change}
        </span>
      )}
    </motion.div>
  );
}
