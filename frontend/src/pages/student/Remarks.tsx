import { useApi } from "../../api/client";
import type { Remark } from "../../api/types";
import { Badge, Empty, PageHeader, QueryState, fmtDate, titleCase } from "../../components/ui";

const CATEGORY_COLOR = { appreciation: "green", academic: "blue", attendance: "amber", behaviour: "red" } as const;

export function RemarksView({ items }: { items: Remark[] }) {
  if (!items.length) return <Empty>No remarks yet.</Empty>;
  return (
    <ul className="space-y-3">
      {items.map((r) => (
        <li key={r.id} className="rounded-xl border border-slate-200 bg-white p-4">
          <div className="mb-2 flex flex-wrap items-center gap-2 text-xs text-slate-500">
            <Badge color={CATEGORY_COLOR[r.category as keyof typeof CATEGORY_COLOR] ?? "gray"}>{titleCase(r.category)}</Badge>
            {r.visibility === "faculty_only" && <Badge color="gray">Faculty only</Badge>}
            <span>
              {r.faculty} · {fmtDate(r.created_at)}
            </span>
          </div>
          <p className="text-sm text-slate-800">{r.remark}</p>
        </li>
      ))}
    </ul>
  );
}

export default function Remarks() {
  const q = useApi<Remark[]>("/student/me/remarks");
  return (
    <>
      <PageHeader title="Faculty remarks" subtitle="Feedback from your mentor and course teachers" />
      <QueryState query={q}>{(d) => <RemarksView items={d} />}</QueryState>
    </>
  );
}
