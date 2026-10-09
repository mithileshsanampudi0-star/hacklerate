import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../api/client";
import { Card, Loading, PageHeader } from "../../components/ui";
import type { SystemSettingsData } from "../../api/types";

export default function Settings() {
  const { data, isLoading, refetch } = useQuery({
    queryKey: ["admin", "settings"],
    queryFn: () => api.get<SystemSettingsData>("/admin/settings").then((r) => r.data),
  });

  const [ssWeights, setSsWeights] = useState<Record<string, number>>({});
  const [prWeights, setPrWeights] = useState<Record<string, number>>({});
  const [thresholds, setThresholds] = useState<Record<string, number>>({});
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    if (data) {
      setSsWeights(data.success_score_weights || {});
      setPrWeights(data.placement_readiness_weights || {});
      setThresholds(data.thresholds || {});
    }
  }, [data]);

  if (isLoading || !data) return <Loading full />;

  const ssSum = Math.round(Object.values(ssWeights).reduce((a, b) => a + b, 0) * 100);
  const prSum = Math.round(Object.values(prWeights).reduce((a, b) => a + b, 0) * 100);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    if (ssSum !== 100) {
      alert(`Success Score weights must sum to exactly 100% (currently ${ssSum}%).`);
      return;
    }
    if (prSum !== 100) {
      alert(`Placement Readiness weights must sum to exactly 100% (currently ${prSum}%).`);
      return;
    }

    setBusy(true);
    setMsg(null);
    try {
      await api.put("/admin/settings", {
        success_score_weights: ssWeights,
        placement_readiness_weights: prWeights,
        thresholds: thresholds,
      });
      setMsg("Institutional scoring weights and thresholds saved successfully!");
      refetch();
    } catch {
      alert("Failed to save settings.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6 max-w-4xl">
      <PageHeader
        title="Scoring Weights & Threshold Configuration"
        subtitle="Manage weighted indicator formulas, risk boundaries, and readiness benchmarks"
      />

      {msg && (
        <div className="rounded-xl bg-emerald-50 border border-emerald-200 p-4 text-xs font-semibold text-emerald-800 flex items-center gap-2">
          <span>✓</span> {msg}
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        {/* Student Success Score Weights */}
        <Card
          title="Student Success Score Formula (7 Weighted Indicators)"
          action={
            <span
              className={`text-xs font-bold tabular-nums px-2.5 py-1 rounded-full ${
                ssSum === 100 ? "bg-emerald-100 text-emerald-800" : "bg-rose-100 text-rose-800"
              }`}
            >
              Total: {ssSum}% {ssSum !== 100 && "(Must equal 100%)"}
            </span>
          }
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {Object.entries(ssWeights).map(([key, val]) => (
              <div key={key}>
                <label className="label capitalize flex justify-between">
                  <span>{key} Weight</span>
                  <span className="font-semibold text-slate-800">{Math.round(val * 100)}%</span>
                </label>
                <input
                  type="number"
                  step="1"
                  min="0"
                  max="100"
                  value={Math.round(val * 100)}
                  onChange={(e) => {
                    const parsed = parseFloat(e.target.value) || 0;
                    setSsWeights((prev) => ({ ...prev, [key]: parsed / 100.0 }));
                  }}
                  className="input"
                />
              </div>
            ))}
          </div>
        </Card>

        {/* Placement Readiness Score Weights */}
        <Card
          title="Placement Readiness Formula (5 Weighted Indicators)"
          action={
            <span
              className={`text-xs font-bold tabular-nums px-2.5 py-1 rounded-full ${
                prSum === 100 ? "bg-emerald-100 text-emerald-800" : "bg-rose-100 text-rose-800"
              }`}
            >
              Total: {prSum}% {prSum !== 100 && "(Must equal 100%)"}
            </span>
          }
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {Object.entries(prWeights).map(([key, val]) => (
              <div key={key}>
                <label className="label capitalize flex justify-between">
                  <span>{key.replace("_", " ")} Weight</span>
                  <span className="font-semibold text-slate-800">{Math.round(val * 100)}%</span>
                </label>
                <input
                  type="number"
                  step="1"
                  min="0"
                  max="100"
                  value={Math.round(val * 100)}
                  onChange={(e) => {
                    const parsed = parseFloat(e.target.value) || 0;
                    setPrWeights((prev) => ({ ...prev, [key]: parsed / 100.0 }));
                  }}
                  className="input"
                />
              </div>
            ))}
          </div>
        </Card>

        {/* Risk & Benchmark Thresholds */}
        <Card title="Risk & Benchmark Cutoff Thresholds">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {Object.entries(thresholds).map(([key, val]) => (
              <div key={key}>
                <label className="label capitalize">{key.replace(/_/g, " ")}</label>
                <input
                  type="number"
                  step="0.5"
                  value={val}
                  onChange={(e) => {
                    const parsed = parseFloat(e.target.value) || 0;
                    setThresholds((prev) => ({ ...prev, [key]: parsed }));
                  }}
                  className="input"
                />
              </div>
            ))}
          </div>
        </Card>

        <div className="flex justify-end">
          <button type="submit" disabled={busy} className="btn-primary px-6 py-2 shadow-sm">
            {busy ? "Saving Settings…" : "Save Configuration"}
          </button>
        </div>
      </form>
    </div>
  );
}
