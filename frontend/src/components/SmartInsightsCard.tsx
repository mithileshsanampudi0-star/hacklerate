import { Link } from "react-router-dom";
import { Card, Badge } from "./ui";
import type { SmartInsightItem } from "../api/types";

const SEVERITY_MAP = {
  critical: { bg: "bg-rose-50/70", border: "border-rose-200", badge: "red" as const, icon: "🚨" },
  warning: { bg: "bg-amber-50/70", border: "border-amber-200", badge: "amber" as const, icon: "⚠️" },
  success: { bg: "bg-emerald-50/70", border: "border-emerald-200", badge: "green" as const, icon: "✨" },
  info: { bg: "bg-indigo-50/70", border: "border-indigo-200", badge: "blue" as const, icon: "💡" },
};

export function SmartInsightsCard({ insights }: { insights: SmartInsightItem[] }) {
  if (!insights || insights.length === 0) {
    return null;
  }

  return (
    <Card
      title={
        <div className="flex items-center gap-2">
          <span>Smart Campus Insights</span>
          <Badge color="blue">Automated Intelligence</Badge>
        </div>
      }
      action={
        <span className="text-xs text-slate-400">Grounded in Live Records</span>
      }
    >
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
        {insights.map((ins) => {
          const style = SEVERITY_MAP[ins.severity] || SEVERITY_MAP.info;

          return (
            <div
              key={ins.id}
              className={`rounded-xl border p-4 flex flex-col justify-between ${style.bg} ${style.border}`}
            >
              <div>
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-1.5">
                    <span className="text-base">{style.icon}</span>
                    <h4 className="text-xs font-bold text-slate-900 leading-snug">{ins.title}</h4>
                  </div>
                  {ins.stat && (
                    <span className="shrink-0 rounded-md bg-white/80 px-2 py-0.5 text-[11px] font-bold text-slate-800 shadow-2xs">
                      {ins.stat}
                    </span>
                  )}
                </div>

                <p className="mt-2 text-xs text-slate-700 leading-relaxed">{ins.summary}</p>

                <div className="mt-2.5 rounded-lg bg-white/60 p-2 text-[11px] text-slate-600 border border-white/80">
                  <strong className="text-slate-800">Recommendation: </strong>
                  {ins.recommendation}
                </div>
              </div>

              {ins.action_link && (
                <div className="mt-3 text-right">
                  <Link
                    to={ins.action_link}
                    className="text-xs font-semibold text-indigo-700 hover:text-indigo-900 hover:underline inline-flex items-center gap-1"
                  >
                    View Cohort & Take Action →
                  </Link>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </Card>
  );
}
