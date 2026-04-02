export interface User {
  id: string;
  email: string;
  created_at: string;
}

export interface Document {
  id: string;
  filename: string;
  status: "uploading" | "processing" | "ready" | "failed";
  error_message: string | null;
  page_count: number | null;
  chunk_count: number | null;
  created_at: string;
}

export interface Citation {
  text: string;
  page_number: number;
  score: number;
}

export interface QueryResponse {
  answer: string;
  citations: Citation[];
  timing: {
    search_ms: number;
    rerank_ms: number;
    generate_ms: number;
  };
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  timing?: QueryResponse["timing"];
}
