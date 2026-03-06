"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard,
  TrendingUp,
  ClipboardCheck,
  Globe2,
  Bot,
  Settings,
  ChevronLeft,
  ChevronRight,
  Compass,
} from "lucide-react";

const NAV_ITEMS = [
  { href: "/app", icon: LayoutDashboard, label: "Engine Hub" },
  { href: "/app/market", icon: TrendingUp, label: "Industry Intelligence" },
  { href: "/app/simulator", icon: ClipboardCheck, label: "Startup Readiness" },
  { href: "/app/deals", icon: Globe2, label: "Market Fit Recommender" },
  { href: "/app/agent", icon: Bot, label: "Research Copilot" },
  { href: "/app/settings", icon: Settings, label: "Settings" },
];

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const pathname = usePathname();

  const isActive = (href: string) => {
    if (href === "/app") return pathname === "/app";
    return pathname.startsWith(href);
  };

  return (
    <aside
      className={`sidebar fixed left-0 top-0 h-screen z-40 hidden md:flex flex-col transition-all duration-300 ${
        collapsed ? "w-16" : "w-60"
      }`}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 h-16 border-b border-white/5">
        <div className="w-8 h-8 rounded-lg border border-white/20 bg-white/5 flex items-center justify-center flex-shrink-0">
          <Compass size={16} className="text-[var(--accent-blue)]" />
        </div>
        <AnimatePresence>
          {!collapsed && (
            <motion.span
              initial={{ opacity: 0, width: 0 }}
              animate={{ opacity: 1, width: "auto" }}
              exit={{ opacity: 0, width: 0 }}
              className="font-semibold tracking-wide text-lg whitespace-nowrap overflow-hidden"
            >
              DealScope
            </motion.span>
          )}
        </AnimatePresence>
      </div>

      {/* Nav Items */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto custom-scrollbar">
        {NAV_ITEMS.map(({ href, icon: Icon, label }) => (
          <Link
            key={href}
            href={href}
            className={`sidebar-item ${isActive(href) ? "active" : ""}`}
            title={collapsed ? label : undefined}
          >
            <Icon size={20} className="flex-shrink-0" />
            <AnimatePresence>
              {!collapsed && (
                <motion.span
                  initial={{ opacity: 0, width: 0 }}
                  animate={{ opacity: 1, width: "auto" }}
                  exit={{ opacity: 0, width: 0 }}
                  className="whitespace-nowrap overflow-hidden"
                >
                  {label}
                </motion.span>
              )}
            </AnimatePresence>
          </Link>
        ))}
      </nav>

      {/* Collapse toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center justify-center h-12 border-t border-white/5 text-white/40 hover:text-white/70 transition-colors"
      >
        {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
      </button>
    </aside>
  );
}
