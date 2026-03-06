"use client";

import { useState } from "react";
import { testWebhookIntegration } from "@/lib/api";
import { loadSavedAnalyses } from "@/lib/persistence";

export default function SettingsPage() {
  const [webhookUrl, setWebhookUrl] = useState("");
  const [webhookResult, setWebhookResult] = useState<{ delivered: boolean; status_code: number } | null>(null);
  const [webhookLoading, setWebhookLoading] = useState(false);

  async function handleWebhookTest() {
    if (!webhookUrl.trim()) return;
    setWebhookLoading(true);
    setWebhookResult(null);
    try {
      const analyses = loadSavedAnalyses();
      const latest = analyses[0] || { title: "No analyses yet" };
      const res = await testWebhookIntegration({
        webhook_url: webhookUrl.trim(),
        event_type: "analysis.saved",
        payload: { latest_analysis: latest },
      });
      setWebhookResult(res);
    } finally {
      setWebhookLoading(false);
    }
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <section className="rounded-2xl border border-white/12 bg-[var(--bg-surface)] p-6">
        <h1 className="text-2xl font-semibold">Settings & Integrations</h1>
        <p className="mt-2 text-sm text-[var(--text-muted)]">
          Configure webhook delivery, export preferences, and API access for DealScope.
        </p>
      </section>

      <section className="rounded-2xl border border-white/12 bg-[var(--bg-surface)] p-6 space-y-4">
        <h2 className="text-lg font-semibold">Webhook Integration</h2>
        <p className="text-sm text-[var(--text-muted)]">
          Send your latest saved analysis to any endpoint — Zapier, Make, Slack, or your own backend. The test button fires a sample{" "}
          <code className="text-xs bg-white/10 px-1 py-0.5 rounded">analysis.saved</code> event.
        </p>

        <div className="space-y-3">
          <label className="block space-y-1.5">
            <span className="text-xs uppercase tracking-[0.12em] text-[var(--text-muted)]">Webhook URL</span>
            <input
              value={webhookUrl}
              onChange={(e) => setWebhookUrl(e.target.value)}
              placeholder="https://your-endpoint/webhook"
              className="w-full rounded-xl border border-white/15 bg-black/25 px-3 py-2.5 text-sm"
            />
          </label>

          <button
            onClick={handleWebhookTest}
            disabled={webhookLoading || !webhookUrl.trim()}
            className="rounded-xl border border-white/25 bg-white/10 px-4 py-2 text-sm font-semibold hover:bg-white/15 disabled:opacity-40"
          >
            {webhookLoading ? "Sending..." : "Test Webhook"}
          </button>

          {webhookResult && (
            <div className={`rounded-lg border px-3 py-2 text-sm ${webhookResult.delivered ? "border-emerald-500/30 text-emerald-300" : "border-rose-500/30 text-rose-300"}`}>
              {webhookResult.delivered
                ? `Delivered successfully (HTTP ${webhookResult.status_code})`
                : `Delivery failed (HTTP ${webhookResult.status_code})`}
            </div>
          )}
        </div>
      </section>

      <section className="rounded-2xl border border-white/12 bg-[var(--bg-surface)] p-6 space-y-3">
        <h2 className="text-lg font-semibold">Export Preferences</h2>
        <p className="text-sm text-[var(--text-muted)]">
          IC Memo exports are generated as print-ready HTML. Use your browser&apos;s print dialog to save as PDF.
          Custom branding and multi-section templates are available from any engine page.
        </p>
        <div className="rounded-lg border border-white/10 bg-black/20 px-4 py-3 text-xs text-[var(--text-muted)]">
          Tip: In Chrome and Safari, choose &quot;Save as PDF&quot; in the print destination for best results.
        </div>
      </section>

      <section className="rounded-2xl border border-white/12 bg-[var(--bg-surface)] p-6 space-y-3">
        <h2 className="text-lg font-semibold">Data & Privacy</h2>
        <p className="text-sm text-[var(--text-muted)]">
          Saved analyses and watchlists are stored locally in your browser. No account is required and no data
          is sent to external servers beyond the analysis API calls you initiate.
        </p>
      </section>
    </div>
  );
}
