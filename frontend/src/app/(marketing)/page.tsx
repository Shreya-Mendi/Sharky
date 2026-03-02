"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import {
  ArrowRight,
  TrendingUp,
  SlidersHorizontal,
  Bot,
  Search,
  Cpu,
  BarChart3,
} from "lucide-react";
import AnimatedCounter from "@/components/ui/AnimatedCounter";

const featureCards = [
  {
    icon: TrendingUp,
    color: "text-blue-400",
    borderColor: "border-blue-500/30",
    glowClass: "glow-blue",
    title: "Market Analysis",
    description:
      "Deep-dive into industry trends, deal success rates, and valuation benchmarks across 10+ sectors.",
  },
  {
    icon: SlidersHorizontal,
    color: "text-amber-400",
    borderColor: "border-amber-500/30",
    glowClass: "glow-amber",
    title: "Deal Simulator",
    description:
      "Test your pitch parameters against real historical outcomes and get instant probability scores.",
  },
  {
    icon: Bot,
    color: "text-emerald-400",
    borderColor: "border-emerald-500/30",
    glowClass: "",
    title: "Research Agent",
    description:
      "AI agent that autonomously researches market patterns and generates comprehensive reports.",
  },
];

const steps = [
  {
    icon: Search,
    number: "01",
    title: "Choose Your Market",
    description:
      "Select from 10+ industry sectors or search for specific deal patterns.",
  },
  {
    icon: Cpu,
    number: "02",
    title: "AI Analyzes 741+ Deals",
    description:
      "Our engine cross-references revenue, valuations, sentiment, and negotiation patterns.",
  },
  {
    icon: BarChart3,
    number: "03",
    title: "Get Actionable Insights",
    description:
      "Receive data-backed recommendations, risk assessments, and competitive benchmarks.",
  },
];

const seasonData = [
  { season: "S1", height: 30, deals: 21 },
  { season: "S2", height: 35, deals: 24 },
  { season: "S3", height: 40, deals: 29 },
  { season: "S4", height: 45, deals: 32 },
  { season: "S5", height: 55, deals: 38 },
  { season: "S6", height: 60, deals: 42 },
  { season: "S7", height: 50, deals: 35 },
  { season: "S8", height: 65, deals: 44 },
  { season: "S9", height: 70, deals: 48 },
  { season: "S10", height: 75, deals: 51 },
  { season: "S11", height: 68, deals: 46 },
  { season: "S12", height: 80, deals: 55 },
  { season: "S13", height: 85, deals: 58 },
  { season: "S14", height: 90, deals: 62 },
  { season: "S15", height: 95, deals: 66 },
];

