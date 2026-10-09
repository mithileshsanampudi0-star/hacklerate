import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../../api/client";
import { Card, Badge, Loading, PageHeader, fmt } from "../../components/ui";
import { Search, X } from "lucide-react";

const SEGMENT_COLORS = {
  A: "green",
  B: "amber",
  C: "blue",
  D: "red",
} as const;

export default function Segmentation() {
  const [selectedSegment, setSelectedSegment] = useState<string>("all");
  const [searchParams, setSearchParams] = useSearchParams();
  const [search, setSearch] = useState(searchParams.get("q") ?? "");

  const { data, isLoading } = useQuery({
    queryKey: ["analytics", "segmentation"],
    queryFn: () =>
      api.get<{
        total_students: number;
        distribution: { code: string; name: string; count: number; percentage: number; color: string; description: string }[];
        segments: Record<string, any[]>;
      }>("/analytics/segmentation").then((r) => r.data),
  });

  if (isLoading || !data) return <Loading full />;

  const allStudents = Object.entries(data.segments).flatMap(([code, items]) =>
    items.map((it) => ({ ...it, segment_code: code }))
  );

  const filteredBySegment =
    selectedSegment === "all"
      ? allStudents
      : allStudents.filter((s) => s.segment_code === selectedSegment);
  const query = search.trim().toLowerCase();
  const filteredStudents = filteredBySegment.filter((s) =>
    !query || [s.name, s.roll_no, s.department, s.segment_code, s.reason].some((value) => String(value ?? "").toLowerCase().includes(query))
  );

  function exportCSV() {
    window.open("/api/admin/export?report_type=students&format=csv", "_blank");
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Student Performance Segmentation"
        subtitle="Automated segmentation categorizing students based on academic standing, placement readiness, and risk factors"
        action={
          <button onClick={exportCSV} className="btn-secondary text-xs px-3 py-1.5 flex items-center gap-1.5">
            <span>📥</span> Export CSV Report
          </button>
        }
      />

      <form onSubmit={(event) => { event.preventDefault(); const params = new URLSearchParams(searchParams); if (search.trim()) params.set("q", search.trim()); else params.delete("q"); setSearchParams(params); }} className="flex max-w-lg items-center gap-2 rounded-2xl border border-white/80 bg-white/75 px-3 py-2 shadow-sm backdrop-blur-md focus-within:ring-2 focus-within:ring-violet-300">
        <Search size={17} className="shrink-0 text-slate-400"/><label htmlFor="segment-search" className="sr-only">Search students in cohorts</label><input id="segment-search" value={search} onChange={(e)=>setSearch(e.target.value)} placeholder="Filter by name, roll number, department…" className="min-w-0 flex-1 bg-transparent px-1 py-1.5 text-sm outline-none placeholder:text-slate-400"/>{search && <button type="button" aria-label="Clear search" onClick={()=>{setSearch("");setSearchParams({});}} className="rounded-md p-1 text-slate-400 hover:bg-slate-100"><X size={15}/></button>}<button type="submit" className="rounded-lg bg-violet-50 px-3 py-2 text-xs font-bold text-violet-700 hover:bg-violet-100">Filter</button>
      </form>

      {/* Segment Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {data.distribution.map((dist) => {
          const isSelected = selectedSegment === dist.code;
          return (
            <button
              key={dist.code}
              onClick={() => setSelectedSegment(isSelected ? "all" : dist.code)}
              aria-pressed={isSelected}
              className={`group relative overflow-hidden rounded-2xl border p-4 text-left transition-all duration-300 hover:-translate-y-0.5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500 ${
                isSelected
                  ? "border-violet-300 bg-gradient-to-br from-violet-50/90 to-indigo-50/90 ring-2 ring-violet-300 shadow-[0_10px_30px_rgba(99,102,241,.12)]"
                  : "border-white/80 bg-white/75 shadow-[0_8px_32px_rgba(31,38,135,.04)] backdrop-blur-md hover:border-violet-200 hover:shadow-[0_12px_36px_rgba(99,102,241,.1)]"
              }`}
            >
              <div className="flex items-center justify-between">
                <Badge color={SEGMENT_COLORS[dist.code as keyof typeof SEGMENT_COLORS] || "gray"}>
                  Segment {dist.code}
                </Badge>
                <span className="text-xs font-semibold text-slate-500 tabular-nums">{dist.percentage}%</span>
              </div>
              <h3 className="mt-2 text-sm font-bold text-slate-900">{dist.name}</h3>
              <p className="mt-1 text-2xl font-black text-slate-900 tabular-nums">{dist.count}</p>
              <p className="mt-1 text-[11px] text-slate-500 line-clamp-2 leading-relaxed">{dist.description}</p>
            </button>
          );
        })}
      </div>

      {/* Filter status */}
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium text-slate-600">
          Showing <strong>{filteredStudents.length}</strong> of {allStudents.length} students
          {selectedSegment !== "all" && <span> in Segment {selectedSegment}</span>}
          {query && <span> matching “{search.trim()}”</span>}
        </p>
        {(selectedSegment !== "all" || query) && (
          <button
            onClick={() => { setSelectedSegment("all"); setSearch(""); setSearchParams({}); }}
            className="text-xs font-semibold text-indigo-600 hover:underline"
          >
            Clear Filters
          </button>
        )}
      </div>

      {/* Students Table */}
      <Card>
        {filteredStudents.length === 0 ? <p className="py-12 text-center text-sm text-slate-500">No students match this search. Try a name, roll number, or department.</p> :
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-200 text-slate-400 uppercase text-[10px] tracking-wider font-semibold">
                <th className="pb-3 pl-1">Student</th>
                <th className="pb-3">Department</th>
                <th className="pb-3">Segment</th>
                <th className="pb-3">CGPA</th>
                <th className="pb-3">Attendance</th>
                <th className="pb-3">Success Score</th>
                <th className="pb-3">Readiness</th>
                <th className="pb-3 pr-1">Segmentation Rationale</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredStudents.map((s) => (
                <tr key={s.id} className="hover:bg-slate-50/80 transition">
                  <td className="py-3 pl-1">
                    <p className="font-bold text-slate-900">{s.name}</p>
                    <p className="text-[11px] font-mono text-slate-400">{s.roll_no} • Sec {s.section}</p>
                  </td>
                  <td className="py-3 text-slate-600 font-medium">{s.department || "CSE"}</td>
                  <td className="py-3">
                    <Badge color={SEGMENT_COLORS[s.segment_code as keyof typeof SEGMENT_COLORS] || "gray"}>
                      Seg {s.segment_code}
                    </Badge>
                  </td>
                  <td className="py-3 font-semibold text-slate-800 tabular-nums">{fmt(s.cgpa)}</td>
                  <td className="py-3 font-semibold text-slate-800 tabular-nums">{fmt(s.attendance_pct, 1)}%</td>
                  <td className="py-3 font-bold text-indigo-600 tabular-nums">{Math.round(s.success_score)}/100</td>
                  <td className="py-3 font-semibold text-slate-800 tabular-nums">{Math.round(s.readiness_score)}/100</td>
                  <td className="py-3 pr-1 text-slate-600 text-[11px] leading-relaxed max-w-xs">
                    {s.reason}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        }
      </Card>
    </div>
  );
}
