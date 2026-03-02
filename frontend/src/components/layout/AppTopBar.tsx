"use client";

import { usePathname } from "next/navigation";
import { Bell, Search } from "lucide-react";

const PAGE_TITLES: Record<string, string> = {
  "/app": "Dashboard",
  "/app/market": "Market Analysis",
  "/app/simulator": "Deal Simulator",
  "/app/agent": "Research Agent",
  "/app/deals": "Deal Explorer",
};

export default function AppTopBar() {
  const pathname = usePathname();
  const title = PAGE_TITLES[pathname] || "DealScope";

  return (
    <header className="h-16 border-b border-white/5 flex items-center justify-between px-6 bg-[var(--bg-primary)]/80 backdrop-blur-sm sticky top-0 z-30">
      <h1 className="text-lg font-semibold">{title}</h1>
      <div className="flex items-center gap-4">
        <div className="relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-white/30" />
          <input
            type="text"
            placeholder="Search deals..."
            className="bg-white/5 border border-white/10 rounded-lg pl-9 pr-4 py-2 text-sm text-white placeholder:text-white/30 focus:outline-none focus:border-blue-500/50 w-64"
          />
        </div>
        <button className="w-9 h-9 rounded-lg bg-white/5 flex items-center justify-center text-white/40 hover:text-white/70 transition-colors">
          <Bell size={18} />
        </button>
      </div>
    </header>
  );
}
