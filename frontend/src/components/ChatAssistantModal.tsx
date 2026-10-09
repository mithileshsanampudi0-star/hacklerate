import { useState, useRef, useEffect } from "react";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";

interface ChatMessage {
  id: string;
  sender: "user" | "assistant";
  text: string;
  sources?: string[];
  timestamp: string;
}

export function ChatAssistantModal() {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Suggested prompts based on role
  const suggestedPrompts =
    user?.role === "student"
      ? [
          "What is my success score breakdown?",
          "How many classes do I need to attend to reach 75%?",
          "What are my placement readiness strengths and gaps?",
          "Why am I at risk and what can I do?",
          "Do I have any pending assignments?",
        ]
      : user?.role === "faculty"
      ? [
          "Which students need immediate intervention?",
          "Which students have low placement readiness?",
          "Which students have incomplete assignments?",
          "What are the department's active interventions?",
          "Explain academic risk for student 24cse007",
        ]
      : [
          "Which department has the highest average CGPA?",
          "Give me an overview of campus placement readiness",
          "How many students are below 75% attendance?",
          "Which students need immediate intervention?",
        ];

  useEffect(() => {
    if (open && messages.length === 0) {
      setMessages([
        {
          id: "welcome",
          sender: "assistant",
          text: `Hello ${user?.name || "there"}! I am your **Campus Analytics Assistant**. Ask natural-language questions regarding academic progress, risk factors, placement readiness, or interventions. All data is grounded in verified college records.`,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
          sources: ["SmartCampusAnalyticsEngine"],
        },
      ]);
    }
  }, [open, user, messages.length]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, busy]);

  async function handleSend(textToSend?: string) {
    const q = textToSend || input;
    if (!q.trim() || busy) return;

    const userMsg: ChatMessage = {
      id: String(Date.now()),
      sender: "user",
      text: q.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setBusy(true);

    try {
      const res = await api.post<{ answer: string; sources: string[] }>("/chat/ask", {
        message: q.trim(),
      });

      const assistantMsg: ChatMessage = {
        id: String(Date.now() + 1),
        sender: "assistant",
        text: res.data.answer,
        sources: res.data.sources,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: String(Date.now() + 1),
          sender: "assistant",
          text: "I encountered an error retrieving data for your query. Please verify your connection or try rephrasing.",
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      {/* Floating Action Trigger Button */}
      <button
        onClick={() => setOpen(true)}
        className="fixed bottom-6 right-6 z-40 flex items-center gap-2 rounded-full bg-gradient-to-r from-indigo-600 to-purple-600 px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-200 hover:from-indigo-700 hover:to-purple-700 hover:shadow-xl transition-all"
        aria-label="Open Campus Assistant"
      >
        <span className="flex h-5 w-5 items-center justify-center rounded-full bg-white/20 text-xs">✨</span>
        <span>Campus Assistant</span>
      </button>

      {/* Slide-over Drawer */}
      {open && (
        <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/40 backdrop-blur-xs flex justify-end">
          <div className="w-full max-w-md bg-white shadow-2xl flex flex-col h-full animate-in slide-in-from-right duration-200">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-slate-200 px-5 py-3.5 bg-gradient-to-r from-indigo-50/80 to-purple-50/80">
              <div className="flex items-center gap-2.5">
                <span className="grid h-8 w-8 place-items-center rounded-lg bg-indigo-600 text-sm font-bold text-white shadow-xs">SC</span>
                <div>
                  <h3 className="text-sm font-bold text-slate-900">Campus Analytics Assistant</h3>
                  <p className="text-[11px] text-slate-500">Grounded Q&A • RBAC Enforced</p>
                </div>
              </div>
              <button
                onClick={() => setOpen(false)}
                className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition"
              >
                ✕
              </button>
            </div>

            {/* Chat Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4" ref={scrollRef}>
              {messages.map((m) => (
                <div
                  key={m.id}
                  className={`flex flex-col ${m.sender === "user" ? "items-end" : "items-start"}`}
                >
                  <div
                    className={`max-w-[88%] rounded-2xl px-4 py-2.5 text-xs leading-relaxed ${
                      m.sender === "user"
                        ? "bg-indigo-600 text-white rounded-br-xs shadow-sm"
                        : "bg-slate-100 text-slate-800 rounded-bl-xs border border-slate-200/80"
                    }`}
                  >
                    <div className="whitespace-pre-wrap">{m.text}</div>
                    {m.sources && m.sources.length > 0 && (
                      <div className="mt-2 border-t border-slate-200/60 pt-1.5 text-[10px] text-slate-500">
                        <span className="font-medium text-slate-600">Verified Sources:</span> {m.sources.join(", ")}
                      </div>
                    )}
                  </div>
                  <span className="mt-1 px-1 text-[10px] text-slate-400">{m.timestamp}</span>
                </div>
              ))}

              {busy && (
                <div className="flex items-center gap-2 text-xs text-slate-500 bg-slate-50 rounded-lg p-2.5 w-fit border border-slate-100">
                  <span className="animate-spin text-sm">✦</span>
                  <span>Analyzing campus database & model records…</span>
                </div>
              )}
            </div>

            {/* Suggested Prompts */}
            <div className="border-t border-slate-100 bg-slate-50/60 p-2.5">
              <p className="mb-1.5 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Suggested Questions</p>
              <div className="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto">
                {suggestedPrompts.slice(0, 4).map((prompt, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSend(prompt)}
                    disabled={busy}
                    className="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[11px] text-slate-700 hover:border-indigo-300 hover:bg-indigo-50/50 hover:text-indigo-700 transition"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>

            {/* Input Form */}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSend();
              }}
              className="border-t border-slate-200 p-3 bg-white flex items-center gap-2"
            >
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about academic risks, scores, or interventions…"
                className="input text-xs py-2"
                disabled={busy}
              />
              <button
                type="submit"
                disabled={busy || !input.trim()}
                className="btn-primary shrink-0 py-2 px-3 text-xs"
              >
                Send
              </button>
            </form>
          </div>
        </div>
      )}
    </>
  );
}
