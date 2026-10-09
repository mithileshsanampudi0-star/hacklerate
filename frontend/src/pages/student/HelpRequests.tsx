import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, errorMessage, useApi } from "../../api/client";
import type { HelpThread } from "../../api/types";
import { HelpThreadCard } from "../../components/HelpThread";
import { Card, Empty, PageHeader, QueryState } from "../../components/ui";

function NewRequest() {
  const qc = useQueryClient();
  const courses = useApi<{ id: number; code: string; name: string }[]>("/student/me/courses");
  const [form, setForm] = useState({ subject: "", message: "", course_id: "" });
  const create = useMutation({
    mutationFn: () => api.post("/student/me/help-requests", { ...form, course_id: form.course_id ? Number(form.course_id) : null }),
    onSuccess: () => {
      setForm({ subject: "", message: "", course_id: "" });
      qc.invalidateQueries({ queryKey: ["/student/me/help-requests"] });
    },
  });

  return (
    <Card title="Ask a faculty member">
      <form
        className="grid gap-3"
        onSubmit={(e) => {
          e.preventDefault();
          create.mutate();
        }}
      >
        <div className="grid gap-3 md:grid-cols-3">
          <div className="md:col-span-2">
            <label className="label">Subject</label>
            <input className="input" required minLength={3} value={form.subject} onChange={(e) => setForm({ ...form, subject: e.target.value })} placeholder="e.g. Doubt in subnetting" />
          </div>
          <div>
            <label className="label">Course (optional)</label>
            <select className="input" value={form.course_id} onChange={(e) => setForm({ ...form, course_id: e.target.value })}>
              <option value="">General / mentor</option>
              {courses.data?.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.code} · {c.name}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div>
          <label className="label">Describe what you need help with</label>
          <textarea className="input" rows={3} required value={form.message} onChange={(e) => setForm({ ...form, message: e.target.value })} />
        </div>
        <div className="flex items-center gap-3">
          <button className="btn-primary" disabled={create.isPending}>
            {create.isPending ? "Sending…" : "Send request"}
          </button>
          <span className="text-xs text-slate-500">Course questions go to the course teacher; others go to your mentor.</span>
        </div>
        {create.isError && <p className="text-sm text-rose-600">{errorMessage(create.error)}</p>}
      </form>
    </Card>
  );
}

export default function HelpRequests() {
  const qc = useQueryClient();
  const q = useApi<HelpThread[]>("/student/me/help-requests");
  return (
    <>
      <PageHeader title="Ask for help" subtitle="Study doubts, attendance issues or anything you need support with" />
      <div className="space-y-5">
        <NewRequest />
        <QueryState query={q}>
          {(threads) =>
            threads.length === 0 ? (
              <Empty>You have not raised any requests yet.</Empty>
            ) : (
              <ul className="space-y-3">
                {threads.map((t) => (
                  <HelpThreadCard
                    key={t.id}
                    thread={t}
                    replyUrl={`/student/me/help-requests/${t.id}/replies`}
                    onChanged={() => qc.invalidateQueries({ queryKey: ["/student/me/help-requests"] })}
                  />
                ))}
              </ul>
            )
          }
        </QueryState>
      </div>
    </>
  );
}
