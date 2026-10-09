import { useState } from "react";
import { useApi } from "../../api/client";
import type { SemesterMarks } from "../../api/types";
import { Badge, Card, Empty, PageHeader, QueryState, Table, Td, fmtDate, titleCase } from "../../components/ui";

const EXAM_LABELS: Record<string, string> = {
  internal1: "Internal 1",
  internal2: "Internal 2",
  assignment: "Assignment",
  lab: "Lab",
  end_sem: "End semester",
};

export function MarksView({ data }: { data: SemesterMarks[] }) {
  const [sem, setSem] = useState(data[0]?.semester);
  const current = data.find((s) => s.semester === sem);
  if (!data.length) return <Empty>No exams yet.</Empty>;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {data.map((s) => (
          <button key={s.semester} onClick={() => setSem(s.semester)} className={sem === s.semester ? "btn-primary px-3 py-1.5" : "btn-secondary px-3 py-1.5"}>
            Semester {s.semester}
          </button>
        ))}
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        {current?.courses.map((c) => (
          <Card
            key={c.course_id}
            title={
              <span>
                {c.code} <span className="font-normal text-slate-500">· {c.name}</span>
              </span>
            }
            action={c.grade && <Badge color={c.grade === "F" ? "red" : "green"}>Grade {c.grade}</Badge>}
          >
            <Table head={["Exam", "Date", "Marks", "%"]}>
              {c.exams.map((e) => (
                <tr key={e.exam_id}>
                  <Td>
                    {EXAM_LABELS[e.type] ?? titleCase(e.type)}
                    <span className="ml-1 text-xs text-slate-400">({e.weightage}%)</span>
                  </Td>
                  <Td className="text-slate-500">{fmtDate(e.exam_date)}</Td>
                  <Td className="tabular-nums">{e.marks === null ? <span className="text-slate-400">Upcoming</span> : `${e.marks} / ${e.max_marks}`}</Td>
                  <Td className={`tabular-nums ${e.percentage !== null && e.percentage < 40 ? "font-medium text-rose-600" : ""}`}>{e.percentage === null ? "—" : `${e.percentage}%`}</Td>
                </tr>
              ))}
            </Table>
            {c.total_marks !== null && <p className="mt-3 text-right text-xs text-slate-500">Weighted total: <b className="text-slate-800">{c.total_marks}</b> / 100</p>}
          </Card>
        ))}
      </div>
    </div>
  );
}

export default function Marks() {
  const q = useApi<SemesterMarks[]>("/student/me/marks");
  return (
    <>
      <PageHeader title="Exam marks" subtitle="Internal, assignment and end-semester marks for every course" />
      <QueryState query={q}>{(d) => <MarksView data={d} />}</QueryState>
    </>
  );
}
