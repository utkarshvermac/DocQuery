"use client";

import { createRef, useMemo, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { AlertCircle, ChevronDown } from "lucide-react";
import type { ChatMessage } from "@/lib/types";
import { cn } from "@/lib/utils";
import CitationCard from "./CitationCard";

export default function MessageBubble({ message }: { message: ChatMessage }) {
  const [showSources, setShowSources] = useState(true);
  const [flashIndex, setFlashIndex] = useState<number | null>(null);
  const sources = message.sources ?? [];
  const refs = useRef(new Map<number, React.RefObject<HTMLLIElement>>());

  // Turn "[2]" markers into links the markdown renderer can style as chips.
  const markdown = useMemo(() => {
    const valid = new Set(sources.map((s) => s.index));
    return message.content.replace(/\[(\d{1,3})\]/g, (m, n) => (valid.has(Number(n)) ? `[${n}](#cite-${n})` : m));
  }, [message.content, sources]);

  const jumpTo = (index: number) => {
    setShowSources(true);
    setFlashIndex(index);
    requestAnimationFrame(() =>
      refs.current.get(index)?.current?.scrollIntoView({ behavior: "smooth", block: "nearest" }),
    );
    setTimeout(() => setFlashIndex(null), 1300);
  };

  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <p className="max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-br-sm bg-pine px-4 py-2.5 text-white sm:max-w-[70%]">{message.content}</p>
      </div>
    );
  }

  if (message.isError) {
    return (
      <div role="alert" className="flex max-w-[85%] items-start gap-2 rounded-lg bg-danger-tint px-4 py-3 text-sm text-danger">
        <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
        <p>{message.content}</p>
      </div>
    );
  }

  return (
    <div className="max-w-full">
      <div className="prose-answer">
        <ReactMarkdown
          components={{
            a: ({ href, children }) => {
              const match = href?.match(/^#cite-(\d+)$/);
              if (!match) return <a href={href} target="_blank" rel="noreferrer" className="text-pine underline">{children}</a>;
              const n = Number(match[1]);
              return (
                <button
                  type="button"
                  onClick={() => jumpTo(n)}
                  className="mx-0.5 inline-flex h-[1.2em] min-w-[1.3em] -translate-y-[1px] items-center justify-center rounded-sm bg-mark px-1 align-baseline font-sans text-[0.72em] font-semibold text-ink hover:bg-mark-soft"
                  aria-label={`Show source ${n}`}
                >
                  {n}
                </button>
              );
            },
          }}
        >
          {markdown}
        </ReactMarkdown>
      </div>

      {sources.length > 0 && (
        <div className="mt-3 max-w-[68ch]">
          <button
            onClick={() => setShowSources((s) => !s)}
            aria-expanded={showSources}
            className="flex items-center gap-1 text-sm font-medium text-pine hover:underline"
          >
            <ChevronDown className={cn("h-4 w-4 transition-transform", !showSources && "-rotate-90")} aria-hidden />
            {sources.length} {sources.length === 1 ? "source" : "sources"}
          </button>
          {showSources && (
            <ul className="mt-2 space-y-2">
              {sources.map((s) => {
                if (!refs.current.has(s.index)) refs.current.set(s.index, createRef<HTMLLIElement>());
                return <CitationCard key={s.index} source={s} highlighted={flashIndex === s.index} ref={refs.current.get(s.index)} />;
              })}
            </ul>
          )}
        </div>
      )}
      {message.latencyMs !== undefined && (
        <p className="mt-2 text-xs text-ink-faint">Answered in {(message.latencyMs / 1000).toFixed(1)}s</p>
      )}
    </div>
  );
}
