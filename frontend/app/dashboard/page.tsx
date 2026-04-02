"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import DocumentSidebar from "@/components/document-sidebar";
import ChatArea from "@/components/chat-area";

export default function DashboardPage() {
  const { user, token, logout, loading } = useAuth();
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    if (!loading && !token) {
      router.push("/login");
    }
  }, [token, loading, router]);

  if (loading || !token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--background)]">
        <div className="animate-pulse text-[var(--muted)]">Loading...</div>
      </div>
    );
  }

  return (
    <div className="h-screen flex bg-[var(--background)]">
      {/* Sidebar */}
      <DocumentSidebar
        selectedDocId={selectedDocId}
        onSelectDoc={setSelectedDocId}
      />

      {/* Main content */}
      <div className="flex-1 flex flex-col">
        {/* Top bar */}
        <div className="h-14 border-b border-[var(--border)] flex items-center justify-between px-6">
          <div className="flex items-center gap-2">
            <span className="text-sm text-[var(--muted)]">Querying:</span>
            <span className="text-sm font-medium text-white">
              {selectedDocId ? "Selected document" : "All documents"}
            </span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-[var(--muted)]">{user?.email}</span>
            <button
              onClick={logout}
              className="text-sm text-[var(--muted)] hover:text-[var(--danger)] transition-colors"
            >
              Sign out
            </button>
          </div>
        </div>

        {/* Chat */}
        <ChatArea selectedDocId={selectedDocId} />
      </div>
    </div>
  );
}
