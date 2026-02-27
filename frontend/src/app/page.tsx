"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowRight, BarChart3, Brain, TrendingUp } from "lucide-react";
import AnimatedCounter from "@/components/ui/AnimatedCounter";
import DealScoreGauge from "@/components/ui/DealScoreGauge";

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.15, duration: 0.6 },
  }),
};

const intelligenceLayers = [
  {
    icon: BarChart3,
    order: "1st Order",
    title: "What Happened",
    example: "Pitch X asked $500K for 10%, got deal from Cuban at 20%",
    color: "text-blue-400",
    borderColor: "border-blue-500/30",
  },
  {
    icon: Brain,
    order: "2nd Order",
    title: "What Patterns Emerge",
    example: "Sharks who express skepticism but ask follow-up questions close 73% of the time",
    color: "text-amber-400",
    borderColor: "border-amber-500/30",
  },
  {
    icon: TrendingUp,
    order: "3rd Order",
    title: "What This Predicts",
    example: "A food-tech startup with $800K revenue should pitch to Lori and expect a 3x equity counter",
    color: "text-emerald-400",
    borderColor: "border-emerald-500/30",
  },
];

export default function HomePage() {
  const [demoAsk, setDemoAsk] = useState(250000);
  const [demoRevenue, setDemoRevenue] = useState(500000);

  const demoScore = Math.max(1, Math.min(10, Math.round(
    (Math.min(demoRevenue / 1_000_000, 1) * 4 +
    Math.max(0, 1 - (demoAsk / 0.1) / 10_000_000) * 3 +
    0.5 * 3)
  )));

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="min-h-screen flex flex-col items-center justify-center px-6 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-blue-950/20 via-transparent to-transparent" />

        <motion.div
          className="text-center max-w-4xl relative z-10"
          initial="hidden"
          animate="visible"
        >
          <motion.h1
            variants={fadeUp}
            custom={0}
            className="text-5xl md:text-7xl font-bold mb-6 bg-gradient-to-r from-white via-blue-100 to-blue-300 bg-clip-text text-transparent"
          >
            Know Your Odds Before You Enter the Tank
          </motion.h1>
          <motion.p
            variants={fadeUp}
            custom={1}
            className="text-xl text-slate-400 mb-10"
          >
            AI-powered pitch analysis across 15 seasons of Shark Tank data
          </motion.p>

          <motion.div variants={fadeUp} custom={2} className="flex gap-4 justify-center mb-16">
            <Link
              href="/simulator"
              className="bg-blue-600 hover:bg-blue-500 text-white px-8 py-3 rounded-xl text-lg font-semibold transition-all glow-blue flex items-center gap-2"
            >
              Simulate Your Pitch <ArrowRight size={20} />
            </Link>
            <Link
              href="/hub"
              className="border border-white/20 hover:border-white/40 text-white px-8 py-3 rounded-xl text-lg font-semibold transition-all"
            >
              Explore the Data
            </Link>
          </motion.div>

          {/* Animated Stats */}
          <motion.div variants={fadeUp} custom={3} className="flex gap-12 justify-center text-center">
            {[
              { target: 292, suffix: "", label: "Episodes Analyzed" },
              { target: 1200, suffix: "+", label: "Pitches Parsed" },
              { target: 2, prefix: "$", suffix: ".4B", label: "In Deals Tracked" },
            ].map(({ target, prefix, suffix, label }) => (
              <div key={label} className="flex flex-col">
                <span className="text-3xl font-bold text-white">
                  <AnimatedCounter target={target} prefix={prefix} suffix={suffix} />
                </span>
                <span className="text-sm text-slate-500 mt-1">{label}</span>
              </div>
            ))}
          </motion.div>
        </motion.div>
      </section>

      {/* Intelligence Layers */}
      <section className="py-24 px-6">
        <div className="max-w-6xl mx-auto">
          <motion.h2
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-3xl font-bold text-center mb-16"
          >
            Three Layers of Intelligence
          </motion.h2>

          <div className="grid md:grid-cols-3 gap-8">
            {intelligenceLayers.map((layer, i) => (
              <motion.div
                key={layer.order}
                initial={{ opacity: 0, y: 40 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.2, duration: 0.6 }}
                className={`glass p-8 ${layer.borderColor} border`}
              >
                <layer.icon className={`${layer.color} mb-4`} size={32} />
                <span className={`text-sm font-semibold ${layer.color}`}>{layer.order}</span>
                <h3 className="text-xl font-bold mt-1 mb-4">{layer.title}</h3>
                <p className="text-slate-400 text-sm italic">{layer.example}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Live Demo Strip */}
      <section className="py-24 px-6 border-t border-white/5">
        <div className="max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="glass p-10"
          >
            <h2 className="text-2xl font-bold mb-2">Try It Now</h2>
            <p className="text-slate-400 mb-8">Drag the sliders and watch the deal score update in real time.</p>

            <div className="grid md:grid-cols-3 gap-8 items-center">
              <div>
                <label className="text-sm text-slate-400 block mb-2">Ask Amount</label>
                <input
                  type="range"
                  min={10000}
                  max={5000000}
                  step={10000}
                  value={demoAsk}
                  onChange={(e) => setDemoAsk(Number(e.target.value))}
                  className="w-full accent-blue-500"
                />
                <span className="text-lg font-bold text-white">${(demoAsk / 1000).toFixed(0)}K</span>
              </div>

              <div>
                <label className="text-sm text-slate-400 block mb-2">Revenue (12mo)</label>
                <input
                  type="range"
                  min={0}
                  max={10000000}
                  step={50000}
                  value={demoRevenue}
                  onChange={(e) => setDemoRevenue(Number(e.target.value))}
                  className="w-full accent-blue-500"
                />
                <span className="text-lg font-bold text-white">${(demoRevenue / 1000).toFixed(0)}K</span>
              </div>

              <div className="flex flex-col items-center">
                <DealScoreGauge score={demoScore} animated={false} />
                <span className="text-sm text-slate-400 mt-2">Deal Score</span>
              </div>
            </div>

            <div className="mt-8 text-center">
              <Link
                href="/simulator"
                className="text-blue-400 hover:text-blue-300 text-sm font-medium inline-flex items-center gap-1"
              >
                The full simulator goes deeper <ArrowRight size={14} />
              </Link>
            </div>
          </motion.div>
        </div>
      </section>
    </div>
  );
}
