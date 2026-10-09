import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { api, errorMessage } from "../../api/client";
import { Card } from "../../components/ui";

const CATEGORIES = [
  { id: "academic", label: "Academic" },
  { id: "behaviour", label: "Behaviour" },
  { id: "attendance", label: "Attendance" },
  { id: "appreciation", label: "Appreciation" },
];

export function WriteRemark({ studentId, studentName, onSaved }: { studentId: number; studentName: string; onSaved: () => void }) {
  const [category, setCategory] = useState("academic");
  const [remark, setRemark] = useState("");
  const [privateNote, setPrivateNote] = useState(false);
  const save = useMutation({
    mutationFn: () =>
      api.post(`/faculty/students/${studentId}/remarks`, {
        category,
        remark,
        visibility: privateNote ? "faculty_only" : "student",
      }),
    onSuccess: () => {
      setRemark("");
      onSaved();
    },
  });

  return (
    <Card title={`Write feedback for ${studentName}`}>
      <form
        className="space-y-3"
        onSubmit={(e) => {
          e.preventDefault();
          save.mutate();
        }}
      >
        <div className="flex flex-wrap gap-2">
          {CATEGORIES.map((c) => (
            <button type="button" key={c.id} onClick={() => setCategory(c.id)} className={category === c.id ? "btn-primary px-3 py-1.5" : "btn-secondary px-3 py-1.5"}>
              {c.label}
            </button>
          ))}
        </div>
        <textarea
          className="input"
          rows={3}
          required
          minLength={3}
          value={remark}
          onChange={(e) => setRemark(e.target.value)}
          placeholder="Observations on behaviour, study habits, or a plan to help them improve…"
        />
        <div className="flex flex-wrap items-center justify-between gap-3">
          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input type="checkbox" checked={privateNote} onChange={(e) => setPrivateNote(e.target.checked)} />
            Private note (visible to faculty only)
          </label>
          <button className="btn-primary" disabled={save.isPending || remark.trim().length < 3}>
            {save.isPending ? "Saving…" : "Save remark"}
          </button>
        </div>
        {save.isError && <p className="text-sm text-rose-600">{errorMessage(save.error)}</p>}
        {save.isSuccess && <p className="text-sm text-emerald-600">Saved{privateNote ? "" : ". The student can see it on their portal"}.</p>}
      </form>
    </Card>
  );
}
