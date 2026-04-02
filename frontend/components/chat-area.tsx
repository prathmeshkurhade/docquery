"use client";

import { useEffect, useRef, useState } from "react";
import { queryDocuments } from "@/lib/api";
import { ChatMessage } from "@/lib/types";

interface Props {
  selectedDocId: string | null;
}

export default function ChatArea({ selectedDocId }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const question = input.trim();
    setInput("");

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: question,
    };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const res = await queryDocuments(question, selectedDocId || undefined);
      const assistantMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: res.data.answer,
        citations: res.data.citations,
        timing: res.data.timing,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: err.response?.data?.detail || "Something went wrong. Please try again.",
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full">
      {/* Chat messages */}
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-[var(--muted)] px-4">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[var(--primary)]/20 to-[var(--accent)]/20 flex items-center justify-center mb-4">
              <svg className="w-8 h-8 text-[var(--primary)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-white mb-1">Ask your documents</h3>
            <p className="text-sm text-center max-w-sm">
              {selectedDocId
                ? "Ask a question about the selected document"
                : "Ask a question across all your uploaded documents"}
            </p>
            <div className="flex flex-wrap gap-2 mt-6 justify-center">
              {["What is this document about?", "Summarize the key points", "What tech stack is mentioned?"].map((q) => (
                <button
                  key={q}
                  onClick={() => {
                    setInput(q);
                    inputRef.current?.focus();
                  }}
                  className="px-3 py-1.5 bg-[var(--card)] border border-[var(--border)] rounded-lg text-xs hover:bg-[var(--card-hover)] hover:border-[var(--muted)] text-[var(--foreground)]"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
            {messages.map((msg) => (
              <div key={msg.id}>
                {msg.role === "user" ? (
                  <div className="flex justify-end">
                    <div className="bg-[var(--primary)] text-white px-4 py-2.5 rounded-2xl rounded-br-md max-w-[80%]">
                      {msg.content}
                    </div>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {/* Answer */}
                    <div className="bg-[var(--card)] border border-[var(--border)] rounded-2xl rounded-bl-md px-5 py-4 max-w-[90%]">
                      <div className="text-[var(--foreground)] whitespace-pre-wrap leading-relaxed">
                        {msg.content}
                      </div>

                      {/* Timing */}
                      {msg.timing && (
                        <div className="flex gap-3 mt-3 pt-3 border-t border-[var(--border)]">
                          <span className="text-xs text-[var(--muted)]">
                            Search: {msg.timing.search_ms}ms
                          </span>
                          <span className="text-xs text-[var(--muted)]">
                            Rerank: {msg.timing.rerank_ms}ms
                          </span>
                          <span className="text-xs text-[var(--muted)]">
                            Generate: {msg.timing.generate_ms}ms
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Citations — collapsed by default */}
                    {msg.citations && msg.citations.length > 0 && (
                      <details className="max-w-[90%]">
                        <summary className="text-xs text-[var(--muted)] cursor-pointer hover:text-[var(--foreground)] px-1 py-1 select-none">
                          {msg.citations.length} sources (click to expand)
                        </summary>
                        <div className="space-y-2 mt-2">
                          {msg.citations.map((cite, i) => (
                            <div
                              key={i}
                              className="bg-[var(--card)] border border-[var(--border)] rounded-xl px-4 py-2.5 text-sm"
                            >
                              <div className="flex items-center gap-2 mb-1">
                                <span className="inline-flex items-center justify-center w-5 h-5 rounded-md bg-[var(--primary)]/15 text-[var(--primary)] text-xs font-medium">
                                  {cite.page_number}
                                </span>
                                <span className="text-[var(--foreground)] text-xs">Page {cite.page_number}</span>
                                <span className="text-[var(--muted)] text-xs ml-auto">
                                  {(cite.score * 100).toFixed(1)}%
                                </span>
                              </div>
                              <div className="text-xs text-[var(--muted)] line-clamp-2">
                                {cite.text}
                              </div>
                            </div>
                          ))}
                        </div>
                      </details>
                    )}
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div className="flex gap-2 px-5 py-4 bg-[var(--card)] border border-[var(--border)] rounded-2xl rounded-bl-md max-w-[90%]">
                <div className="flex gap-1.5 items-center">
                  <div className="w-2 h-2 rounded-full bg-[var(--primary)] animate-bounce [animation-delay:-0.3s]" />
                  <div className="w-2 h-2 rounded-full bg-[var(--primary)] animate-bounce [animation-delay:-0.15s]" />
                  <div className="w-2 h-2 rounded-full bg-[var(--primary)] animate-bounce" />
                </div>
                <span className="text-sm text-[var(--muted)]">Searching and generating answer...</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input area */}
      <div className="border-t border-[var(--border)] p-4">
        <form onSubmit={handleSubmit} className="max-w-3xl mx-auto relative">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              selectedDocId
                ? "Ask about this document..."
                : "Ask across all documents..."
            }
            rows={1}
            className="w-full px-4 py-3 pr-12 bg-[var(--card)] border border-[var(--border)] rounded-xl text-white placeholder-[var(--muted)] focus:outline-none focus:border-[var(--primary)] focus:ring-1 focus:ring-[var(--primary)] resize-none"
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-2 text-[var(--primary)] hover:text-[var(--primary-hover)] disabled:text-[var(--muted)] disabled:cursor-not-allowed"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19V5m0 0l-7 7m7-7l7 7" />
            </svg>
          </button>
        </form>
      </div>
    </div>
  );
}
