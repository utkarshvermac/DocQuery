"use client";

import { useCallback, useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { DocumentInfo } from "@/lib/types";
import { uid } from "@/lib/utils";

export interface UploadTask {
  id: string;
  name: string;
  status: "uploading" | "error";
  error?: string;
}

/** Owns the document library, upload queue and the "search scope" selection. */
export function useDocuments() {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [uploads, setUploads] = useState<UploadTask[]>([]);
  const [excluded, setExcluded] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const { documents } = await api.listDocuments();
      setDocuments(documents);
      setError(null);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to load documents.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const upload = useCallback(
    async (files: File[]) => {
      await Promise.all(
        files.map(async (file) => {
          const id = uid();
          setUploads((u) => [...u, { id, name: file.name, status: "uploading" }]);
          try {
            const doc = await api.uploadDocument(file);
            setDocuments((d) => [doc, ...d]);
            setUploads((u) => u.filter((t) => t.id !== id));
          } catch (e) {
            const message = e instanceof ApiError ? e.message : "Upload failed.";
            setUploads((u) => u.map((t) => (t.id === id ? { ...t, status: "error", error: message } : t)));
          }
        }),
      );
    },
    [],
  );

  const dismissUpload = useCallback((id: string) => setUploads((u) => u.filter((t) => t.id !== id)), []);

  const remove = useCallback(async (id: string) => {
    try {
      await api.deleteDocument(id);
      setDocuments((d) => d.filter((doc) => doc.id !== id));
      setExcluded((s) => {
        const next = new Set(s);
        next.delete(id);
        return next;
      });
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not delete the document.");
    }
  }, []);

  const toggle = useCallback((id: string) => {
    setExcluded((s) => {
      const next = new Set(s);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }, []);

  const activeIds = documents.filter((d) => !excluded.has(d.id)).map((d) => d.id);

  return { documents, uploads, excluded, activeIds, loading, error, upload, dismissUpload, remove, toggle, refresh };
}
