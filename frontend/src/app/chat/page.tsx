"use client";

import { useState, useRef, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { Send } from "lucide-react";
import ChatMessage from "@/components/chat/ChatMessage";
import SourcesPanel from "@/components/chat/SourcesPanel";
import { streamAnalysis, type ChatMessage as ChatMessageType } from "@/lib/api";

const STARTERS = [
  "What industries get the most deals?",
  "Compare food vs tech pitch success rates",
  "What should I ask for with $500K revenue?",
  "Show me the biggest deals ever made",
  "What patterns do failed pitches have?",
  "Analyze objection patterns across seasons",
];

function ChatContent() {
  const searchParams = useSearchParams();
  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [sources, setSources] = useState<any[]>([]);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Pre-load context from simulator
  useEffect(() => {
    const context = searchParams.get("context");
    if (context && messages.length === 0) {
      setInput(context);
    }
  }, [searchParams, messages.length]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleSend(text?: string) {
    const query = text || input.trim();
    if (!query || streaming) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: query }]);
    setStreaming(true);

    let assistantContent = "";
    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

    try {
      for await (const chunk of streamAnalysis(query)) {
        if (chunk.type === "sources") {
          setSources(chunk.data);
        } else if (chunk.type === "text") {
          assistantContent += chunk.data;
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = { role: "assistant", content: assistantContent };
            return updated;
          });
        } else if (chunk.type === "error") {
          assistantContent = `I couldn't complete the analysis: ${chunk.data}. This likely means API keys (ANTHROPIC_API_KEY, OPENAI_API_KEY, PINECONE_API_KEY) aren't configured. You can still use the Simulator and Intelligence Hub which work with local data.`;
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = { role: "assistant", content: assistantContent };
            return updated;
          });
        }
      }
    } catch (err) {
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: "assistant",
          content: "Connection error. Make sure the API server is running on port 8000.",
        };
        return updated;
      });
    } finally {
      setStreaming(false);
    }
  }

  return (
    <div className="h-[calc(100vh-4rem)] flex">
      {/* Chat */}
      <div className="flex-1 flex flex-col">
        <div className="flex-1 overflow-y-auto px-6 py-6 space-y-4">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center">
              <h2 className="text-2xl font-bold mb-2">SharkBot</h2>
              <p className="text-slate-400 mb-8 text-center max-w-md">
                Ask me anything about Shark Tank pitches, deal patterns, and market intelligence.
              </p>
              <div className="grid grid-cols-2 gap-3 max-w-lg">
                {STARTERS.map((s) => (
                  <button
                    key={s}
                    onClick={() => handleSend(s)}
                    className="glass glass-hover px-4 py-3 text-sm text-left text-slate-300 hover:text-white transition-colors"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((msg, i) => <ChatMessage key={i} role={msg.role} content={msg.content} />)
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Input */}
        <div className="border-t border-white/10 px-6 py-4">
          <div className="flex gap-3 max-w-4xl mx-auto">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              placeholder="Ask about Shark Tank pitches..."
              disabled={streaming}
              className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 disabled:opacity-50"
            />
            <button
              onClick={() => handleSend()}
              disabled={streaming || !input.trim()}
              className="bg-blue-600 hover:bg-blue-500 disabled:opacity-30 text-white p-3 rounded-xl transition-all"
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </div>

      {/* Sources Panel */}
      <div className="w-80 border-l border-white/10 p-4 overflow-y-auto hidden lg:block">
        <SourcesPanel sources={sources} />
      </div>
    </div>
  );
}

export default function ChatPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center text-slate-400">Loading chat...</div>}>
      <ChatContent />
    </Suspense>
  );
}
