"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import { BarChart3, Bot, Home, Zap } from "lucide-react";

const links = [
  { href: "/", label: "Home", icon: Home },
  { href: "/simulator", label: "Simulator", icon: Zap },
  { href: "/hub", label: "Intelligence Hub", icon: BarChart3 },
  { href: "/chat", label: "SharkBot", icon: Bot },
];

export default function Navbar() {
  const pathname = usePathname();

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 glass border-b border-white/10">
      <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          <span className="text-xl font-bold bg-gradient-to-r from-blue-400 to-blue-600 bg-clip-text text-transparent">
            SharkTank AI
          </span>
        </Link>

        <div className="hidden md:flex items-center gap-1">
          {links.map(({ href, label, icon: Icon }) => {
            const isActive = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                className={`relative px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2 ${
                  isActive ? "text-white" : "text-slate-400 hover:text-white"
                }`}
              >
                <Icon size={16} />
                {label}
                {isActive && (
                  <motion.div
                    layoutId="navbar-indicator"
                    className="absolute inset-0 bg-white/10 rounded-lg"
                    transition={{ type: "spring", duration: 0.5 }}
                  />
                )}
              </Link>
            );
          })}
        </div>

        <Link
          href="/simulator"
          className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors glow-blue"
        >
          Try Simulator
        </Link>
      </div>
    </nav>
  );
}
