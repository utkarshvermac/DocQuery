export interface DocumentInfo {
  id: string;
  filename: string;
  file_type: string;
  size_bytes: number;
  page_count: number | null;
  chunk_count: number;
  uploaded_at: string;
}

export interface Source {
  index: number;
  document_id: string;
  filename: string;
  page: number | null;
  section: string | null;
  chunk_index: number;
  snippet: string;
  score: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  isError?: boolean;
  latencyMs?: number;
}

export interface ChatResponse {
  session_id: string;
  answer: string;
  sources: Source[];
  latency_ms: number;
}
