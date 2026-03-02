"use client";

import { Bot } from "lucide-react";
import ToolCallCard from "./ToolCallCard";
import type { ToolCallEvent } from "@/lib/api";

interface Props {
  steps: ToolCallEvent[];
}

interface PairedStep {
  tool: string;
  input?: Record<string, unknown>;
  result?: unknown;
  status: "running" | "complete";
}

export default function ResearchSteps({ steps }: Props) {
  // Build paired steps: match tool_call events with their tool_result counterparts
  const paired: PairedStep[] = [];
  const toolCalls = steps.filter((s) => s.type === "tool_call");
  const toolResults = steps.filter((s) => s.type === "tool_result");

  for (let i = 0; i < toolCalls.length; i++) {
    const call = toolCalls[i];
    const matchingResult = toolResults[i];
    paired.push({
      tool: call.tool || "unknown",
      input: call.input,
      result: matchingResult?.result,
      status: matchingResult ? "complete" : "running",
    });
  }

  return (
    <div className="glass h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-2 px-5 py-4 border-b border-white/[0.06]">
        <Bot size={18} className="text-blue-400" />
        <h2 className="text-sm font-semibold text-white/80">Research Steps</h2>
        {paired.length > 0 && (
          <span className="ml-auto text-xs text-white/30">
            {paired.length} step{paired.length !== 1 ? "s" : ""}
          </span>
        )}
      </div>

      {/* Steps list */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-3">
        {paired.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <p className="text-sm text-white/30 text-center">
              Research steps will appear here as the agent works.
            </p>
          </div>
        ) : (
          paired.map((step, i) => (
            <ToolCallCard
              key={i}
              tool={step.tool}
              input={step.input}
              result={step.result}
              status={step.status}
            />
          ))
        )}
      </div>
    </div>
  );
}
