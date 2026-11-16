"use client";

import { useEffect, useRef } from "react";
import { Menu, RotateCcw } from "lucide-react";
import type { ChatMessage, DocumentInfo } from "@/lib/types";
import ChatInput from "./ChatInput";
import MessageBubble from "./MessageBubble";

interface Props {
  messages: ChatMessage[];
  loading: boolean;
  documents: DocumentInfo[];
  activeCount: number;
  onSend: (q: string) => void;
  onReset: () => void;
  onOpenSidebar: () => void;
}

const STARTERS = [
  "Summarise the main points of these documents.",
  "What are the key conclusions or recommendations?",
  "List any dates, deadlines or figures mentioned.",
];

export default function ChatWindow({ messages, loading, documents, activeCount, onSend, onReset, onOpenSidebar }: Props) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, loading]);

  const hasDocs = documents.length > 0;
  const canAsk = hasDocs && activeCount > 0 && !loading;
  const placeholder = !hasDocs
    ? "Upload a document to start asking questions"
    : activeCount === 0
      ? "Tick at least one document to search"
      : "Ask a question about your documents";

  return (
    <main className="flex min-w-0 flex-1 flex-col">
      <header className="flex items-center gap-3 border-b border-rule px-4 py-3">
        <button onClick={onOpenSidebar} className="rounded p-1.5 hover:bg-paper-sunk lg:hidden" aria-label="Open document library">
          <Menu className="h-5 w-5" />
        </button>
        <p className="text-sm text-ink-soft">
          {hasDocs ? `Searching ${activeCount} of ${documents.length} documents` : "No documents uploaded"}
        </p>
        {messages.length > 0 && (
          <button onClick={onReset} className="ml-auto flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-sm text-ink-soft hover:bg-paper-sunk">
            <RotateCcw className="h-4 w-4" aria-hidden /> New conversation
          </button>
        )}
      </header>

      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="mx-auto flex max-w-3xl flex-col gap-6">
          {messages.length === 0 && (
            <div className="pt-[8vh]">
              <h2 className="font-serif text-3xl font-semibold leading-tight sm:text-4xl">
                {hasDocs ? "What would you like to know?" : "Start by adding a document"}
              </h2>
              <p className="mt-3 max-w-[52ch] text-ink-soft">
                {hasDocs
                  ? "Answers come only from your files, and every claim links back to the passage it came from."
                  : "Upload a PDF, Word file or text file from the library. Once it is indexed you can ask questions and see exactly where each answer comes from."}
              </p>
              {hasDocs && (
                <div className="mt-6 flex flex-col items-start gap-2">
                  {STARTERS.map((s) => (
                    <button key={s} disabled={!canAsk} onClick={() => onSend(s)} className="rounded-lg border border-rule bg-paper-raised px-3.5 py-2 text-left text-sm hover:border-pine disabled:opacity-50">
                      {s}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {messages.map((m) => <MessageBubble key={m.id} message={m} />)}

          {loading && (
            <div className="flex items-center gap-1.5 text-ink-soft" role="status" aria-label="Searching your documents">
              {[0, 1, 2].map((i) => (
                <span key={i} className="h-2 w-2 animate-dot rounded-full bg-pine" style={{ animationDelay: `${i * 0.18}s` }} />
              ))}
              <span className="ml-2 text-sm">Searching your documents</span>
            </div>
          )}
          <div ref={endRef} />
        </div>
      </div>

      <div className="px-4 pb-4 pt-2">
        <div className="mx-auto max-w-3xl">
          <ChatInput onSend={onSend} disabled={!canAsk} placeholder={placeholder} />
          <p className="mt-2 text-center text-xs text-ink-faint">Enter to send, Shift+Enter for a new line. Check important facts against the cited passages.</p>
        </div>
      </div>
    </main>
  );
}
