/** Thin, typed API client. All errors surface as `ApiError` with a user-readable message. */
import type { ChatResponse, DocumentInfo } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export class ApiError extends Error {
  constructor(message: string, public code: string = "unknown", public status = 0) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, init);
  } catch {
    throw new ApiError(
      "Can't reach the DocQuery server. Check that the backend is running.",
      "network_error",
    );
  }

  if (res.status === 204) return undefined as T;

  const body = await res.json().catch(() => null);
  if (!res.ok) {
    const err = body?.error;
    throw new ApiError(err?.message ?? `Request failed (${res.status}).`, err?.code ?? "http_error", res.status);
  }
  return body as T;
}

export const api = {
  listDocuments: () => request<{ documents: DocumentInfo[]; total: number }>("/documents"),

  uploadDocument(file: File) {
    const form = new FormData();
    form.append("file", file);
    return request<DocumentInfo>("/documents", { method: "POST", body: form });
  },

  deleteDocument: (id: string) => request<void>(`/documents/${id}`, { method: "DELETE" }),

  chat: (payload: { question: string; session_id: string | null; document_ids: string[] | null }) =>
    request<ChatResponse>("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  deleteSession: (id: string) => request<void>(`/sessions/${id}`, { method: "DELETE" }),
};
