import { useMutation } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { api, errorMessage } from "../api/client";
import type { HelpThread } from "../api/types";
import { StatusBadge, fmtDate } from "./ui";

/** One help-request conversation. Used by students and faculty with different reply URLs. */
export function HelpThreadCard({
  thread,
  replyUrl,
  onChanged,
  actions,
  studentLink,
}: {
  thread: HelpThread;
  replyUrl: string;
  onChanged: () => void;
  actions?: ReactNode;
  studentLink?: string;
}) {
  const [open, setOpen] = useState(thread.status !== "resolved");
  const [message, setMessage] = useState("");
  const reply = useMutation({
    mutationFn: () => api.post(replyUrl, { message }),
    onSuccess: () => {
      setMessage("");
      onChanged();
    },
  });

  return (
    <li className="rounded-xl border border-slate-200 bg-white">
      <button className="flex w-full items-start justify-between gap-3 p-4 text-left" onClick={() => setOpen((o) => !o)}>
        <div>
          <p className="font-medium text-slate-900">{thread.subject}</p>
          <p className="mt-0.5 text-xs text-slate-500">
            {studentLink ? `${thread.student_name} · ` : ""}
            {thread.course_code ? `${thread.course_code} · ` : ""}
            {fmtDate(thread.created_at)}
            {thread.assigned_to ? ` · with ${thread.assigned_to}` : " · unassigned"}
          </p>
        </div>
        <StatusBadge status={thread.status} />
      </button>

      {open && (
        <div className="border-t border-slate-100 p-4">
          {studentLink && (
            <Link to={studentLink} className="mb-3 inline-block text-xs text-indigo-600 hover:underline">
              Open {thread.student_name}'s profile →
            </Link>
          )}
          <div className="space-y-3">
            <Bubble mine={!studentLink} author={thread.student_name ?? "Student"} date={thread.created_at} text={thread.message} />
            {thread.replies.map((r) => (
              <Bubble key={r.id} mine={studentLink ? !r.author_is_student : r.author_is_student} author={r.author} date={r.created_at} text={r.message} />
            ))}
          </div>

          <form
            className="mt-4 flex flex-col gap-2 sm:flex-row"
            onSubmit={(e) => {
              e.preventDefault();
              if (message.trim()) reply.mutate();
            }}
          >
            <textarea className="input min-h-[42px] flex-1" rows={1} value={message} onChange={(e) => setMessage(e.target.value)} placeholder="Write a reply…" />
            <button className="btn-primary" disabled={reply.isPending || !message.trim()}>
              {reply.isPending ? "Sending…" : "Reply"}
            </button>
          </form>
          {reply.isError && <p className="mt-2 text-sm text-rose-600">{errorMessage(reply.error)}</p>}
          {actions && <div className="mt-3 flex flex-wrap gap-2">{actions}</div>}
        </div>
      )}
    </li>
  );
}

function Bubble({ mine, author, date, text }: { mine: boolean; author: string; date: string; text: string }) {
  return (
    <div className={`flex ${mine ? "justify-end" : "justify-start"}`}>
      <div className={`max-w-[85%] rounded-xl px-3 py-2 text-sm ${mine ? "bg-indigo-600 text-white" : "bg-slate-100 text-slate-800"}`}>
        <p className={`mb-0.5 text-xs ${mine ? "text-indigo-100" : "text-slate-500"}`}>
          {author} · {fmtDate(date)}
        </p>
        <p className="whitespace-pre-wrap">{text}</p>
      </div>
    </div>
  );
}
