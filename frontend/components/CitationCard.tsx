import { forwardRef } from "react";
import type { Source } from "@/lib/types";
import { cn } from "@/lib/utils";

interface Props {
  source: Source;
  highlighted: boolean;
}

/** One cited passage. The yellow marker is the product's signature motif. */
const CitationCard = forwardRef<HTMLLIElement, Props>(function CitationCard({ source, highlighted }, ref) {
  const location = source.page
    ? `Page ${source.page}`
    : source.section
      ? source.section
      : `Passage ${source.chunk_index + 1}`;

  return (
    <li
      ref={ref}
      id={`source-${source.index}`}
      className={cn("rounded-lg border border-rule bg-paper-raised p-3", highlighted && "animate-flash border-mark")}
    >
      <div className="flex items-center gap-2 text-sm">
        <span className="flex h-5 min-w-5 items-center justify-center rounded bg-mark px-1 text-xs font-semibold">{source.index}</span>
        <span className="min-w-0 truncate font-medium" title={source.filename}>{source.filename}</span>
        <span className="shrink-0 text-ink-soft">{location}</span>
        <span className="ml-auto shrink-0 text-xs text-ink-faint" title="Retrieval similarity">{Math.round(source.score * 100)}% match</span>
      </div>
      <blockquote className="mt-2 border-l-2 border-mark pl-3 font-serif text-sm leading-relaxed text-ink-soft">
        {source.snippet}
      </blockquote>
    </li>
  );
});

export default CitationCard;
