import { useApi } from "../../api/client";
import type { AttendanceReport } from "../../api/types";
import { Card, Empty, PageHeader, ProgressBar, QueryState, RiskBadge, Table, Td, fmtDate } from "../../components/ui";

export function AttendanceView({ data }: { data: AttendanceReport }) {
  const o = data.overall;
  return (
    <div className="space-y-5">
      <Card>
        <div className="flex flex-wrap items-center gap-6">
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-500">Overall · Semester {data.semester}</p>
            <p className="mt-1 text-3xl font-semibold tabular-nums text-slate-900">{o.percentage ?? "—"}%</p>
            <p className="text-sm text-slate-500">
              {o.attended} of {o.total} classes attended
            </p>
          </div>
          <RiskBadge risk={o.risk} />
          <div className="ml-auto text-sm">
            {o.classes_needed > 0 ? (
              <p className="rounded-lg bg-rose-50 px-3 py-2 text-rose-700">
                Attend the next <b>{o.classes_needed}</b> classes without a break to get back to 75%.
              </p>
            ) : (
              <p className="rounded-lg bg-emerald-50 px-3 py-2 text-emerald-700">
                You can miss up to <b>{o.can_skip}</b> more classes and stay at or above 75%.
              </p>
            )}
          </div>
        </div>
      </Card>

      <Card title="Course-wise attendance" action={data.courses_at_risk > 0 && <span className="text-xs text-amber-700">{data.courses_at_risk} course(s) need attention</span>}>
        {data.courses.length === 0 ? (
          <Empty>No attendance recorded yet.</Empty>
        ) : (
          <Table head={["Course", "Attended", "Percentage", "", "Risk", "To reach 75%"]}>
            {data.courses.map((c) => (
              <tr key={c.course_id}>
                <Td>
                  <p className="font-medium text-slate-900">{c.code}</p>
                  <p className="text-xs text-slate-500">{c.name}</p>
                </Td>
                <Td className="tabular-nums">
                  {c.attended}/{c.total}
                </Td>
                <Td className="font-medium tabular-nums">{c.percentage ?? "—"}%</Td>
                <Td className="w-40">
                  <ProgressBar value={c.percentage} risk={c.risk} />
                </Td>
                <Td>
                  <RiskBadge risk={c.risk} />
                </Td>
                <Td className="text-xs text-slate-600">{c.classes_needed > 0 ? `Attend ${c.classes_needed} more` : `Can skip ${c.can_skip}`}</Td>
              </tr>
            ))}
          </Table>
        )}
      </Card>

      <Card title="Recent absences">
        {data.recent_absences.length === 0 ? (
          <Empty>No absences. Keep it up!</Empty>
        ) : (
          <ul className="flex flex-wrap gap-2">
            {data.recent_absences.map((a, i) => (
              <li key={i} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs">
                <span className="font-medium text-slate-800">{a.code}</span> · {fmtDate(a.date)} · P{a.period}
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}

export default function Attendance() {
  const q = useApi<AttendanceReport>("/student/me/attendance");
  return (
    <>
      <PageHeader title="Attendance" subtitle="On-duty and approved medical leave count as present. 75% is the minimum for exam eligibility." />
      <QueryState query={q}>{(d) => <AttendanceView data={d} />}</QueryState>
    </>
  );
}
