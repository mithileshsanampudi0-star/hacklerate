import { useState } from "react";
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useApi } from "../../api/client";
import type { Results } from "../../api/types";
import { Badge, Card, Empty, PageHeader, QueryState, StatCard, Table, Td, fmt } from "../../components/ui";

export function GpaTrendChart({ data }: { data: { semester: number; sgpa: number | null; cgpa: number | null }[] }) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <LineChart data={data.map((d) => ({ ...d, label: `Sem ${d.semester}` }))} margin={{ top: 8, right: 12, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
        <XAxis dataKey="label" tick={{ fontSize: 12 }} />
        <YAxis domain={[0, 10]} tick={{ fontSize: 12 }} />
        <Tooltip />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Line type="monotone" dataKey="sgpa" name="SGPA" stroke="#4f46e5" strokeWidth={2} dot={{ r: 4 }} />
        <Line type="monotone" dataKey="cgpa" name="CGPA" stroke="#0d9488" strokeWidth={2} strokeDasharray="5 4" dot={{ r: 3 }} />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function ResultsView({ data }: { data: Results }) {
  const [openSem, setOpenSem] = useState<number | null>(data.semesters.at(-1)?.semester ?? null);
  if (!data.semesters.length) return <Empty>No results have been published yet.</Empty>;

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <StatCard label="CGPA" value={fmt(data.cgpa)} tone={data.cgpa !== null && data.cgpa < 6 ? "bad" : "default"} />
        <StatCard label="Credits earned" value={data.credits_earned} />
        <StatCard label="Active backlogs" value={data.active_backlogs} tone={data.active_backlogs ? "bad" : "good"} />
        <StatCard label="Semesters completed" value={data.semesters.length} />
      </div>

      <div className="grid gap-5 lg:grid-cols-3">
        <Card title="SGPA and CGPA trend" className="lg:col-span-2">
          <GpaTrendChart data={data.semesters.map((s) => ({ semester: s.semester, sgpa: s.sgpa, cgpa: s.cgpa_upto }))} />
        </Card>
        <Card title="Year-wise GPA">
          <ul className="space-y-3">
            {data.years.map((y) => (
              <li key={y.year} className="flex items-center justify-between rounded-lg bg-slate-50 px-4 py-3">
                <div>
                  <p className="font-medium text-slate-900">Year {y.year}</p>
                  <p className="text-xs text-slate-500">Semesters {y.semesters.join(" & ")}</p>
                </div>
                <p className="text-xl font-semibold tabular-nums">{fmt(y.gpa)}</p>
              </li>
            ))}
          </ul>
        </Card>
      </div>

      <Card title="Semester results">
        <div className="divide-y divide-slate-100">
          {data.semesters.map((s) => (
            <div key={s.semester}>
              <button className="flex w-full items-center justify-between py-3 text-left" onClick={() => setOpenSem(openSem === s.semester ? null : s.semester)}>
                <span className="font-medium text-slate-900">Semester {s.semester}</span>
                <span className="flex items-center gap-4 text-sm tabular-nums text-slate-600">
                  <span>
                    SGPA <b className="text-slate-900">{fmt(s.sgpa)}</b>
                  </span>
                  <span className="hidden sm:inline">
                    CGPA <b className="text-slate-900">{fmt(s.cgpa_upto)}</b>
                  </span>
                  <span className="hidden sm:inline">
                    Credits {s.credits_earned}/{s.credits}
                  </span>
                  <span className="text-slate-400">{openSem === s.semester ? "▲" : "▼"}</span>
                </span>
              </button>
              {openSem === s.semester && (
                <div className="pb-4">
                  <Table head={["Course", "Credits", "Total", "Grade", "Points"]}>
                    {s.courses.map((c) => (
                      <tr key={c.code}>
                        <Td>
                          <span className="font-medium">{c.code}</span> <span className="text-slate-500">{c.name}</span>
                        </Td>
                        <Td>{c.credits}</Td>
                        <Td className="tabular-nums">{c.total_marks}</Td>
                        <Td>
                          <Badge color={c.grade === "F" ? "red" : c.grade_points >= 9 ? "green" : "gray"}>{c.grade}</Badge>
                        </Td>
                        <Td className="tabular-nums">{c.grade_points}</Td>
                      </tr>
                    ))}
                  </Table>
                </div>
              )}
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

export default function Grades() {
  const q = useApi<Results>("/student/me/results");
  return (
    <>
      <PageHeader title="SGPA & CGPA" subtitle="10-point scale. CGPA uses your best attempt in each course." />
      <QueryState query={q}>{(d) => <ResultsView data={d} />}</QueryState>
    </>
  );
}
