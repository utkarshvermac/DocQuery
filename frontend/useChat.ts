"use client";

import { useCallback, useRef, useState } from "react";
import { api, ApiError } from "@/lib/api";
import type { ChatMessage } from "@/lib/types";
import { uid } from "@/lib/utils";

/** Conversation state. `scopeIds` limits retrieval to the selected documents. */
export function useChat(scopeIds: string[], totalDocs: number) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const sessionId = useRef<string | null>(null);

  const send = useCallback(
    async (question: string) => {
      const text = question.trim();
      if (!text || loading) return;
      setMessages((m) => [...m, { id: uid(), role: "user", content: text }]);
      setLoading(true);
      try {
        const res = await api.chat({
          question: text,
          session_id: sessionId.current,
          // null = search everything; otherwise only the ticked documents
          document_ids: scopeIds.length === totalDocs ? null : scopeIds,
        });
        sessionId.current = res.session_id;
        setMessages((m) => [
          ...m,
          { id: uid(), role: "assistant", content: res.answer, sources: res.sources, latencyMs: res.latency_ms },
        ]);
      } catch (e) {
        const message = e instanceof ApiError ? e.message : "Something went wrong. Please try again.";
        setMessages((m) => [...m, { id: uid(), role: "assistant", content: message, isError: true }]);
      } finally {
        setLoading(false);
      }
    },
    [loading, scopeIds, totalDocs],
  );

  const reset = useCallback(async () => {
    const old = sessionId.current;
    sessionId.current = null;
    setMessages([]);
    if (old) await api.deleteSession(old).catch(() => undefined);
  }, []);

  return { messages, loading, send, reset };
}
