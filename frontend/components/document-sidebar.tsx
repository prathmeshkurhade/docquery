"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { listDocuments, uploadDocument, getDocument, deleteDocument } from "@/lib/api";
import { Document } from "@/lib/types";

interface Props {
  selectedDocId: string | null;
  onSelectDoc: (id: string | null) => void;
}

export default function DocumentSidebar({ selectedDocId, onSelectDoc }: Props) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [search, setSearch] = useState("");
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const fetchDocs = useCallback(async () => {
    try {
      const res = await listDocuments();
      setDocuments(res.data);
    } catch {}
  }, []);

  useEffect(() => {
    fetchDocs();
    const interval = setInterval(fetchDocs, 5000);
    return () => clearInterval(interval);
  }, [fetchDocs]);

  // Poll processing docs more frequently
  useEffect(() => {
    const processingDocs = documents.filter(
      (d) => d.status === "uploading" || d.status === "processing"
    );
    if (processingDocs.length === 0) return;

    const interval = setInterval(async () => {
      for (const doc of processingDocs) {
        try {
          const res = await getDocument(doc.id);
          setDocuments((prev) =>
            prev.map((d) => (d.id === doc.id ? res.data : d))
          );
        } catch {}
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [documents]);

  const handleUpload = async (file: File) => {
    if (file.type !== "application/pdf") {
      alert("Only PDF files are allowed");
      return;
    }
    setUploading(true);
    try {
      await uploadDocument(file);
      await fetchDocs();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      alert(e.response?.data?.detail || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleUpload(file);
  };

  const handleDelete = async (e: React.MouseEvent, docId: string) => {
    e.stopPropagation();
    if (!confirm("Delete this document? This cannot be undone.")) return;
    try {
      await deleteDocument(docId);
      if (selectedDocId === docId) onSelectDoc(null);
      await fetchDocs();
    } catch {
      alert("Failed to delete document");
    }
  };

  const filteredDocs = documents.filter((d) =>
    d.filename.toLowerCase().includes(search.toLowerCase())
  );

  const statusIcon = (status: Document["status"]) => {
    switch (status) {
      case "ready":
        return <span className="w-2 h-2 rounded-full bg-[var(--success)]" />;
      case "processing":
      case "uploading":
        return (
          <span className="w-2 h-2 rounded-full bg-[var(--warning)] animate-pulse" />
        );
      case "failed":
        return <span className="w-2 h-2 rounded-full bg-[var(--danger)]" />;
    }
  };

  return (
    <div className="w-80 h-full bg-[var(--card)] border-r border-[var(--border)] flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-[var(--border)]">
        <div className="flex items-center gap-2 mb-4">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[var(--primary)] to-[var(--accent)] flex items-center justify-center">
            <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <span className="font-semibold text-white">DocQuery</span>
        </div>

        {/* Search */}
        <div className="relative">
          <svg className="absolute left-3 top-2.5 w-4 h-4 text-[var(--muted)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search documents..."
            className="w-full pl-9 pr-3 py-2 bg-[var(--background)] border border-[var(--border)] rounded-lg text-sm text-white placeholder-[var(--muted)] focus:outline-none focus:border-[var(--primary)]"
          />
        </div>
      </div>

      {/* Upload area */}
      <div className="p-4">
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-4 text-center cursor-pointer transition-colors ${
            dragOver
              ? "border-[var(--primary)] bg-[var(--primary)]/10"
              : "border-[var(--border)] hover:border-[var(--muted)]"
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) handleUpload(file);
              e.target.value = "";
            }}
          />
          {uploading ? (
            <div className="text-[var(--muted)] text-sm">
              <svg className="animate-spin w-5 h-5 mx-auto mb-1" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Uploading...
            </div>
          ) : (
            <div className="text-[var(--muted)] text-sm">
              <svg className="w-6 h-6 mx-auto mb-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 4v16m8-8H4" />
              </svg>
              Drop PDF here or click
            </div>
          )}
        </div>
      </div>

      {/* Query scope */}
      <div className="px-4 pb-2">
        <button
          onClick={() => onSelectDoc(null)}
          className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
            selectedDocId === null
              ? "bg-[var(--primary)]/15 text-[var(--primary-hover)] border border-[var(--primary)]/30"
              : "text-[var(--muted)] hover:bg-[var(--card-hover)]"
          }`}
        >
          All Documents
        </button>
      </div>

      {/* Document list */}
      <div className="flex-1 overflow-y-auto px-4 pb-4 space-y-1">
        <div className="text-xs text-[var(--muted)] uppercase tracking-wider mb-2 px-1">
          Documents ({filteredDocs.length})
        </div>
        {filteredDocs.map((doc) => (
          <button
            key={doc.id}
            onClick={() => doc.status === "ready" && onSelectDoc(doc.id)}
            className={`w-full text-left px-3 py-2.5 rounded-lg text-sm transition-colors group ${
              selectedDocId === doc.id
                ? "bg-[var(--primary)]/15 text-[var(--primary-hover)] border border-[var(--primary)]/30"
                : doc.status === "ready"
                ? "text-[var(--foreground)] hover:bg-[var(--card-hover)]"
                : "text-[var(--muted)] cursor-default"
            }`}
          >
            <div className="flex items-center gap-2">
              {statusIcon(doc.status)}
              <span className="truncate flex-1">{doc.filename}</span>
              <span
                onClick={(e) => handleDelete(e, doc.id)}
                className="hidden group-hover:block p-1 rounded hover:bg-red-500/20 text-[var(--muted)] hover:text-[var(--danger)]"
              >
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </span>
            </div>
            {doc.status === "ready" && doc.page_count && (
              <div className="text-xs text-[var(--muted)] mt-0.5 ml-4">
                {doc.page_count} pages, {doc.chunk_count} chunks
              </div>
            )}
            {doc.status === "failed" && (
              <div className="text-xs text-[var(--danger)] mt-0.5 ml-4 truncate">
                {doc.error_message || "Processing failed"}
              </div>
            )}
            {(doc.status === "processing" || doc.status === "uploading") && (
              <div className="text-xs text-[var(--warning)] mt-0.5 ml-4">
                {doc.status === "processing" ? "Processing..." : "Uploading..."}
              </div>
            )}
          </button>
        ))}
        {filteredDocs.length === 0 && (
          <div className="text-[var(--muted)] text-sm text-center py-8">
            {search ? "No matching documents" : "No documents yet. Upload a PDF to get started."}
          </div>
        )}
      </div>
    </div>
  );
}
