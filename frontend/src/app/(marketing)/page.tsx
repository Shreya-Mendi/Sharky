"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowRight, Database, LineChart, Radar, Sparkles } from "lucide-react";
import AnimatedCounter from "@/components/ui/AnimatedCounter";

const intelligenceLayers = [
  {
    layer: "1st order",
    question: "What happened?",
    example: "Fintech peer set with $750K revenue closed 68% of rounds when pricing stayed below 5x revenue.",
  },
  {
    layer: "2nd order",
    question: "What patterns emerge?",
    example:
      "Teams with lower objection pressure and higher confidence signals outperform sector averages by 1.4x.",
  },
  {
    layer: "3rd order",
    question: "What should we prioritize?",
    example:
      "A B2B health-tech startup shows strongest pitch-dynamic alignment with Northeast markets and enterprise partnerships — ranked with 74% confidence from corpus signals.",
  },
];

const featureCards = [
  {
    icon: Database,
    title: "Industry Intelligence Engine",
    description: "Map sector-level success patterns from outcome, transcript, and live market signals.",
  },
  {
    icon: Radar,
    title: "Startup Readiness Engine",
    description: "Benchmark a startup against successful peers and surface funding-readiness gaps.",
  },
  {
    icon: LineChart,
    title: "Market Fit Recommender",
    description: "Rank sectors, growth avenues, and US markets with rationale and confidence.",
  },
];

const flowItems = [
  "Ingest structured outcomes + negotiation transcript corpus + live US news",
  "Build feature signals and confidence scores across sectors and startup profiles",
  "Deliver explainable recommendations through three decision engines",
];

