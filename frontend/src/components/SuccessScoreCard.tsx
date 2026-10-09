import { Card, Badge } from "./ui";
import type { StudentSuccessScoreData } from "../api/types";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

const CATEGORY_COLORS = {
  Excellent: "green",
  Good: "blue",
  Average: "amber",
  "At Risk": "red",
} as const;

export function SuccessScoreCard({ data }: { data: StudentSuccessScoreData }) {
  const badgeColor = CATEGORY_COLORS[data.score_category] || "gray";

  return (
    <Card
      title={
        <div className="flex items-center gap-2">
          <span>Student Success Score</span>
          <Badge color={badgeColor}>{data.score_category}</Badge>
        </div>
      }
      action={
        <span className="text-xs text-slate-400">7 Weighted Indicators</span>
      }
    >
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
        {/* Overall Score Dial */}
        <div className="md:col-span-4 flex flex-col items-center justify-center p-4 rounded-xl bg-slate-50 border border-slate-100 text-center">
          <div className="relative flex items-center justify-center h-28 w-28">
            <svg className="h-full w-full -rotate-90" viewBox="0 0 36 36">
              <path
                className="text-slate-200"
                strokeWidth="3.2"
                stroke="currentColor"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
              <path
                className={
                  data.overall_score >= 80
                    ? "text-emerald-500"
                    : data.overall_score >= 65
                    ? "text-indigo-500"
                    : data.overall_score >= 50
                    ? "text-amber-500"
                    : "text-rose-500"
                }
                strokeDasharray={`${data.overall_score}, 100`}
                strokeWidth="3.2"
                strokeLinecap="round"
                stroke="currentColor"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
            </svg>
            <div className="absolute flex flex-col items-center">
              <span className="text-3xl font-extrabold text-slate-900 tabular-nums">
                {Math.round(data.overall_score)}
              </span>
              <span className="text-[10px] uppercase font-bold text-slate-400">out of 100</span>
            </div>
          </div>
          <p className="mt-2 text-xs font-semibold text-slate-700">{data.score_category} Standing</p>
          <p className="text-[11px] text-slate-500 mt-0.5">Continuous composite success metric</p>
        </div>

        {/* Breakdown of 7 Indicators */}
        <div className="md:col-span-8 space-y-2.5">
          {Object.entries(data.breakdown).map(([key, item]) => {
            const pct = Math.min(100, Math.max(0, item.normalized));
            const barColor =
              item.impact === "positive"
                ? "bg-emerald-500"
                : item.impact === "warning"
                ? "bg-amber-500"
                : "bg-rose-500";

            return (
              <div key={key} className="text-xs">
                <div className="flex justify-between items-center mb-1">
                  <div className="flex items-center gap-1.5">
                    <span className="font-semibold text-slate-800">{item.label}</span>
                    <span className="text-[10px] text-slate-400">({Math.round(item.weight * 100)}% wt)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-slate-500 font-mono text-[11px]">{item.raw}</span>
                    <span className="font-semibold text-slate-900 tabular-nums">
                      +{item.contribution.toFixed(1)} pts
                    </span>
                  </div>
                </div>
                <div className="h-2 w-full rounded-full bg-slate-100 overflow-hidden">
                  <div className={`h-full ${barColor} rounded-full transition-all duration-500`} style={{ width: `${pct}%` }} />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Historical Trend Chart */}
      {data.history && data.history.length > 1 && (
        <div className="mt-6 border-t border-slate-100 pt-4">
          <p className="text-xs font-semibold text-slate-600 mb-2">Historical Score Progression</p>
          <div className="h-28 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.history} margin={{ top: 5, right: 10, left: -25, bottom: 0 }}>
                <XAxis dataKey="date" stroke="#94a3b8" fontSize={10} tickLine={false} />
                <YAxis domain={[40, 100]} stroke="#94a3b8" fontSize={10} tickLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#1e293b", borderRadius: "8px", border: "none", color: "#fff", fontSize: "11px" }}
                  formatter={(val: any) => [`${val}/100`, "Success Score"]}
                />
                <Line type="monotone" dataKey="score" stroke="#6366f1" strokeWidth={2.5} dot={{ r: 3, fill: "#6366f1" }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      <details className="mt-4 border-t border-slate-100 pt-3">
        <summary className="min-h-11 cursor-pointer py-2 text-xs font-semibold text-indigo-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500">
          How this score is calculated
        </summary>
        <p className="text-xs leading-relaxed text-slate-600">
          Each indicator is normalized to a 0–100 scale, multiplied by its configured weight, and combined into
          this composite score. The raw value and weight are shown above; some unavailable data sources use a
          default, so check those values before drawing conclusions. This is a progress summary, not a GPA.
        </p>
      </details>
    </Card>
  );
}
