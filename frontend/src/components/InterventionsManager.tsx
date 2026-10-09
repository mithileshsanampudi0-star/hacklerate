import { useState } from "react";
import { api } from "../api/client";
import { Card, Badge } from "./ui";
import type { InterventionItem } from "../api/types";

interface Props {
  interventions: InterventionItem[];
  isFaculty?: boolean;
  studentId?: number;
  onRefresh?: () => void;
}

const URGENCY_COLORS = {
  critical: "red",
  high: "amber",
  medium: "blue",
  low: "gray",
} as const;

const STATUS_COLORS = {
  pending: "amber",
  in_progress: "blue",
  completed: "green",
  dismissed: "gray",
} as const;

export function InterventionsManager({ interventions, isFaculty = false, studentId, onRefresh }: Props) {
  const [modalOpen, setModalOpen] = useState(false);
  const [busy, setBusy] = useState(false);

  // New intervention form state
  const [category, setCategory] = useState("academic");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [urgency, setUrgency] = useState("high");
  const [step1, setStep1] = useState("");
  const [step2, setStep2] = useState("");
  const [targetDate, setTargetDate] = useState("");

  async function handleAssignSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!studentId) return;
    setBusy(true);
    try {
      const actionSteps = [step1, step2].filter((s) => s.trim().length > 0);
      await api.post("/interventions", {
        student_id: studentId,
        category,
        title,
        description,
        urgency,
        action_steps: actionSteps,
        target_date: targetDate || null,
      });
      setModalOpen(false);
      setTitle("");
      setDescription("");
      setStep1("");
      setStep2("");
      onRefresh?.();
    } catch {
      alert("Failed to assign intervention. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  async function handleStatusChange(id: number, newStatus: string) {
    try {
      await api.patch(`/interventions/${id}/status`, { status: newStatus });
      onRefresh?.();
    } catch {
      alert("Failed to update status.");
    }
  }

  return (
    <Card
      title={
        <div className="flex items-center gap-2">
          <span>Active Intervention Plans</span>
          <span className="rounded-full bg-indigo-100 px-2 py-0.5 text-xs font-semibold text-indigo-700">
            {interventions.length}
          </span>
        </div>
      }
      action={
        isFaculty && studentId ? (
          <button
            onClick={() => setModalOpen(true)}
            className="btn-primary text-xs py-1.5 px-3"
          >
            + Assign Intervention
          </button>
        ) : null
      }
    >
      {interventions.length === 0 ? (
        <div className="py-8 text-center text-slate-400 text-xs">
          No active interventions assigned. Student is in good standing.
        </div>
      ) : (
        <div className="space-y-3">
          {interventions.map((it) => (
            <div
              key={it.id}
              className="rounded-xl border border-slate-200 bg-white p-4 shadow-2xs hover:border-slate-300 transition"
            >
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-sm text-slate-900">{it.title}</span>
                    <Badge color={URGENCY_COLORS[it.urgency]}>{it.urgency.toUpperCase()}</Badge>
                    <Badge color={STATUS_COLORS[it.status]}>{it.status.replace("_", " ")}</Badge>
                  </div>
                  <p className="mt-1 text-xs text-slate-600">{it.description}</p>
                </div>

                <div className="flex items-center gap-2 text-xs">
                  {it.status === "pending" && (
                    <button
                      onClick={() => handleStatusChange(it.id, "in_progress")}
                      className="rounded-md border border-indigo-200 bg-indigo-50 px-2.5 py-1 font-medium text-indigo-700 hover:bg-indigo-100"
                    >
                      Start Plan
                    </button>
                  )}
                  {it.status === "in_progress" && (
                    <button
                      onClick={() => handleStatusChange(it.id, "completed")}
                      className="rounded-md border border-emerald-200 bg-emerald-50 px-2.5 py-1 font-medium text-emerald-700 hover:bg-emerald-100"
                    >
                      Mark Completed
                    </button>
                  )}
                </div>
              </div>

              {it.action_steps && it.action_steps.length > 0 && (
                <div className="mt-3 border-t border-slate-100 pt-2.5">
                  <p className="text-[11px] font-semibold text-slate-500 uppercase">Action Steps Checklist:</p>
                  <ul className="mt-1 space-y-1">
                    {it.action_steps.map((step, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-xs text-slate-700">
                        <span className="text-indigo-500 font-bold">✓</span>
                        <span>{step}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="mt-2.5 flex items-center justify-between text-[11px] text-slate-400">
                <span>Category: <strong className="text-slate-600 capitalize">{it.category}</strong></span>
                {it.target_date && <span>Target: {new Date(it.target_date).toLocaleDateString()}</span>}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Assign Intervention Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4 backdrop-blur-xs">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl">
            <h3 className="text-base font-bold text-slate-900 mb-4">Assign Targeted Student Intervention</h3>
            <form onSubmit={handleAssignSubmit} className="space-y-3.5">
              <div>
                <label className="label">Category</label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="input"
                >
                  <option value="academic">Academic Remedial</option>
                  <option value="attendance">Attendance Recovery</option>
                  <option value="placement">Placement Acceleration</option>
                  <option value="counseling">Counseling & Guidance</option>
                </select>
              </div>

              <div>
                <label className="label">Intervention Title</label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Remedial Tutoring for Core Courses"
                  className="input"
                />
              </div>

              <div>
                <label className="label">Description & Rationale</label>
                <textarea
                  required
                  rows={2}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Detail the specific weakness and objectives..."
                  className="input"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="label">Urgency</label>
                  <select
                    value={urgency}
                    onChange={(e) => setUrgency(e.target.value)}
                    className="input"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>
                <div>
                  <label className="label">Target Completion Date</label>
                  <input
                    type="date"
                    value={targetDate}
                    onChange={(e) => setTargetDate(e.target.value)}
                    className="input"
                  />
                </div>
              </div>

              <div>
                <label className="label">Action Step 1</label>
                <input
                  type="text"
                  value={step1}
                  onChange={(e) => setStep1(e.target.value)}
                  placeholder="e.g. Attend Friday remedial classes"
                  className="input mb-2"
                />
                <label className="label">Action Step 2 (Optional)</label>
                <input
                  type="text"
                  value={step2}
                  onChange={(e) => setStep2(e.target.value)}
                  placeholder="e.g. Submit practice problems to mentor"
                  className="input"
                />
              </div>

              <div className="mt-5 flex justify-end gap-2 border-t border-slate-100 pt-4">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="btn-secondary text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={busy}
                  className="btn-primary text-xs"
                >
                  {busy ? "Saving…" : "Assign Intervention"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </Card>
  );
}
