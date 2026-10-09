import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, errorMessage, useApi } from "../../api/client";
import type { FeedbackFormItem, FeedbackForms } from "../../api/types";
import { Badge, Card, Empty, PageHeader, QueryState, fmtDate } from "../../components/ui";

/** Read-only status list (used on the faculty student page too). */
export function FeedbackStatusView({ data }: { data: FeedbackForms }) {
  return (
    <div className="grid gap-5 md:grid-cols-2">
      <Card title={`Pending (${data.pending.length})`}>
        {data.pending.length === 0 ? (
          <Empty>Nothing pending.</Empty>
        ) : (
          <ul className="space-y-2 text-sm">
            {data.pending.map((f) => (
              <li key={f.id} className="flex items-center justify-between gap-2">
                <span>{f.title}</span>
                {f.overdue ? <Badge color="red">Overdue</Badge> : <span className="text-xs text-slate-500">due {fmtDate(f.due_date)}</span>}
              </li>
            ))}
          </ul>
        )}
      </Card>
      <Card title={`Completed (${data.completed.length})`}>
        {data.completed.length === 0 ? (
          <Empty>None yet.</Empty>
        ) : (
          <ul className="space-y-2 text-sm">
            {data.completed.map((f) => (
              <li key={f.id} className="flex items-center justify-between gap-2">
                <span>{f.title}</span>
                <span className="text-xs text-slate-500">{fmtDate(f.submitted_at)}</span>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}

function FillForm({ form, onDone }: { form: FeedbackFormItem; onDone: () => void }) {
  const [answers, setAnswers] = useState<Record<string, number | string>>({});
  const submit = useMutation({
    mutationFn: () => api.post(`/student/me/feedback-forms/${form.id}`, { answers }),
    onSuccess: onDone,
  });
  const ready = form.questions.every((q) => q.type === "text" || typeof answers[q.id] === "number");

  return (
    <form
      className="mt-4 space-y-4 border-t border-slate-100 pt-4"
      onSubmit={(e) => {
        e.preventDefault();
        submit.mutate();
      }}
    >
      {form.questions.map((q, i) => (
        <div key={q.id}>
          <p className="mb-2 text-sm text-slate-800">
            {i + 1}. {q.text}
          </p>
          {q.type === "rating" ? (
            <div className="flex flex-wrap gap-2" role="radiogroup">
              {[1, 2, 3, 4, 5].map((n) => (
                <button
                  type="button"
                  key={n}
                  role="radio"
                  aria-checked={answers[q.id] === n}
                  onClick={() => setAnswers({ ...answers, [q.id]: n })}
                  className={`h-9 w-9 rounded-lg border text-sm font-medium transition ${
                    answers[q.id] === n ? "border-indigo-600 bg-indigo-600 text-white" : "border-slate-300 bg-white text-slate-700 hover:border-indigo-400"
                  }`}
                >
                  {n}
                </button>
              ))}
              <span className="self-center text-xs text-slate-400">1 = poor, 5 = excellent</span>
            </div>
          ) : (
            <textarea className="input" rows={2} value={(answers[q.id] as string) ?? ""} onChange={(e) => setAnswers({ ...answers, [q.id]: e.target.value })} />
          )}
        </div>
      ))}
      <div className="flex items-center gap-3">
        <button className="btn-primary" disabled={!ready || submit.isPending}>
          {submit.isPending ? "Submitting…" : "Submit feedback"}
        </button>
        {!ready && <span className="text-xs text-slate-500">Rate every question to submit.</span>}
        {submit.isError && <span className="text-sm text-rose-600">{errorMessage(submit.error)}</span>}
      </div>
    </form>
  );
}

function FeedbackPage({ data }: { data: FeedbackForms }) {
  const qc = useQueryClient();
  const [openId, setOpenId] = useState<number | null>(null);

  return (
    <div className="space-y-5">
      <Card title={`Waiting for your response (${data.pending.length})`}>
        {data.pending.length === 0 ? (
          <Empty>All caught up. Thank you for your feedback!</Empty>
        ) : (
          <ul className="space-y-3">
            {data.pending.map((f) => (
              <li key={f.id} className="rounded-lg border border-slate-200 p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="font-medium text-slate-900">{f.title}</p>
                    <p className="text-xs text-slate-500">
                      {f.faculty ? `${f.faculty} · ` : ""}
                      {f.questions.length} questions · due {fmtDate(f.due_date)}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {f.overdue && <Badge color="red">Overdue</Badge>}
                    <button className="btn-secondary px-3 py-1.5" onClick={() => setOpenId(openId === f.id ? null : f.id)}>
                      {openId === f.id ? "Close" : "Fill now"}
                    </button>
                  </div>
                </div>
                {openId === f.id && (
                  <FillForm
                    form={f}
                    onDone={() => {
                      setOpenId(null);
                      qc.invalidateQueries({ queryKey: ["/student/me/feedback-forms"] });
                      qc.invalidateQueries({ queryKey: ["/student/me/dashboard"] });
                    }}
                  />
                )}
              </li>
            ))}
          </ul>
        )}
      </Card>
      <Card title={`Submitted (${data.completed.length})`}>
        {data.completed.length === 0 ? (
          <Empty>No feedback submitted yet.</Empty>
        ) : (
          <ul className="divide-y divide-slate-100 text-sm">
            {data.completed.map((f) => (
              <li key={f.id} className="flex items-center justify-between py-2">
                <span>{f.title}</span>
                <span className="text-xs text-slate-500">Submitted {fmtDate(f.submitted_at)}</span>
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}

export default function Feedback() {
  const q = useApi<FeedbackForms>("/student/me/feedback-forms");
  return (
    <>
      <PageHeader title="Feedback forms" subtitle="Help your teachers improve their courses. Please submit before the due date." />
      <QueryState query={q}>{(d) => <FeedbackPage data={d} />}</QueryState>
    </>
  );
}
