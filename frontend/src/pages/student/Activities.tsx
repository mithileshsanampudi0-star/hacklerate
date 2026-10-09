import { useApi } from "../../api/client";
import type { Activities as ActivitiesData } from "../../api/types";
import { Badge, Card, Empty, PageHeader, QueryState, Table, Td, fmtDate, titleCase } from "../../components/ui";

const LEVEL_COLOR = { national: "blue", state: "green", college: "gray" } as const;

export function ActivitiesView({ data }: { data: ActivitiesData }) {
  return (
    <div className="space-y-5">
      <Card title="Club memberships">
        {data.clubs.length === 0 ? (
          <Empty>Not a member of any club yet.</Empty>
        ) : (
          <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {data.clubs.map((c) => (
              <li key={c.club} className="rounded-lg border border-slate-200 p-3">
                <p className="font-medium text-slate-900">{c.club}</p>
                <p className="text-xs text-slate-500">
                  {c.category} · {c.role} · since {fmtDate(c.joined_on)}
                </p>
              </li>
            ))}
          </ul>
        )}
      </Card>
      <Card title="Activities and participation">
        {data.activities.length === 0 ? (
          <Empty>No activities recorded.</Empty>
        ) : (
          <Table head={["Activity", "Type", "Level", "Result", "Date"]}>
            {data.activities.map((a) => (
              <tr key={a.id}>
                <Td className="font-medium text-slate-900">{a.title}</Td>
                <Td>{titleCase(a.type)}</Td>
                <Td>
                  <Badge color={LEVEL_COLOR[a.level as keyof typeof LEVEL_COLOR] ?? "gray"}>{titleCase(a.level)}</Badge>
                </Td>
                <Td>{a.achievement ?? "—"}</Td>
                <Td className="text-slate-500">{fmtDate(a.date)}</Td>
              </tr>
            ))}
          </Table>
        )}
      </Card>
    </div>
  );
}

export default function Activities() {
  const q = useApi<ActivitiesData>("/student/me/activities");
  return (
    <>
      <PageHeader title="Clubs & activities" />
      <QueryState query={q}>{(d) => <ActivitiesView data={d} />}</QueryState>
    </>
  );
}
