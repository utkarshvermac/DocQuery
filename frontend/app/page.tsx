"use client";

import { useState } from "react";
import ChatWindow from "@/components/ChatWindow";
import Sidebar from "@/components/Sidebar";
import { useChat } from "@/hooks/useChat";
import { useDocuments } from "@/hooks/useDocuments";

export default function Home() {
  const docs = useDocuments();
  const chat = useChat(docs.activeIds, docs.documents.length);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar docs={docs} open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <ChatWindow
        messages={chat.messages}
        loading={chat.loading}
        documents={docs.documents}
        activeCount={docs.activeIds.length}
        onSend={chat.send}
        onReset={chat.reset}
        onOpenSidebar={() => setSidebarOpen(true)}
      />
    </div>
  );
}
