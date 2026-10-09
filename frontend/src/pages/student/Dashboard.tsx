import { Link } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { CalendarDays } from "lucide-react";
import { useApi } from "../../api/client";
import type {
  Risk,
  StudentDashboard,
  StudentSuccessScoreData,
  PlacementReadinessData,
  AcademicRiskData,
  LMSActivityData,
  InterventionItem,
} from "../../api/types";
import {
  Card,
  Badge,
  Empty,
  PageHeader,
  QueryState,
  RiskBadge,
  StatCard,
  StatusBadge,
  fmt,
  fmtDate,
} from "../../components/ui";
import { GpaTrendChart } from "./Grades";
import { SuccessScoreCard } from "../../components/SuccessScoreCard";
import { PlacementReadinessCard } from "../../components/PlacementReadinessCard";
import { RiskAnalysisCard } from "../../components/RiskAnalysisCard";
import { LMSActivityCard } from "../../components/LMSActivityCard";
import { InterventionsManager } from "../../components/InterventionsManager";

const RISK_FILL: Record<Risk, string> = {
  safe: "#10b981",
  warning: "#f59e0b",
  critical: "#f43f5e",
};

export function AttendanceChart({
  data,
}: {
  data: { code: string; percentage: number | null; risk: Risk }[];
}) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data} margin={{ top: 8, right: 12, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
        <XAxis dataKey="code" tick={{ fontSize: 12 }} />
        <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} />
        <Tooltip formatter={(v) => [`${v}%`, "Attendance"]} />
        <ReferenceLine
          y={75}
          stroke="#64748b"
          strokeDasharray="4 4"
          label={{
            value: "75% min",
            fontSize: 11,
            position: "insideTopRight",
            fill: "#64748b",
          }}
        />
        <Bar dataKey="percentage" radius={[4, 4, 0, 0]}>
          {data.map((d) => (
            <Cell key={d.code} fill={RISK_FILL[d.risk]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

function DashboardBody({
  d,
  successScore,
  placementReadiness,
  academicRisk,
  lms,
  interventions,
  onRefreshInterventions,
}: {
  d: StudentDashboard;
  successScore?: StudentSuccessScoreData;
  placementReadiness?: PlacementReadinessData;
  academicRisk?: AcademicRiskData;
  lms?: LMSActivityData;
  interventions: InterventionItem[];
  onRefreshInterventions: () => void;
}) {
  const att = d.attendance;
  const actions: { title: string; detail: string; to: string; label: string; tone: string }[] = [];

  if (att.risk === "critical" || att.risk === "warning") {
    actions.push({
      title: "Protect your attendance",
      detail:
        att.risk === "critical"
          ? `At ${att.percentage}%. Attend the next ${att.classes_needed} classes to reach the 75% minimum.`
          : `At ${att.percentage}%. Keep attending to stay above the 75% minimum.`,
      to: "/student/attendance",
      label: "View attendance",
      tone: att.risk === "critical" ? "border-rose-200 bg-rose-50/70" : "border-amber-200 bg-amber-50/70",
    });
  }

  if (d.pending_assignments > 0) {
    const nextAssignment =
      d.upcoming_assignments.find((assignment) => assignment.status === "overdue") ??
      d.upcoming_assignments.find((assignment) => assignment.status === "pending");
    actions.push({
      title: `${d.pending_assignments} assignment${d.pending_assignments === 1 ? "" : "s"} to review`,
      detail: nextAssignment
        ? `${nextAssignment.title} · Due ${fmtDate(nextAssignment.due_date)}`
        : "Check your assignments for upcoming or overdue work.",
      to: "/student/assignments",
      label: "View assignments",
      tone: "border-indigo-200 bg-indigo-50/70",
    });
  }

  if (d.pending_feedback > 0) {
    actions.push({
      title: `${d.pending_feedback} feedback form${d.pending_feedback === 1 ? "" : "s"} pending`,
      detail: "Submit your feedback before the forms close.",
      to: "/student/feedback",
      label: "Open feedback",
      tone: "border-violet-200 bg-violet-50/70",
    });
  }

  if (d.active_backlogs > 0) {
    actions.push({
      title: `${d.active_backlogs} active backlog${d.active_backlogs === 1 ? "" : "s"}`,
      detail: "Review your course results and plan your next steps.",
      to: "/student/grades",
      label: "View results",
      tone: "border-rose-200 bg-rose-50/70",
    });
  }

  return (
    <div className="space-y-6">
      <Card title="Start here">
        {actions.length === 0 ? (
          <p className="text-sm text-slate-600">You have no urgent actions right now. Keep checking in for updates.</p>
        ) : (
          <ul className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {actions.map((action) => (
              <li key={action.title} className={`rounded-xl border p-4 ${action.tone}`}>
                <p className="text-sm font-semibold text-slate-900">{action.title}</p>
                <p className="mt-1 text-xs leading-relaxed text-slate-600">{action.detail}</p>
                <Link
                  to={action.to}
                  className="mt-3 inline-flex min-h-11 items-center gap-1 text-xs font-semibold text-indigo-700 underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500"
                >
                  {action.label} <span aria-hidden="true">→</span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </Card>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
        <StatCard
          label="CGPA"
          value={fmt(d.cgpa)}
          hint={`${d.credits_earned} credits earned`}
          tone={d.cgpa !== null && d.cgpa < 6 ? "bad" : "default"}
        />
        <StatCard
          label="Last SGPA"
          value={fmt(d.last_sgpa)}
          hint={d.last_sgpa_semester ? `Semester ${d.last_sgpa_semester}` : undefined}
        />
        <StatCard
          label="Attendance"
          value={`${att.percentage ?? "—"}%`}
          hint={<RiskBadge risk={att.risk} />}
          tone={att.risk === "critical" ? "bad" : att.risk === "warning" ? "warn" : "good"}
        />
        <StatCard
          label="Backlogs"
          value={d.active_backlogs}
          tone={d.active_backlogs ? "bad" : "good"}
        />
        <StatCard
          label="Pending tasks"
          value={d.pending_feedback + d.pending_assignments}
          hint={`${d.pending_feedback} feedback · ${d.pending_assignments} assignments`}
          tone={d.pending_feedback + d.pending_assignments ? "warn" : "good"}
        />
        <StatCard
          label="Placement"
          value={d.placement_eligible ? "Eligible" : "Not yet"}
          tone={d.placement_eligible ? "good" : "bad"}
          hint={
            <Link to="/student/placement" className="text-indigo-600 hover:underline">
              View criteria
            </Link>
          }
        />
      </div>

      {/* Academic Trends and Attendance Charts */}
      <div className="grid gap-5 lg:grid-cols-2">
        <Card title="SGPA and CGPA by semester">
          {d.sgpa_trend.length ? <GpaTrendChart data={d.sgpa_trend} /> : <Empty>No results yet.</Empty>}
        </Card>
        <Card title={`Attendance by course · Semester ${d.student.current_semester}`}>
          {d.attendance_by_course.length ? (
            <AttendanceChart data={d.attendance_by_course} />
          ) : (
            <Empty>No classes yet.</Empty>
          )}
        </Card>
      </div>

      <details className="group rounded-2xl border border-slate-200 bg-white/50 p-4 sm:p-5">
        <summary className="flex min-h-11 cursor-pointer list-none items-center justify-between gap-3 text-sm font-semibold text-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500">
          <span>Deeper insights and support</span>
          <span className="text-xs font-medium text-indigo-700 group-open:hidden">Show details</span>
          <span className="hidden text-xs font-medium text-indigo-700 group-open:inline">Hide details</span>
        </summary>
        <div className="mt-4 space-y-5">
          <div className="grid gap-5 lg:grid-cols-2">
            {successScore && <SuccessScoreCard data={successScore} />}
            {placementReadiness && <PlacementReadinessCard data={placementReadiness} />}
            {academicRisk && <RiskAnalysisCard data={academicRisk} />}
            {lms && <LMSActivityCard data={lms} />}
          </div>
          <InterventionsManager
            interventions={interventions}
            onRefresh={onRefreshInterventions}
          />
        </div>
      </details>

      {/* Assignments & Faculty Remarks */}
      <div className="grid gap-5 lg:grid-cols-2">
        <Card
          title="Assignments due"
          action={
            <Link to="/student/assignments" className="text-xs text-indigo-600 hover:underline">
              All assignments
            </Link>
          }
        >
          {d.upcoming_assignments.length === 0 ? (
            <Empty>Nothing due.</Empty>
          ) : (
            <ul className="divide-y divide-slate-100">
              {d.upcoming_assignments.map((a) => (
                <li key={a.id} className="flex items-center justify-between gap-3 py-2.5 text-sm">
                  <div>
                    <p className="font-medium text-slate-900">{a.title}</p>
                    <p className="text-xs text-slate-500">Due {fmtDate(a.due_date)}</p>
                  </div>
                  <StatusBadge status={a.status} />
                </li>
              ))}
            </ul>
          )}
        </Card>
        <Card
          title="Latest from faculty"
          action={
            <Link to="/student/remarks" className="text-xs text-indigo-600 hover:underline">
              All remarks
            </Link>
          }
        >
          {d.recent_remarks.length === 0 ? (
            <Empty>No remarks yet.</Empty>
          ) : (
            <ul className="space-y-3">
              {d.recent_remarks.map((r) => (
                <li key={r.id} className="rounded-lg bg-slate-50 p-3 text-sm">
                  <p className="text-slate-800">{r.remark}</p>
                  <p className="mt-1 text-xs text-slate-500">
                    {r.faculty} · {fmtDate(r.created_at)}
                  </p>
                </li>
              ))}
            </ul>
          )}
          {d.pending_feedback > 0 && (
            <Link to="/student/feedback" className="btn-secondary mt-4 w-full">
              Fill {d.pending_feedback} pending feedback form{d.pending_feedback > 1 ? "s" : ""}
            </Link>
          )}
        </Card>
      </div>

      <Card
        title={
          <span className="flex items-center gap-2">
            <CalendarDays size={17} aria-hidden="true" />
            Campus calendar & planner
          </span>
        }
        action={<Badge color="blue">Future implementation</Badge>}
      >
        <p className="text-sm leading-relaxed text-slate-600">
          A single weekly view for your class timetable, exams, assignment deadlines, and reminders. This is a
          planned feature; calendar data and scheduling are not available yet.
        </p>
      </Card>
    </div>
  );
}

export default function StudentDashboardPage() {
  const q = useApi<StudentDashboard>("/student/me/dashboard");
  const successScoreQ = useApi<StudentSuccessScoreData>("/analytics/student/success-score");
  const placementReadinessQ = useApi<PlacementReadinessData>("/analytics/student/placement-readiness");
  const academicRiskQ = useApi<AcademicRiskData>("/analytics/student/academic-risk");
  const lmsQ = useApi<LMSActivityData>("/analytics/student/lms");
  const interventionsQ = useApi<InterventionItem[]>("/interventions");

  const s = q.data?.student;
  return (
    <>
      <PageHeader
        title={s ? `Welcome, ${s.name.split(" ")[0]}` : "Dashboard"}
        subtitle={
          s &&
          `${s.roll_no} · ${s.department} · Semester ${s.current_semester}, Section ${s.section}${
            s.mentor ? ` · Mentor: ${s.mentor}` : ""
          }`
        }
      />
      <QueryState query={q}>
        {(d) => (
          <DashboardBody
            d={d}
            successScore={successScoreQ.data}
            placementReadiness={placementReadinessQ.data}
            academicRisk={academicRiskQ.data}
            lms={lmsQ.data}
            interventions={interventionsQ.data || []}
            onRefreshInterventions={() => interventionsQ.refetch()}
          />
        )}
      </QueryState>
    </>
  );
}
