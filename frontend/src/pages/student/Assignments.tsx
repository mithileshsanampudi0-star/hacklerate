import { useApi } from "../../api/client";
import type { Assignments as AssignmentsData } from "../../api/types";
import { Card, Empty, PageHeader, QueryState, StatusBadge, Table, Td, fmtDate } from "../../components/ui";

export function AssignmentsView({ data }: { data: AssignmentsData }) {
  return (
    <Card title={`Current semester · ${data.pending} pending, ${data.overdue} overdue`}>
      {data.items.length === 0 ? (
        <Empty>No assignments yet.</Empty>
      ) : (
        <Table head={["Assignment", "Course", "Due", "Status", "Marks"]}>
          {data.items.map((a) => (
            <tr key={a.id}>
              <Td>
                <p className="font-medium text-slate-900">{a.title}</p>
                {a.description && <p className="text-xs text-slate-500">{a.description}</p>}
              </Td>
              <Td>{a.course_code}</Td>
              <Td className={a.status === "overdue" ? "font-medium text-rose-600" : ""}>{fmtDate(a.due_date)}</Td>
              <Td>
                <StatusBadge status={a.status} />
              </Td>
              <Td className="tabular-nums">{a.marks === null ? "—" : `${a.marks} / ${a.max_marks}`}</Td>
            </tr>
          ))}
        </Table>
      )}
    </Card>
  );
}

export default function Assignments() {
  const q = useApi<AssignmentsData>("/student/me/assignments");
  return (
    <>
      <PageHeader title="Assignments" subtitle="Submit assignments to your course teacher before the due date" />
      <QueryState query={q}>{(d) => <AssignmentsView data={d} />}</QueryState>
    </>
  );
}
