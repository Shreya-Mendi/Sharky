"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Send, Bot, User, Sparkles, Loader2 } from "lucide-react";
import { streamResearch } from "@/lib/api";
import type { ToolCallEvent } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface Props {
  onStep: (step: ToolCallEvent) => void;
  onReset: () => void;
}

const STARTER_PROMPTS = [
  "What makes food-tech startups successful?",
  "Compare tech vs health deal success rates",
  "Revenue benchmarks by industry",
  "Best equity structures for high-value deals",
];

function renderMarkdown(text: string) {
  // Split on double newlines into paragraphs, apply bold
  const paragraphs = text.split(/\n\n+/);
  return paragraphs.map((p, i) => {
    // Replace **bold** with <strong>
    const parts: (string | React.ReactElement)[] = [];
    const regex = /\*\*(.+?)\*\*/g;
    let lastIndex = 0;
    let match;
    while ((match = regex.exec(p)) !== null) {
      if (match.index > lastIndex) {
        parts.push(p.slice(lastIndex, match.index));
      }
      parts.push(
        <strong key={`${i}-${match.index}`} className="font-semibold text-white">
          {match[1]}
        </strong>
      );
      lastIndex = regex.lastIndex;
    }
    if (lastIndex < p.length) {
      parts.push(p.slice(lastIndex));
    }
    return (
      <p key={i} className={i > 0 ? "mt-3" : ""}>
        {parts}
      </p>
    );
  });
}

export default function AgentChat({ onStep, onReset }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const handleSubmit = async (query: string) => {
    if (!query.trim() || streaming) return;

    const userMessage: Message = { role: "user", content: query.trim() };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setStreaming(true);

    // Reset steps for new query
    onReset();

    let assistantContent = "";
    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

    try {
      for await (const event of streamResearch(query.trim())) {
        if (event.type === "tool_call" || event.type === "tool_result") {
          onStep(event);
        } else if (event.type === "answer" && event.content) {
          assistantContent += event.content;
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = {
              role: "assistant",
              content: assistantContent,
            };
            return updated;
          });
        } else if (event.type === "error") {
          assistantContent += event.content || "An error occurred.";
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = {
              role: "assistant",
              content: assistantContent,
            };
            return updated;
          });
        } else if (event.type === "done") {
          break;
        }
      }
    } catch (err) {
      const errorMsg =
        err instanceof Error ? err.message : "Something went wrong.";
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: "assistant",
          content: errorMsg,
        };
        return updated;
      });
    } finally {
      setStreaming(false);
    }
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSubmit(input);
  };

  const hasMessages = messages.length > 0;

  return (
    <div className="glass flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-2 px-5 py-4 border-b border-white/[0.06]">
        <Sparkles size={18} className="text-amber-400" />
        <h2 className="text-sm font-semibold text-white/80">Research Agent</h2>
        {streaming && (
          <span className="ml-auto flex items-center gap-1.5 text-xs text-blue-400">
            <Loader2 size={12} className="animate-spin" />
            Researching...
          </span>
        )}
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-5 space-y-4">
        {!hasMessages && (
          <div className="h-full flex flex-col items-center justify-center gap-6">
            <div className="text-center">
              <Bot size={40} className="text-blue-400 mx-auto mb-3 opacity-60" />
              <h3 className="text-lg font-semibold text-white/70">
                Ask the Research Agent
              </h3>
              <p className="text-sm text-white/30 mt-1">
                Ask questions about Shark Tank deals, market trends, and investment patterns.
              </p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-lg">
              {STARTER_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  onClick={() => handleSubmit(prompt)}
                  className="text-left text-sm px-4 py-3 rounded-xl bg-white/[0.04] border border-white/[0.06] text-white/50 hover:bg-white/[0.08] hover:text-white/70 hover:border-white/[0.12] transition-all"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        )}

        {hasMessages &&
          messages.map((msg, i) => (
            <div
              key={i}
              className={`flex gap-3 ${
                msg.role === "user" ? "flex-row-reverse" : ""
              }`}
            >
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                  msg.role === "assistant" ? "bg-blue-600" : "bg-slate-700"
                }`}
              >
                {msg.role === "assistant" ? (
                  <Bot size={16} />
                ) : (
                  <User size={16} />
                )}
              </div>
              <div
                className={`max-w-[75%] rounded-2xl px-5 py-3 ${
                  msg.role === "assistant"
                    ? "bg-white/[0.05] border border-white/[0.06]"
                    : "bg-blue-600/20 border border-blue-500/20"
                }`}
              >
                <div className="text-sm leading-relaxed text-white/80">
                  {msg.role === "assistant"
                    ? renderMarkdown(msg.content)
                    : msg.content}
                  {msg.role === "assistant" &&
                    msg.content === "" &&
                    streaming &&
                    i === messages.length - 1 && (
                      <span className="inline-flex items-center gap-1.5 text-white/30">
                        <Loader2 size={12} className="animate-spin" />
                        Thinking...
                      </span>
                    )}
                </div>
              </div>
            </div>
          ))}

        <div ref={messagesEndRef} />
      </div>

      {/* Input bar */}
      <form
        onSubmit={handleFormSubmit}
        className="px-5 py-4 border-t border-white/[0.06]"
      >
        <div className="flex items-center gap-3 bg-white/[0.04] border border-white/[0.08] rounded-xl px-4 py-2 focus-within:border-blue-500/40 transition-colors">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a research question..."
            disabled={streaming}
            className="flex-1 bg-transparent text-sm text-white placeholder-white/30 outline-none disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!input.trim() || streaming}
            className="w-8 h-8 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-30 disabled:hover:bg-blue-600 flex items-center justify-center transition-colors"
          >
            <Send size={14} />
          </button>
        </div>
      </form>
    </div>
  );
}
