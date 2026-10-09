import { Card, Badge, fmtDate } from "./ui";
import type { AcademicRiskData } from "../api/types";

const RISK_BADGES = {
  low: { color: "green" as const, label: "Low Risk" },
  medium: { color: "amber" as const, label: "Medium Risk" },
  high: { color: "red" as const, label: "High Risk" },
};

export function RiskAnalysisCard({ data }: { data: AcademicRiskData }) {
  const badgeInfo = RISK_BADGES[data.risk_category] || { color: "gray", label: data.risk_category };
  const scoreColor =
    data.risk_category === "high"
      ? "text-rose-600"
      : data.risk_category === "medium"
        ? "text-amber-600"
        : "text-emerald-600";

  return (
    <Card
      title={
        <div className="flex items-center gap-2">
          <span>Academic Risk Estimate</span>
          <Badge color={badgeInfo.color}>{badgeInfo.label}</Badge>
        </div>
      }
      action={
        <span className="text-xs text-slate-400 font-mono">
          Scoring version: {data.model_version}
        </span>
      }
    >
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-xl bg-slate-50 border border-slate-100">
        <div>
          <p className="text-xs uppercase font-semibold text-slate-500">Rule-based risk score</p>
          <div className="flex items-baseline gap-2 mt-1">
            <span className={`text-3xl font-extrabold tabular-nums ${scoreColor}`}>
              {data.risk_probability} / 100
            </span>
            <span className="text-xs font-medium text-slate-600">
              {data.risk_category.toUpperCase()} RISK
            </span>
          </div>
          <p className="mt-1 text-xs text-slate-600">
            An additive score from current student indicators, not a calibrated probability or a guaranteed outcome.
          </p>
        </div>

        <div className="text-xs text-slate-500 sm:text-right">
          <p className="font-semibold text-slate-700">Support signal for review</p>
          <p className="text-[11px] mt-0.5">
            {data.prediction_timestamp ? `Updated ${fmtDate(data.prediction_timestamp)}` : "Based on available records"}
          </p>
        </div>
      </div>

      <div className="mt-5">
        <p className="text-xs font-semibold text-slate-800 uppercase tracking-wide mb-2.5">
          What changes this score
        </p>
        <div className="space-y-2">
          {data.contributing_factors.map((f, i) => (
            <div
              key={i}
              className={`flex items-start justify-between p-2.5 rounded-lg border text-xs ${
                f.direction === "negative"
                  ? "bg-rose-50/60 border-rose-100 text-slate-800"
                  : "bg-emerald-50/60 border-emerald-100 text-slate-800"
              }`}
            >
              <div className="flex items-start gap-2">
                <span className={`mt-0.5 text-sm ${f.direction === "negative" ? "text-rose-600" : "text-emerald-600"}`}>
                  {f.direction === "negative" ? "▲" : "▼"}
                </span>
                <div>
                  <span className="font-semibold text-slate-900">
                    {f.direction === "negative" ? "Raises risk · " : "Lowers risk · "}
                    {f.factor}:{" "}
                  </span>
                  <span className="text-slate-700">{f.detail}</span>
                </div>
              </div>
              <span
                className={`font-semibold tabular-nums ml-2 shrink-0 ${
                  f.direction === "negative" ? "text-rose-600" : "text-emerald-600"
                }`}
              >
                {f.impact > 0 ? `+${f.impact} pts` : `${f.impact} pts`}
              </span>
            </div>
          ))}
        </div>
      </div>

      {data.suggested_interventions && data.suggested_interventions.length > 0 && (
        <div className="mt-5 border-t border-slate-100 pt-3">
          <p className="text-xs font-semibold text-slate-800 uppercase tracking-wide mb-2">
            Suggested Interventions & Mitigation
          </p>
          <ul className="space-y-1.5">
            {data.suggested_interventions.map((step, idx) => (
              <li key={idx} className="flex items-start gap-2 text-xs text-slate-700">
                <span className="text-indigo-600 font-bold">•</span>
                <span>{step}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <details className="mt-4 border-t border-slate-100 pt-3">
        <summary className="min-h-11 cursor-pointer py-2 text-xs font-semibold text-indigo-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500">
          How to interpret this score
        </summary>
        <p className="text-xs leading-relaxed text-slate-600">
          The score adds rule-based contributions from attendance, backlogs, GPA trends, internal marks, missing
          assignments, and learning-platform activity. Its category uses institution-configured thresholds. Review
          the underlying records with the student before deciding on support; this score is not a diagnosis or an
          automated decision.
        </p>
      </details>
    </Card>
  );
}
