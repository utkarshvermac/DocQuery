"use client";

import { useState } from "react";
import { FileText, Trash2 } from "lucide-react";
import type { DocumentInfo } from "@/lib/types";
import { cn, formatBytes } from "@/lib/utils";

interface Props {
  documents: DocumentInfo[];
  excluded: Set<string>;
  onToggle: (id: string) => void;
  onDelete: (id: string) => void;
}

export default function DocumentList({ documents, excluded, onToggle, onDelete }: Props) {
  const [confirming, setConfirming] = useState<string | null>(null);

  if (!documents.length) {
    return <p className="px-1 text-sm text-ink-soft">No documents yet. Upload one to begin.</p>;
  }

  return (
    <ul className="space-y-1.5">
      {documents.map((doc) => {
        const active = !excluded.has(doc.id);
        const meta = [
          doc.page_count ? `${doc.page_count} pages` : null,
          `${doc.chunk_count} passages`,
          formatBytes(doc.size_bytes),
        ].filter(Boolean).join(", ");

        return (
          <li key={doc.id} className={cn("group rounded-lg border p-2.5 transition-colors", active ? "border-pine/40 bg-paper-raised" : "border-rule bg-transparent opacity-70")}>
            <div className="flex items-start gap-2.5">
              <input
                type="checkbox"
                checked={active}
                onChange={() => onToggle(doc.id)}
                aria-label={`Include ${doc.filename} in answers`}
                className="mt-1 h-4 w-4 shrink-0 accent-[#145A4E]"
              />
              <FileText className="mt-0.5 h-4 w-4 shrink-0 text-pine" aria-hidden />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium" title={doc.filename}>{doc.filename}</p>
                <p className="text-xs text-ink-soft">{meta}</p>
              </div>
              {confirming === doc.id ? (
                <div className="flex shrink-0 items-center gap-1 text-xs">
                  <button onClick={() => { onDelete(doc.id); setConfirming(null); }} className="rounded bg-danger px-2 py-1 font-medium text-white">Delete</button>
                  <button onClick={() => setConfirming(null)} className="rounded px-2 py-1 text-ink-soft hover:bg-paper-sunk">Keep</button>
                </div>
              ) : (
                <button
                  onClick={() => setConfirming(doc.id)}
                  aria-label={`Delete ${doc.filename}`}
                  className="shrink-0 rounded p-1 text-ink-faint hover:bg-danger-tint hover:text-danger"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              )}
            </div>
          </li>
        );
      })}
    </ul>
  );
}