export default function HomePage() {
  return (
    <div className="min-h-screen bg-[#0a0a0f]">
      {/* ─── Hero ─── */}
      <section className="relative min-h-screen flex flex-col items-center justify-center px-6 overflow-hidden">
        {/* Radial gradient background */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_60%_at_50%_-10%,rgba(59,130,246,0.15),rgba(124,58,237,0.08),transparent_70%)]" />

        <motion.div
          className="text-center max-w-4xl relative z-10"
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight bg-gradient-to-r from-white via-blue-100 to-blue-300 bg-clip-text text-transparent">
            Turn Data Into Deal-Ready Intelligence
          </h1>
          <p className="text-lg md:text-xl text-slate-400 mb-12 max-w-2xl mx-auto leading-relaxed">
            AI-powered market analysis from 741+ real venture pitches. Predict
            outcomes, benchmark deals, and research markets — all in one
            platform.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/app"
              className="bg-blue-600 hover:bg-blue-500 text-white px-8 py-3.5 rounded-xl text-lg font-semibold transition-all glow-blue flex items-center justify-center gap-2"
            >
              Start Analyzing <ArrowRight size={20} />
            </Link>
            <Link
              href="#how-it-works"
              className="border border-white/20 hover:border-white/40 text-white px-8 py-3.5 rounded-xl text-lg font-semibold transition-all hover:bg-white/5"
            >
              See How It Works
            </Link>
          </div>
        </motion.div>
      </section>

      {/* ─── Stats Strip ─── */}
      <section id="stats" className="py-16">
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="max-w-5xl mx-auto px-6"
        >
          <div className="glass py-10 px-8">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
              <div className="flex flex-col items-center">
                <span className="text-3xl md:text-4xl font-bold text-white">
                  <AnimatedCounter target={741} suffix="+" />
                </span>
                <span className="text-sm text-slate-500 mt-2">
                  Deals Analyzed
                </span>
              </div>
              <div className="flex flex-col items-center">
                <span className="text-3xl md:text-4xl font-bold text-white">
                  <AnimatedCounter target={15} />
                </span>
                <span className="text-sm text-slate-500 mt-2">
                  Seasons of Data
                </span>
              </div>
              <div className="flex flex-col items-center">
                <span className="text-3xl md:text-4xl font-bold text-white">
                  <AnimatedCounter target={2} prefix="$" suffix=".4B" />
                </span>
                <span className="text-sm text-slate-500 mt-2">
                  Deal Value Tracked
                </span>
              </div>
              <div className="flex flex-col items-center">
                <span className="text-3xl md:text-4xl font-bold text-white">
                  <AnimatedCounter target={292} />
                </span>
                <span className="text-sm text-slate-500 mt-2">
                  Episodes Parsed
                </span>
              </div>
            </div>
          </div>
        </motion.div>
      </section>

      {/* ─── Three-Feature Showcase ─── */}
      <section id="features" className="py-24 px-6">
        <div className="max-w-7xl mx-auto">
          <motion.h2
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-3xl md:text-4xl font-bold text-center mb-16"
          >
            Everything You Need for Deal Intelligence
          </motion.h2>

          <div className="grid md:grid-cols-3 gap-8">
            {featureCards.map((card, i) => (
              <motion.div
                key={card.title}
                initial={{ opacity: 0, y: 40 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.15, duration: 0.6 }}
                className={`glass glass-hover p-8 ${card.borderColor} border cursor-default`}
              >
                <div
                  className={`w-12 h-12 rounded-xl flex items-center justify-center mb-5 ${
                    card.color === "text-blue-400"
                      ? "bg-blue-500/10"
                      : card.color === "text-amber-400"
                        ? "bg-amber-500/10"
                        : "bg-emerald-500/10"
                  }`}
                >
                  <card.icon className={card.color} size={24} />
                </div>
                <h3 className="text-xl font-bold mb-3">{card.title}</h3>
                <p className="text-slate-400 leading-relaxed">
                  {card.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── How It Works ─── */}
      <section id="how-it-works" className="py-32 px-6">
        <div className="max-w-7xl mx-auto">
          <motion.h2
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-3xl md:text-4xl font-bold text-center mb-16"
          >
            Three Steps to Smarter Decisions
          </motion.h2>

          <div className="grid md:grid-cols-3 gap-8">
            {steps.map((step, i) => (
              <motion.div
                key={step.number}
                initial={{ opacity: 0, y: 40 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.15, duration: 0.6 }}
                className="relative text-center md:text-left"
              >
                <div className="flex flex-col items-center md:items-start">
                  <span className="text-5xl font-black text-white/5 mb-4">
                    {step.number}
                  </span>
                  <div className="w-12 h-12 rounded-xl bg-blue-500/10 flex items-center justify-center mb-4">
                    <step.icon className="text-blue-400" size={24} />
                  </div>
                  <h3 className="text-xl font-bold mb-3">{step.title}</h3>
                  <p className="text-slate-400 leading-relaxed">
                    {step.description}
                  </p>
                </div>

                {/* Connector line between steps (hidden on last) */}
                {i < steps.length - 1 && (
                  <div className="hidden md:block absolute top-16 -right-4 w-8">
                    <div className="border-t border-dashed border-white/10 w-full" />
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Dashboard Preview ─── */}
      <section className="py-24 px-6">
        <div className="max-w-7xl mx-auto">
          <motion.h2
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-3xl md:text-4xl font-bold text-center mb-16"
          >
            Your Command Center for Deal Intelligence
          </motion.h2>

          <motion.div
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.7 }}
            className="max-w-5xl mx-auto"
          >
            <div className="glass p-8 md:p-10">
              {/* KPI Row */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                <div className="bg-white/[0.03] border border-white/[0.06] rounded-xl p-4 text-center">
                  <p className="text-2xl font-bold text-white">741</p>
                  <p className="text-xs text-slate-500 mt-1">Deals</p>
                </div>
                <div className="bg-white/[0.03] border border-white/[0.06] rounded-xl p-4 text-center">
                  <p className="text-2xl font-bold text-emerald-400">68%</p>
                  <p className="text-xs text-slate-500 mt-1">Success</p>
                </div>
                <div className="bg-white/[0.03] border border-white/[0.06] rounded-xl p-4 text-center">
                  <p className="text-2xl font-bold text-blue-400">$2.4B</p>
                  <p className="text-xs text-slate-500 mt-1">Tracked</p>
                </div>
                <div className="bg-white/[0.03] border border-white/[0.06] rounded-xl p-4 text-center">
                  <p className="text-2xl font-bold text-amber-400">15</p>
                  <p className="text-xs text-slate-500 mt-1">Seasons</p>
                </div>
              </div>

              {/* Chart Header */}
              <div className="flex items-center justify-between mb-4">
                <div>
                  <p className="text-sm font-semibold text-white">
                    Deals Closed by Season
                  </p>
                  <p className="text-xs text-slate-500">
                    Historical deal volume across all 15 seasons
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-full bg-blue-500" />
                  <span className="text-xs text-slate-500">Deals Closed</span>
                </div>
              </div>

              {/* Bar Chart Mockup */}
              <div className="bg-white/[0.02] rounded-xl p-6 border border-white/[0.04]">
                <div className="flex items-end justify-between gap-2 h-48">
                  {seasonData.map((s) => (
                    <div
                      key={s.season}
                      className="flex flex-col items-center flex-1 gap-1"
                    >
                      <span className="text-[10px] text-slate-500">
                        {s.deals}
                      </span>
                      <div
                        className="w-full rounded-t-md bg-gradient-to-t from-blue-600 to-blue-400 transition-all"
                        style={{ height: `${s.height}%` }}
                      />
                      <span className="text-[10px] text-slate-600 mt-1">
                        {s.season}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* ─── CTA Footer ─── */}
      <section className="py-32 px-6">
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center max-w-2xl mx-auto"
        >
          <h2 className="text-3xl md:text-4xl font-bold mb-6">
            Ready to make data-driven decisions?
          </h2>
          <Link
            href="/app"
            className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-10 py-4 rounded-xl text-lg font-semibold transition-all glow-blue"
          >
            Launch DealScope <ArrowRight size={20} />
          </Link>
        </motion.div>
      </section>
    </div>
  );
}
