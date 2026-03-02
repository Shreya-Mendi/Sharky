"use client";

import { Bot, User } from "lucide-react";

interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
}

export default function ChatMessage({ role, content }: ChatMessageProps) {
  const isBot = role === "assistant";

  return (
    <div className={`flex gap-3 ${isBot ? "" : "flex-row-reverse"}`}>
      <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
        isBot ? "bg-blue-600" : "bg-slate-700"
      }`}>
        {isBot ? <Bot size={16} /> : <User size={16} />}
      </div>
      <div className={`max-w-[70%] rounded-2xl px-5 py-3 ${
        isBot ? "glass" : "bg-blue-600/20 border border-blue-500/20"
      }`}>
        <div className="text-sm leading-relaxed whitespace-pre-wrap">{content}</div>
      </div>
    </div>
  );
}
