"use client";

import { useRef, useState } from "react";
import { AlertCircle, Loader2, UploadCloud, X } from "lucide-react";
import type { UploadTask } from "@/hooks/useDocuments";
import { cn } from "@/lib/utils";

const ACCEPT = ".pdf,.txt,.docx";

interface Props {
  tasks: UploadTask[];
  onFiles: (files: File[]) => void;
  onDismiss: (id: string) => void;
}

export default function UploadZone({ tasks, onFiles, onDismiss }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const handle = (list: FileList | null) => {
    if (list?.length) onFiles(Array.from(list));
    if (inputRef.current) inputRef.current.value = ""; // allow re-selecting the same file
  };

  return (
    <div className="space-y-2">
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => { e.preventDefault(); setDragging(false); handle(e.dataTransfer.files); }}
        className={cn(
          "flex w-full flex-col items-center gap-1 rounded-lg border-2 border-dashed px-4 py-5 text-center transition-colors",
          dragging ? "border-pine bg-pine-tint" : "border-rule bg-paper-raised hover:border-pine/60",
        )}
      >
        <UploadCloud className="h-6 w-6 text-pine" aria-hidden />
        <span className="text-sm font-medium">Drop files or click to upload</span>
        <span className="text-xs text-ink-soft">PDF, DOCX or TXT, up to 25 MB each</span>
      </button>
      <input ref={inputRef} type="file" accept={ACCEPT} multiple hidden onChange={(e) => handle(e.target.files)} />

      <ul className="space-y-1.5" aria-live="polite">
        {tasks.map((t) => (
          <li
            key={t.id}
            className={cn(
              "flex items-start gap-2 rounded-md px-3 py-2 text-sm",
              t.status === "error" ? "bg-danger-tint text-danger" : "bg-paper-sunk text-ink-soft",
            )}
          >
            {t.status === "uploading" ? (
              <Loader2 className="mt-0.5 h-4 w-4 shrink-0 animate-spin" aria-hidden />
            ) : (
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
            )}
            <div className="min-w-0 flex-1">
              <p className="truncate font-medium">{t.name}</p>
              <p className="text-xs">{t.status === "uploading" ? "Reading and indexing..." : t.error}</p>
            </div>
            {t.status === "error" && (
              <button onClick={() => onDismiss(t.id)} aria-label={`Dismiss error for ${t.name}`}>
                <X className="h-4 w-4" />
              </button>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
