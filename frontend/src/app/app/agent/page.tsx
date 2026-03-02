"use client";

import { useState } from "react";
import AgentChat from "@/components/agent/AgentChat";
import ResearchSteps from "@/components/agent/ResearchSteps";
import type { ToolCallEvent } from "@/lib/api";

export default function AgentPage() {
  const [steps, setSteps] = useState<ToolCallEvent[]>([]);

  return (
    <div className="grid lg:grid-cols-5 gap-6 h-[calc(100vh-7rem)]">
      <div className="lg:col-span-3 flex flex-col">
        <AgentChat
          onStep={(step) => setSteps((prev) => [...prev, step])}
          onReset={() => setSteps([])}
        />
      </div>
      <div className="lg:col-span-2">
        <ResearchSteps steps={steps} />
      </div>
    </div>
  );
}
