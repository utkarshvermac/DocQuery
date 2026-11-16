"use client";

import { X } from "lucide-react";
import type { useDocuments } from "@/hooks/useDocuments";
import DocumentList from "./DocumentList";
import UploadZone from "./UploadZone";
import { cn } from "@/lib/utils";

type Docs = ReturnType<typeof useDocuments>;

interface Props {
  docs: Docs;
  open: boolean;
  onClose: () => void;
}

export default function Sidebar({ docs, open, onClose }: Props) {
  return (
    <>
      {open && <div className="fixed inset-0 z-30 bg-ink/40 lg:hidden" onClick={onClose} aria-hidden />}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex w-[19rem] flex-col border-r border-rule bg-paper transition-transform lg:static lg:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full",
        )}
        aria-label="Document library"
      >
        <div className="flex items-center justify-between px-5 pb-3 pt-5">
          <h1 className="font-serif text-2xl font-semibold tracking-tight">
            <span className="bg-gradient-to-t from-mark from-40% to-transparent to-40% px-0.5">Doc</span>Query
          </h1>
          <button onClick={onClose} className="rounded p-1 hover:bg-paper-sunk lg:hidden" aria-label="Close sidebar">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="flex-1 space-y-5 overflow-y-auto px-4 pb-4">
          <UploadZone tasks={docs.uploads} onFiles={docs.upload} onDismiss={docs.dismissUpload} />

          <section aria-labelledby="library-heading">
            <div className="mb-2 flex items-baseline justify-between px-1">
              <h2 id="library-heading" className="text-sm font-semibold">Your documents</h2>
              {docs.documents.length > 0 && (
                <span className="text-xs text-ink-soft">{docs.activeIds.length} of {docs.documents.length} searched</span>
              )}
            </div>
            {docs.loading ? (
              <div className="h-16 animate-pulse rounded-lg bg-paper-sunk" aria-label="Loading documents" />
            ) : (
              <DocumentList documents={docs.documents} excluded={docs.excluded} onToggle={docs.toggle} onDelete={docs.remove} />
            )}
          </section>
        </div>

        {docs.error && (
          <div role="alert" className="m-4 rounded-md bg-danger-tint p-3 text-sm text-danger">
            {docs.error}{" "}
            <button onClick={docs.refresh} className="font-medium underline">Retry</button>
          </div>
        )}
      </aside>
    </>
  );
}
