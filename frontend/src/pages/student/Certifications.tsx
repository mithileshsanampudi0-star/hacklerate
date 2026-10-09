import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent, type ReactNode } from "react";
import { api, errorMessage, useApi } from "../../api/client";
import type { CertificationItem } from "../../api/types";
import { Badge, Card, Empty, PageHeader, QueryState, fmtDate } from "../../components/ui";

export function CertificationsView({ items, renderAction }: { items: CertificationItem[]; renderAction?: (c: CertificationItem) => ReactNode }) {
  if (!items.length) return <Empty>No certifications added yet.</Empty>;
  return (
    <ul className="grid gap-3 md:grid-cols-2">
      {items.map((c) => (
        <li key={c.id} className="rounded-xl border border-slate-200 bg-white p-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="font-medium text-slate-900">{c.title}</p>
              <p className="text-sm text-slate-500">
                {c.issuer} · {fmtDate(c.issue_date)}
              </p>
            </div>
            {c.verified ? <Badge color="green">Verified</Badge> : <Badge color="amber">Not verified</Badge>}
          </div>
          <div className="mt-3 flex items-center justify-between text-xs">
            {c.credential_url ? (
              <a href={c.credential_url} target="_blank" rel="noreferrer" className="text-indigo-600 hover:underline">
                View credential
              </a>
            ) : (
              <span />
            )}
            {c.verified_by && <span className="text-slate-500">by {c.verified_by}</span>}
            {renderAction?.(c)}
          </div>
        </li>
      ))}
    </ul>
  );
}

function AddCertification() {
  const qc = useQueryClient();
  const [form, setForm] = useState({ title: "", issuer: "", issue_date: "", credential_url: "" });
  const mutation = useMutation({
    mutationFn: () => api.post("/student/me/certifications", { ...form, credential_url: form.credential_url || null }),
    onSuccess: () => {
      setForm({ title: "", issuer: "", issue_date: "", credential_url: "" });
      qc.invalidateQueries({ queryKey: ["/student/me/certifications"] });
    },
  });
  const set = (k: keyof typeof form) => (e: { target: { value: string } }) => setForm({ ...form, [k]: e.target.value });

  return (
    <Card title="Add a certification">
      <form
        className="grid gap-3 md:grid-cols-2"
        onSubmit={(e: FormEvent) => {
          e.preventDefault();
          mutation.mutate();
        }}
      >
        <div>
          <label className="label">Title</label>
          <input className="input" required value={form.title} onChange={set("title")} placeholder="e.g. Python for Data Science" />
        </div>
        <div>
          <label className="label">Issued by</label>
          <input className="input" required value={form.issuer} onChange={set("issuer")} placeholder="e.g. NPTEL" />
        </div>
        <div>
          <label className="label">Issue date</label>
          <input className="input" type="date" required value={form.issue_date} onChange={set("issue_date")} max={new Date().toISOString().slice(0, 10)} />
        </div>
        <div>
          <label className="label">Credential link (optional)</label>
          <input className="input" type="url" value={form.credential_url} onChange={set("credential_url")} placeholder="https://…" />
        </div>
        <div className="flex items-center gap-3 md:col-span-2">
          <button className="btn-primary" disabled={mutation.isPending}>
            {mutation.isPending ? "Saving…" : "Add certification"}
          </button>
          {mutation.isError && <span className="text-sm text-rose-600">{errorMessage(mutation.error)}</span>}
          {mutation.isSuccess && <span className="text-sm text-emerald-600">Added. A faculty member will verify it.</span>}
        </div>
      </form>
    </Card>
  );
}

export default function Certifications() {
  const q = useApi<CertificationItem[]>("/student/me/certifications");
  return (
    <>
      <PageHeader title="Certifications" subtitle="Online courses and certificates. Faculty verify them for your placement profile." />
      <div className="space-y-5">
        <QueryState query={q}>{(d) => <CertificationsView items={d} />}</QueryState>
        <AddCertification />
      </div>
    </>
  );
}
