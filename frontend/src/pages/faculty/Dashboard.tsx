import { Link } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useApi } from "../../api/client";
import type {
  AtRiskStudent,
  FacultyDashboard,
  SmartInsightItem,
  SegmentationSummary,
} from "../../api/types";
import {
  Badge,
  Card,
  Empty,
  PageHeader,
  QueryState,
  StatCard,
  Table,
  Td,
  fmt,
} from "../../components/ui";
import { SmartInsightsCard } from "../../components/SmartInsightsCard";
import { Users, AlertTriangle, Briefcase, Award } from "lucide-react";

export function AtRiskTable({ items }: { items: AtRiskStudent[] }) {
  if (!items.length) return <Empty>No students at risk right now.</Empty>;
  return (
    <Table head={["Student", "Attendance", "CGPA", "Why", ""]}>
      {items.map((s) => (
        <tr key={s.id}>
          <Td>
            <p className="font-medium text-slate-900">{s.name}</p>
            <p className="text-xs text-slate-500">
              {s.roll_no} · Sec {s.section}
            </p>
          </Td>
          <Td className="tabular-nums">{s.attendance_pct ?? "—"}%</Td>
          <Td className="tabular-nums">{fmt(s.cgpa)}</Td>
          <Td>
            <div className="flex flex-col gap-1">
              <Badge color={s.severity === "high" ? "red" : "amber"}>
                {s.severity === "high" ? "High" : "Medium"}
              </Badge>
              <span className="text-xs text-slate-600">{s.reasons.join("; ")}</span>
            </div>
          </Td>
          <Td>
            <Link
              to={`/faculty/students/${s.id}`}
              className="text-sm font-semibold text-indigo-600 hover:underline"
            >
              View
            </Link>
          </Td>
        </tr>
      ))}
    </Table>
  );
}

function Body({
  d,
  insights,
  segmentation,
}: {
  d: FacultyDashboard;
  insights?: SmartInsightItem[];
  segmentation?: SegmentationSummary;
}) {
  return (
    <div className="space-y-6">
      {/* Smart campus insights */}
      {insights && insights.length > 0 && <SmartInsightsCard insights={insights} />}

      {/* Core Academic & Department KPIs */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
        <StatCard
          label="Students"
          value={d.total_students}
          hint={`${d.my_mentees} are your mentees`}
        />
        <StatCard label="Average CGPA" value={fmt(d.average_cgpa)} />
        <StatCard
          label="Attendance < 75%"
          value={d.attendance_critical}
          tone={d.attendance_critical ? "bad" : "good"}
          hint={`${d.attendance_warning} more in 75–85%`}
        />
        <StatCard
          label="With backlogs"
          value={d.with_backlogs}
          tone={d.with_backlogs ? "bad" : "good"}
        />
        <StatCard
          label="Placement eligible"
          value={`${d.placement_eligible}/${d.total_students}`}
        />
        <StatCard
          label="Open help requests"
          value={d.open_help_requests}
          tone={d.open_help_requests ? "warn" : "good"}
          hint={
            <Link to="/faculty/help" className="text-indigo-600 hover:underline">
              Open inbox
            </Link>
          }
        />
      </div>

      {/* Student Segmentation Breakdown */}
      {segmentation && (
        <Card
          title="Department Cohort Segmentation"
          action={
            <Link
              to="/faculty/students"
              className="text-xs font-semibold text-indigo-600 hover:underline"
            >
              Manage Cohorts
            </Link>
          }
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {segmentation.distribution.map((seg) => {
              const borderTone =
                seg.code === "A"
                  ? "border-emerald-200 bg-emerald-50/50 text-emerald-900"
                  : seg.code === "B"
                  ? "border-amber-200 bg-amber-50/50 text-amber-900"
                  : seg.code === "C"
                  ? "border-indigo-200 bg-indigo-50/50 text-indigo-900"
                  : "border-rose-200 bg-rose-50/50 text-rose-900";

              const Icon =
                seg.code === "A"
                  ? Award
                  : seg.code === "B"
                  ? Users
                  : seg.code === "C"
                  ? Briefcase
                  : AlertTriangle;

              return (
                <div
                  key={seg.code}
                  className={`rounded-xl border p-4 flex flex-col justify-between ${borderTone}`}
                >
                  <div>
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-xs uppercase tracking-wider">
                        Segment {seg.code}
                      </span>
                      <Icon className="h-4 w-4 opacity-75" />
                    </div>
                    <p className="mt-1 font-semibold text-sm leading-snug">{seg.name}</p>
                    <p className="mt-1 text-xs opacity-80">{seg.description}</p>
                  </div>
                  <div className="mt-4 flex items-baseline justify-between border-t border-black/5 pt-2">
                    <span className="text-2xl font-bold tabular-nums">{seg.count}</span>
                    <span className="text-xs font-semibold">{seg.percentage}% of Dept</span>
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {/* Students Needing Attention & CGPA Distribution */}
      <div className="grid gap-5 lg:grid-cols-3">
        <Card
          title="Students needing attention"
          className="lg:col-span-2"
          action={
            <Link
              to="/faculty/students?risk=any"
              className="text-xs font-semibold text-indigo-600 hover:underline"
            >
              See all
            </Link>
          }
        >
          <AtRiskTable items={d.at_risk} />
        </Card>
        <Card title="CGPA distribution">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart
              data={d.cgpa_distribution}
              margin={{ top: 8, right: 8, left: -24, bottom: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
              <XAxis dataKey="range" tick={{ fontSize: 12 }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="students" fill="#4f46e5" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>
    </div>
  );
}

export default function FacultyDashboardPage() {
  const q = useApi<FacultyDashboard>("/faculty/dashboard");
  const insightsQ = useApi<SmartInsightItem[]>("/analytics/smart-insights");
  const segmentationQ = useApi<SegmentationSummary>("/analytics/segmentation");

  const f = q.data?.faculty;
  return (
    <>
      <PageHeader
        title={f ? `Hello, ${f.name}` : "Dashboard"}
        subtitle={f && `${f.designation} · ${f.department}`}
      />
      <QueryState query={q}>
        {(d) => (
          <Body
            d={d}
            insights={insightsQ.data}
            segmentation={segmentationQ.data}
          />
        )}
      </QueryState>
    </>
  );
}