export default function HomePage() {
  return (
    <div className="mesh-bg min-h-screen">
      <section className="px-6 pt-28 pb-20">
        <div className="max-w-6xl mx-auto">
          <motion.p
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45 }}
            className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/[0.03] px-4 py-1 text-xs tracking-[0.2em] uppercase text-[var(--text-muted)]"
          >
            <Sparkles size={14} className="text-[var(--accent-blue)]" />
            VC Decision Intelligence
          </motion.p>

          <motion.h1
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, delay: 0.05 }}
            className="mt-6 max-w-4xl text-5xl md:text-7xl font-semibold leading-[1.02] tracking-tight"
          >
            Move from startup guesswork to engine-driven market decisions.
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, delay: 0.1 }}
            className="mt-6 max-w-2xl text-lg text-[var(--text-muted)] leading-relaxed"
          >
            DealScope turns sector patterns, startup readiness, and market expansion planning into one product workflow for investors and founders.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, delay: 0.15 }}
            className="mt-10 flex flex-col sm:flex-row gap-4"
          >
            <Link
              href="/app"
              className="inline-flex items-center justify-center gap-2 rounded-xl border border-white/20 bg-white/[0.08] px-7 py-3 font-semibold hover:bg-white/[0.14] transition-colors"
            >
              Launch DealScope <ArrowRight size={17} />
            </Link>
            <a
              href="#layers"
              className="inline-flex items-center justify-center rounded-xl border border-white/15 px-7 py-3 font-semibold text-[var(--text-muted)] hover:text-white hover:border-white/30 transition-colors"
            >
              View Intelligence Layers
            </a>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-4"
          >
            <div className="rounded-xl border border-white/10 bg-[var(--bg-surface)] p-5">
              <p className="text-3xl font-semibold">
                <AnimatedCounter target={741} suffix="+" />
              </p>
              <p className="mt-1 text-sm text-[var(--text-muted)]">Pitches Parsed</p>
            </div>
            <div className="rounded-xl border border-white/10 bg-[var(--bg-surface)] p-5">
              <p className="text-3xl font-semibold">
                <AnimatedCounter target={15} />
              </p>
              <p className="mt-1 text-sm text-[var(--text-muted)]">Seasons Covered</p>
            </div>
            <div className="rounded-xl border border-white/10 bg-[var(--bg-surface)] p-5">
              <p className="text-3xl font-semibold">
                <AnimatedCounter target={1481} />
              </p>
              <p className="mt-1 text-sm text-[var(--text-muted)]">Labeled Records</p>
            </div>
            <div className="rounded-xl border border-white/10 bg-[var(--bg-surface)] p-5">
              <p className="text-3xl font-semibold">3 Engines</p>
              <p className="mt-1 text-sm text-[var(--text-muted)]">Industry, Readiness, Market Fit</p>
            </div>
          </motion.div>
        </div>
      </section>

      <section id="layers" className="px-6 py-16">
        <div className="max-w-6xl mx-auto">
          <motion.h2
            initial={{ opacity: 0, y: 18 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="text-3xl md:text-4xl font-semibold tracking-tight"
          >
            Intelligence Layers
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 18 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.05 }}
            className="mt-3 text-[var(--text-muted)] max-w-3xl"
          >
            The product flow is strongest when each layer is explicit: event recall, pattern recognition, and forward prediction.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 18 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.08 }}
            className="mt-8 overflow-x-auto rounded-2xl border border-white/15 bg-[var(--bg-panel)]"
          >
            <table className="matrix-table min-w-full text-left">
              <thead>
                <tr className="bg-black/25">
                  <th className="px-6 py-4 text-sm font-semibold text-[var(--text-muted)]">Layer</th>
                  <th className="px-6 py-4 text-sm font-semibold text-[var(--text-muted)]">What it answers</th>
                  <th className="px-6 py-4 text-sm font-semibold text-[var(--text-muted)]">Example</th>
                </tr>
              </thead>
              <tbody>
                {intelligenceLayers.map((row) => (
                  <tr key={row.layer}>
                    <td className="px-6 py-6 text-lg font-semibold">{row.layer}</td>
                    <td className="px-6 py-6 text-lg text-[var(--text-muted)]">{row.question}</td>
                    <td className="px-6 py-6 text-lg text-[var(--text-muted)]">{row.example}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </motion.div>
        </div>
      </section>

      <section id="features" className="px-6 py-16">
        <div className="max-w-6xl mx-auto grid md:grid-cols-3 gap-5">
          {featureCards.map((card, i) => (
            <motion.article
              key={card.title}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.45, delay: i * 0.06 }}
              className="rounded-2xl border border-white/12 bg-[var(--bg-surface)] p-6"
            >
              <card.icon size={20} className="text-[var(--accent-blue)]" />
              <h3 className="mt-4 text-xl font-semibold">{card.title}</h3>
              <p className="mt-3 text-[var(--text-muted)] leading-relaxed">{card.description}</p>
            </motion.article>
          ))}
        </div>
      </section>

      <section id="how-it-works" className="px-6 pt-4 pb-24">
        <div className="max-w-6xl mx-auto rounded-2xl border border-white/12 bg-[var(--bg-surface)] p-8 md:p-10">
          <h2 className="text-2xl md:text-3xl font-semibold tracking-tight">Product Flow</h2>
          <div className="mt-6 grid md:grid-cols-3 gap-4">
            {flowItems.map((item, idx) => (
              <div key={item} className="rounded-xl border border-white/10 bg-black/20 p-5">
                <p className="text-xs uppercase tracking-[0.22em] text-[var(--text-muted)]">Step {idx + 1}</p>
                <p className="mt-2 text-base leading-relaxed">{item}</p>
              </div>
            ))}
          </div>
          <div className="mt-8 flex flex-col sm:flex-row gap-4 sm:items-center sm:justify-between">
            <p className="text-[var(--text-muted)]">
              We position negotiation transcripts as a novel signal layer while keeping the product centered on practical VC and founder decisions.
            </p>
            <Link
              href="/app"
              className="inline-flex items-center justify-center gap-2 rounded-xl border border-white/20 bg-white/[0.08] px-7 py-3 font-semibold hover:bg-white/[0.14] transition-colors"
            >
              Open Product <ArrowRight size={17} />
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
