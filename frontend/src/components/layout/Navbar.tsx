"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Compass } from "lucide-react";
import ThemeToggle from "@/components/theme/ThemeToggle";

const links = [
  { href: "#features", label: "Features" },
  { href: "#how-it-works", label: "How It Works" },
  { href: "/pricing", label: "Pricing" },
];

export default function Navbar() {
  return (
    <motion.nav
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      className="fixed top-0 w-full z-50 border-b border-white/10 bg-[#111212]/85 backdrop-blur-md"
    >
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg border border-white/20 bg-white/5 flex items-center justify-center">
            <Compass size={16} className="text-[var(--accent-blue)]" />
          </div>
          <span className="font-semibold text-lg tracking-wide">DealScope</span>
        </Link>

        <div className="hidden md:flex items-center gap-8">
          {links.map(({ href, label }) => (
            href.startsWith("/") ? (
              <Link
                key={href}
                href={href}
                className="text-sm text-[var(--text-muted)] hover:text-white transition-colors"
              >
                {label}
              </Link>
            ) : (
              <a
                key={href}
                href={href}
                className="text-sm text-[var(--text-muted)] hover:text-white transition-colors"
              >
                {label}
              </a>
            )
          ))}
        </div>

        <div className="flex items-center gap-3">
          <ThemeToggle />
          <Link
            href="/app"
            className="border border-white/20 bg-white/5 hover:bg-white/10 text-white px-6 py-2 rounded-lg text-sm font-semibold transition-all"
          >
            Launch App
          </Link>
        </div>
      </div>
    </motion.nav>
  );
}
