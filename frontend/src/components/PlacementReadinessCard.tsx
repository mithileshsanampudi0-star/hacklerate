import { Card, Badge } from "./ui";
import type { PlacementReadinessData } from "../api/types";
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from "recharts";

const CATEGORY_COLORS = {
  "Placement Ready": "green",
  Developing: "amber",
  "Needs Improvement": "red",
} as const;

export function PlacementReadinessCard({ data }: { data: PlacementReadinessData }) {
  const badgeColor = CATEGORY_COLORS[data.category] || "gray";

  const radarData = [
    { subject: "Coding Skills", score: data.components.coding?.score || 0, fullMark: 100 },
    { subject: "Aptitude", score: data.components.aptitude?.score || 0, fullMark: 100 },
    { subject: "Communication", score: data.components.communication?.score || 0, fullMark: 100 },
    { subject: "Mock Interview", score: data.components.mock_interview?.score || 0, fullMark: 100 },
    { subject: "CGPA Academic", score: data.components.cgpa?.score || 0, fullMark: 100 },
  ];

  return (
    <Card
      title={
        <div className="flex items-center gap-2">
          <span>Placement Readiness Score</span>
          <Badge color={badgeColor}>{data.category}</Badge>
        </div>
      }
      action={
        <span className="text-base font-bold text-indigo-700 tabular-nums">
          {data.overall_score} / 100
        </span>
      }
    >
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
        {/* Radar Chart */}
        <div className="md:col-span-6 h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart cx="50%" cy="50%" outerRadius="75%" data={radarData}>
              <PolarGrid stroke="#e2e8f0" />
              <PolarAngleAxis dataKey="subject" stroke="#64748b" tick={{ fontSize: 11 }} />
              <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="#cbd5e1" tick={{ fontSize: 9 }} />
              <Radar
                name="Student Score"
                dataKey="score"
                stroke="#6366f1"
                fill="#818cf8"
                fillOpacity={0.45}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        {/* Strengths & Gaps */}
        <div className="md:col-span-6 space-y-4">
          <div>
            <p className="text-xs font-semibold text-emerald-700 uppercase tracking-wide mb-1.5 flex items-center gap-1.5">
              <span>✓</span> Strengths
            </p>
            {data.strengths.length > 0 ? (
              <ul className="space-y-1">
                {data.strengths.map((s, idx) => (
                  <li key={idx} className="text-xs text-slate-700 flex items-start gap-1.5">
                    <span className="text-emerald-500 font-bold">•</span>
                    <span>{s}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-slate-400">Baseline performance established.</p>
            )}
          </div>

          <div>
            <p className="text-xs font-semibold text-amber-700 uppercase tracking-wide mb-1.5 flex items-center gap-1.5">
              <span>⚠️</span> Skill Gaps & Development Needs
            </p>
            {data.skill_gaps.length > 0 ? (
              <ul className="space-y-1">
                {data.skill_gaps.map((g, idx) => (
                  <li key={idx} className="text-xs text-slate-700 flex items-start gap-1.5">
                    <span className="text-amber-500 font-bold">•</span>
                    <span>{g}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-emerald-600 font-medium">No critical skill gaps flagged.</p>
            )}
          </div>
        </div>
      </div>

      {/* Personalized Recommendations */}
      {data.recommendations && data.recommendations.length > 0 && (
        <div className="mt-5 border-t border-slate-100 pt-3">
          <p className="text-xs font-semibold text-slate-800 mb-2">Personalized Next Steps</p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {data.recommendations.map((rec, i) => (
              <div key={i} className="rounded-lg bg-indigo-50/60 p-2.5 text-xs text-indigo-900 border border-indigo-100/60">
                <span className="font-semibold text-indigo-700">Action {i + 1}: </span>
                <span>{rec}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
}
