import { useApi } from "../../api/client";
import type { Placement as PlacementData } from "../../api/types";
import { Badge, Card, Empty, PageHeader, QueryState, Table, Td } from "../../components/ui";

export function PlacementView({ data }: { data: PlacementData }) {
  if (!data.criteria_defined) return <Empty>Placement criteria for your batch have not been published yet.</Empty>;
  const failing = data.checks.filter((c) => !c.passed);
  return (
    <div className="space-y-5">
      <div className={`rounded-xl border p-5 ${data.eligible ? "border-emerald-200 bg-emerald-50" : "border-rose-200 bg-rose-50"}`}>
        <p className={`text-lg font-semibold ${data.eligible ? "text-emerald-800" : "text-rose-800"}`}>
          {data.eligible ? "Eligible for campus placements" : "Not yet eligible for campus placements"}
        </p>
        <p className={`text-sm ${data.eligible ? "text-emerald-700" : "text-rose-700"}`}>
          {data.eligible ? "All criteria are met. Keep your CGPA and attendance up." : `${failing.length} criterion(s) to work on: ${failing.map((c) => c.name).join(", ")}.`}
        </p>
      </div>
      <Card title="Criteria">
        <Table head={["Criterion", "Required", "Yours", "Status", "Gap"]}>
          {data.checks.map((c) => (
            <tr key={c.name}>
              <Td className="font-medium text-slate-900">{c.name}</Td>
              <Td className="tabular-nums">{c.name === "Active backlogs" ? `≤ ${c.required}` : `≥ ${c.required}`}</Td>
              <Td className="tabular-nums">{c.actual ?? "—"}</Td>
              <Td>{c.passed ? <Badge color="green">Met</Badge> : <Badge color="red">Not met</Badge>}</Td>
              <Td className="tabular-nums text-slate-600">{c.passed ? "—" : c.gap ?? "No data"}</Td>
            </tr>
          ))}
        </Table>
      </Card>
    </div>
  );
}

export default function Placement() {
  const q = useApi<PlacementData>("/student/me/placement");
  return (
    <>
      <PageHeader title="Placement eligibility" subtitle="Checked against the criteria set for your batch" />
      <QueryState query={q}>{(d) => <PlacementView data={d} />}</QueryState>
    </>
  );
}
