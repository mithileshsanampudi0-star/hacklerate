import { Card } from "./ui";
import type { LMSActivityData } from "../api/types";

export function LMSActivityCard({ data }: { data: LMSActivityData }) {
  return (
    <Card
      title="LMS Learning Engagement"
      action={<span className="text-xs text-slate-400">Integrated Course Analytics</span>}
    >
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 text-center">
          <p className="text-[11px] font-medium text-slate-500 uppercase">Portal Logins</p>
          <p className="mt-1 text-2xl font-bold text-slate-900 tabular-nums">{data.login_count}</p>
          <p className="mt-0.5 text-[10px] text-slate-400">Semester total</p>
        </div>
        <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 text-center">
          <p className="text-[11px] font-medium text-slate-500 uppercase">Course Views</p>
          <p className="mt-1 text-2xl font-bold text-indigo-600 tabular-nums">{data.course_views}</p>
          <p className="mt-0.5 text-[10px] text-slate-400">Content modules</p>
        </div>
        <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 text-center">
          <p className="text-[11px] font-medium text-slate-500 uppercase">Videos Watched</p>
          <p className="mt-1 text-2xl font-bold text-emerald-600 tabular-nums">{data.videos_watched}</p>
          <p className="mt-0.5 text-[10px] text-slate-400">Lecture recordings</p>
        </div>
        <div className="p-3 rounded-xl bg-slate-50 border border-slate-100 text-center">
          <p className="text-[11px] font-medium text-slate-500 uppercase">Time Spent</p>
          <p className="mt-1 text-2xl font-bold text-purple-600 tabular-nums">{data.time_spent_hours}h</p>
          <p className="mt-0.5 text-[10px] text-slate-400">Active study time</p>
        </div>
      </div>

      <div className="mt-3 flex items-center justify-between text-xs text-slate-500 border-t border-slate-100 pt-2 px-1">
        <span>Assignments completed online: <strong>{data.assignments_completed}</strong></span>
        <span>
          Last Active:{" "}
          <strong>
            {data.last_active
              ? new Date(data.last_active).toLocaleDateString("en-IN", { day: "numeric", month: "short" })
              : "Recently"}
          </strong>
        </span>
      </div>
    </Card>
  );
}
