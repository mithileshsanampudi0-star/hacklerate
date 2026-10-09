import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useApi } from "../../api/client";
import type { StudentOverview } from "../../api/types";
import { Badge, Card, Empty, PageHeader, QueryState, RiskBadge, Table, Td, fmt } from "../../components/ui";

interface Page {
  items: StudentOverview[];
  total: number;
  page: number;
  page_size: number;
}

export default function StudentList() {
  const [params, setParams] = useSearchParams();
  const [search, setSearch] = useState(params.get("search") ?? "");

  // Debounce the search box into the URL so filters are shareable and survive reloads.
  useEffect(() => {
    const t = setTimeout(() => update({ search: search || null, page: null }), 300);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search]);

  function update(changes: Record<string, string | null>) {
    const next = new URLSearchParams(params);
    for (const [k, v] of Object.entries(changes)) {
      if (v) next.set(k, v);
      else next.delete(k);
    }
    setParams(next, { replace: true });
  }

  const query = new URLSearchParams(params);
  query.set("page_size", "15");
  const q = useApi<Page>(`/faculty/students?${query.toString()}`);
  const page = Number(params.get("page") ?? 1);

  return (
    <>
      <PageHeader title="Students" subtitle="Performance of every student in your department" />
      <Card>
        <div className="mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <input className="input" placeholder="Search by name or roll no" value={search} onChange={(e) => setSearch(e.target.value)} />
          <select className="input" value={params.get("section") ?? ""} onChange={(e) => update({ section: e.target.value || null, page: null })}>
            <option value="">All sections</option>
            <option value="A">Section A</option>
            <option value="B">Section B</option>
          </select>
          <select className="input" value={params.get("risk") ?? ""} onChange={(e) => update({ risk: e.target.value || null, page: null })}>
            <option value="">Any attendance</option>
            <option value="any">Needs attention (any reason)</option>
            <option value="critical">Attendance critical (&lt; 75%)</option>
            <option value="warning">Attendance warning (75–85%)</option>
            <option value="safe">Attendance safe</option>
          </select>
          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input type="checkbox" checked={params.get("mentees_only") === "true"} onChange={(e) => update({ mentees_only: e.target.checked ? "true" : null, page: null })} />
            Only my mentees
          </label>
        </div>

        <QueryState query={q}>
          {(d) =>
            d.items.length === 0 ? (
              <Empty>No students match these filters.</Empty>
            ) : (
              <>
                <Table head={["Roll no", "Name", "Sec", "CGPA", "Last SGPA", "Attendance", "Backlogs", "Placement", ""]}>
                  {d.items.map((s) => (
                    <tr key={s.id} className="hover:bg-slate-50">
                      <Td className="font-mono text-xs">{s.roll_no}</Td>
                      <Td className="font-medium text-slate-900">{s.name}</Td>
                      <Td>{s.section}</Td>
                      <Td className={`tabular-nums ${s.cgpa !== null && s.cgpa < 6 ? "font-medium text-rose-600" : ""}`}>{fmt(s.cgpa)}</Td>
                      <Td className="tabular-nums">{fmt(s.last_sgpa)}</Td>
                      <Td>
                        <span className="mr-2 tabular-nums">{s.attendance_pct ?? "—"}%</span>
                        <RiskBadge risk={s.attendance_risk} />
                      </Td>
                      <Td className={s.active_backlogs ? "font-medium text-rose-600" : ""}>{s.active_backlogs}</Td>
                      <Td>{s.placement_eligible ? <Badge color="green">Eligible</Badge> : <Badge color="gray">No</Badge>}</Td>
                      <Td>
                        <Link to={`/faculty/students/${s.id}`} className="text-indigo-600 hover:underline">
                          Open
                        </Link>
                      </Td>
                    </tr>
                  ))}
                </Table>
                <div className="mt-4 flex items-center justify-between text-sm text-slate-600">
                  <span>
                    {d.total} student{d.total === 1 ? "" : "s"}
                  </span>
                  <div className="flex gap-2">
                    <button className="btn-secondary px-3 py-1.5" disabled={page <= 1} onClick={() => update({ page: String(page - 1) })}>
                      Previous
                    </button>
                    <button className="btn-secondary px-3 py-1.5" disabled={page * d.page_size >= d.total} onClick={() => update({ page: String(page + 1) })}>
                      Next
                    </button>
                  </div>
                </div>
              </>
            )
          }
        </QueryState>
      </Card>
    </>
  );
}
