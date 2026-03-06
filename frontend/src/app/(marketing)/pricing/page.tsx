"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { Check } from "lucide-react";

const tiers = [
  {
    name: "Explorer",
    price: "Free",
    priceNote: "No credit card required",
    description: "Get started with the three core intelligence engines.",
    cta: "Launch DealScope",
    ctaHref: "/app",
    ctaStyle: "border",
    features: [
      "Industry Intelligence Engine (10 runs/month)",
      "Startup Readiness Engine (5 runs/month)",
      "Market Fit Recommender (5 runs/month)",
      "Research Copilot — 3 sessions/month",
      "IC Memo PDF export",
      "Browser-based saved analyses",
    ],
  },
  {
    name: "Pro",
    price: "$49",
    priceNote: "per month, billed monthly",
    description: "Full access for founders and independent analysts.",
    cta: "Start Free Trial",
    ctaHref: "mailto:hello@dealscope.ai?subject=Pro%20Trial",
    ctaStyle: "filled",
    highlight: true,
    features: [
      "Unlimited engine runs",
      "Research Copilot — unlimited sessions",
      "Deep research mode (8-turn agent)",
      "Comparable deal deep-dives",
      "Scenario testing with custom deltas",
      "Watchlist + saved history sync",
      "Priority email support",
    ],
  },
  {
    name: "Team",
    price: "$299",
    priceNote: "per month, up to 10 seats",
    description: "Built for accelerators, VC analysts, and MBA programs.",
    cta: "Contact Us",
    ctaHref: "mailto:hello@dealscope.ai?subject=Team%20Plan",
    ctaStyle: "border",
    features: [
      "Everything in Pro for all seats",
      "Batch startup analysis (CSV upload)",
      "Cohort readiness reports",
      "Shared watchlists and analyses",
      "Webhook integrations for Zapier/Make",
      "Custom branding on IC Memos",
      "Dedicated onboarding call",
    ],
  },
];

export default function PricingPage() {
  return (
    <div className="mesh-bg min-h-screen">
      <section className="px-6 pt-28 pb-16">
        <div className="max-w-5xl mx-auto text-center">
          <motion.p
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/[0.03] px-4 py-1 text-xs tracking-[0.2em] uppercase text-[var(--text-muted)]"
          >
            Pricing
          </motion.p>
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.05 }}
            className="mt-6 text-4xl md:text-6xl font-semibold tracking-tight leading-[1.05]"
          >
            Simple, honest pricing.
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="mt-5 max-w-xl mx-auto text-[var(--text-muted)] leading-relaxed"
          >
            Start free. Upgrade when you need more runs, deeper research, or team features.
          </motion.p>
        </div>
      </section>

      <section className="px-6 pb-24">
        <div className="max-w-5xl mx-auto grid md:grid-cols-3 gap-5">
          {tiers.map((tier, i) => (
            <motion.div
              key={tier.name}
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 + i * 0.08 }}
              className={`rounded-2xl border p-7 flex flex-col ${
                tier.highlight
                  ? "border-blue-500/50 bg-blue-950/20"
                  : "border-white/12 bg-[var(--bg-surface)]"
              }`}
            >
              {tier.highlight && (
                <p className="text-xs tracking-[0.18em] uppercase text-blue-400 font-semibold mb-3">
                  Most popular
                </p>
              )}
              <h2 className="text-xl font-semibold">{tier.name}</h2>
              <div className="mt-3">
                <span className="text-4xl font-bold">{tier.price}</span>
                <p className="text-xs text-[var(--text-muted)] mt-1">{tier.priceNote}</p>
              </div>
              <p className="mt-3 text-sm text-[var(--text-muted)] leading-relaxed">{tier.description}</p>

              <ul className="mt-6 space-y-2.5 flex-1">
                {tier.features.map((f) => (
                  <li key={f} className="flex items-start gap-2.5 text-sm">
                    <Check size={15} className="text-emerald-400 flex-shrink-0 mt-0.5" />
                    <span>{f}</span>
                  </li>
                ))}
              </ul>

              <Link
                href={tier.ctaHref}
                className={`mt-7 block text-center rounded-xl px-4 py-3 text-sm font-semibold transition-colors ${
                  tier.ctaStyle === "filled"
                    ? "bg-white text-black hover:bg-white/90"
                    : "border border-white/25 hover:bg-white/8"
                }`}
              >
                {tier.cta}
              </Link>
            </motion.div>
          ))}
        </div>

        <div className="max-w-3xl mx-auto mt-14 rounded-2xl border border-white/10 bg-[var(--bg-surface)] p-7 text-center">
          <h3 className="text-lg font-semibold">Accelerators & MBA Programs</h3>
          <p className="mt-2 text-sm text-[var(--text-muted)] leading-relaxed max-w-xl mx-auto">
            Running a cohort of 10–30 startups? We offer cohort pricing with batch readiness analysis,
            shared reports, and outcome tracking. Reach out to discuss a partnership.
          </p>
          <Link
            href="mailto:hello@dealscope.ai?subject=Accelerator%20Partnership"
            className="mt-4 inline-flex items-center gap-2 rounded-xl border border-white/25 px-5 py-2.5 text-sm font-medium hover:bg-white/8 transition-colors"
          >
            Get in touch
          </Link>
        </div>
      </section>
    </div>
  );
}
