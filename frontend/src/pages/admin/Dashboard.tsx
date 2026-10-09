import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { api } from "../../api/client";
import { StatCard, Card, Loading, PageHeader, fmt } from "../../components/ui";
import { SmartInsightsCard } from "../../components/SmartInsightsCard";
import type { AdminDashboardData, SmartInsightItem } from "../../api/types";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
  AreaChart,
  Area,
  CartesianGrid,
} from "recharts";
import { ArrowRight, Search, Sparkles, ShieldAlert, Gauge, HandHeart, Activity } from "lucide-react";

export default function AdminDashboard() {
  const navigate = useNavigate();
  const [search, setSearch] = useState("");
  const { data, isLoading } = useQuery({
    queryKey: ["admin", "dashboard"],
    queryFn: () => api.get<AdminDashboardData>("/admin/dashboard").then((r) => r.data),
  });

  const { data: insights } = useQuery({
    queryKey: ["admin", "insights"],
    queryFn: () => api.get<SmartInsightItem[]>("/analytics/smart-insights").then((r) => r.data),
  });

  const { data: trendData } = useQuery({
    queryKey: ["admin", "trends"],
    queryFn: () => api.get<{ departments: any[] }>("/analytics/trends").then((r) => r.data),
  });

  if (isLoading || !data) return <Loading full />;

  const kpis = data.kpis;
  const interventionRate = kpis.total_interventions > 0 ? Math.round(kpis.intervention_completion_rate) : 0;
  const submitSearch = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const q = search.trim();
    navigate(q ? `/admin/segmentation?q=${encodeURIComponent(q)}` : "/admin/segmentation");
  };
  const pieColors: Record<string, string> = {
    emerald: "#10b981",
    amber: "#f59e0b",
    rose: "#f43f5e",
  };

  return (
    <div className="space-y-6 sm:space-y-8">
      <PageHeader title="Institution Overview & Analytics" subtitle="Campus-wide student success, predictive risks, and performance metrics" />

      <section className="relative isolate overflow-hidden rounded-[1.75rem] border border-white/80 bg-white/65 p-5 shadow-[0_18px_60px_rgba(70,65,140,.08)] backdrop-blur-xl sm:p-8 lg:p-9">
        <div aria-hidden="true" className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(ellipse_at_82%_20%,rgba(139,92,246,.16),transparent_42%),radial-gradient(ellipse_at_100%_100%,rgba(99,102,241,.12),transparent_40%)]" />
        <div className="grid items-center gap-8 lg:grid-cols-[1.1fr_.9fr] lg:gap-10">
          <div>
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-violet-200/80 bg-white/75 px-3 py-1.5 text-[10px] font-bold uppercase tracking-[.16em] text-violet-700 shadow-sm"><Sparkles size={13}/> Campus intelligence <span className="h-1 w-1 rounded-full bg-slate-300"/> Academic overview</div>
            <h2 className="max-w-2xl text-3xl font-extrabold leading-[1.08] tracking-tight text-slate-900 sm:text-4xl xl:text-[3.25rem]">Campus Intelligence <span className="bg-gradient-to-r from-violet-600 via-indigo-600 to-purple-500 bg-clip-text text-transparent">Portal</span></h2>
            <p className="mt-4 max-w-xl text-sm leading-6 text-slate-600 sm:text-base">A clearer view of student success, emerging academic risk, and campus-wide support outcomes.</p>
            <form onSubmit={submitSearch} className="mt-6 flex max-w-xl items-center gap-2 rounded-2xl border border-white bg-white/85 p-1.5 shadow-[0_8px_24px_rgba(70,65,140,.08)] focus-within:ring-2 focus-within:ring-violet-300">
              <Search className="ml-3 shrink-0 text-slate-400" size={18}/><label className="sr-only" htmlFor="campus-search">Search students and records</label><input id="campus-search" value={search} onChange={(e)=>setSearch(e.target.value)} placeholder="Search students, departments, or cohorts…" className="min-w-0 flex-1 bg-transparent px-1 py-2.5 text-sm text-slate-800 outline-none placeholder:text-slate-400"/><button type="submit" className="inline-flex shrink-0 items-center gap-2 rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 px-4 py-2.5 text-xs font-bold text-white shadow-md shadow-indigo-500/20 transition hover:-translate-y-0.5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-400 focus-visible:ring-offset-2">Search<ArrowRight size={14}/></button>
            </form>
            <div className="mt-4 flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-slate-500"><span className="inline-flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-emerald-500"/>Live campus data</span><span>Across {kpis.total_departments} departments</span><span>{kpis.total_students.toLocaleString()} enrolled students</span></div>
          </div>
          <div className="relative mx-auto w-full max-w-lg lg:pl-4">
            <div className="absolute -right-2 top-0 h-44 w-44 rounded-full bg-violet-300/30 blur-3xl"/>
            <div className="relative rounded-[1.5rem] border border-white/90 bg-white/85 p-5 shadow-[0_20px_50px_rgba(76,67,160,.12)] backdrop-blur-xl sm:p-6">
              <div className="flex items-start justify-between gap-3"><div><p className="text-[10px] font-bold uppercase tracking-[.17em] text-slate-500">Campus success index</p><p className="mt-2 text-4xl font-extrabold tracking-tight text-slate-900">{kpis.average_success_score ?? "—"}<span className="ml-1 text-lg font-semibold text-slate-400">/100</span></p></div><span className="grid h-11 w-11 place-items-center rounded-2xl bg-gradient-to-br from-violet-100 to-indigo-100 text-indigo-700"><Gauge size={21}/></span></div>
              <div className="mt-5 h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-gradient-to-r from-violet-500 to-indigo-500" style={{width:`${Math.max(0,Math.min(kpis.average_success_score ?? 0,100))}%`}}/></div>
              <div className="mt-2 flex justify-between text-[10px] font-medium text-slate-400"><span>Current cohort average</span><span>100</span></div>
              <div className="mt-5 grid grid-cols-2 gap-3"><div className="rounded-xl border border-rose-100 bg-rose-50/70 p-3"><div className="flex items-center gap-2 text-rose-600"><ShieldAlert size={15}/><span className="text-[10px] font-bold uppercase tracking-wide">High academic risk</span></div><p className="mt-2 text-2xl font-extrabold text-slate-900">{kpis.high_risk_students.toLocaleString()}</p><p className="text-[10px] text-slate-500">Students needing attention</p></div><div className="rounded-xl border border-emerald-100 bg-emerald-50/70 p-3"><div className="flex items-center gap-2 text-emerald-700"><HandHeart size={15}/><span className="text-[10px] font-bold uppercase tracking-wide">Interventions</span></div><p className="mt-2 text-2xl font-extrabold text-slate-900">{interventionRate}<span className="text-base">%</span></p><p className="text-[10px] text-slate-500">Completion rate · {kpis.total_interventions} plans</p></div></div>
            </div>
            <div className="relative mt-3 flex items-center justify-between rounded-xl border border-white/90 bg-white/75 px-4 py-3 shadow-lg shadow-indigo-900/5"><div className="flex items-center gap-3"><span className="grid h-9 w-9 place-items-center rounded-xl bg-indigo-50 text-indigo-600"><Activity size={17}/></span><div><p className="text-xs font-bold text-slate-800">Intervention tracker</p><p className="text-[10px] text-slate-500">{kpis.completed_interventions} of {kpis.total_interventions} plans completed</p></div></div><button onClick={()=>navigate("/admin/segmentation")} className="rounded-lg px-2 py-2 text-xs font-bold text-indigo-700 hover:bg-indigo-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400" aria-label="Review student cohorts">Review <ArrowRight className="ml-1 inline" size={13}/></button></div>
          </div>
        </div>
      </section>

      {/* KPI Grid */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4 sm:gap-4">
        <StatCard
          label="Total Enrollment"
          value={kpis.total_students}
          hint={`${kpis.total_departments} Academic Departments`}
        />
        <StatCard
          label="Average Success Score"
          value={`${kpis.average_success_score ?? "—"}/100`}
          hint="Comprehensive student success metric"
          tone={kpis.average_success_score && kpis.average_success_score >= 70 ? "good" : "warn"}
        />
        <StatCard
          label="Placement Readiness"
          value={`${kpis.average_placement_readiness ?? "—"}/100`}
          hint={`${kpis.placement_eligible_count} students eligible`}
          tone="default"
        />
        <StatCard
          label="High Academic Risk"
          value={kpis.high_risk_students}
          hint={`${kpis.intervention_completion_rate}% interventions completed`}
          tone={kpis.high_risk_students > 0 ? "bad" : "good"}
        />
      </div>

      {/* Smart Insights Panel */}
      {insights && insights.length > 0 && <SmartInsightsCard insights={insights} />}

      {/* Charts Row */}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2 lg:gap-6">
        {/* Department Performance Comparison */}
        <Card title="Department Academic Benchmarks" action={<span className="text-xs text-slate-400">CGPA & Success Score</span>}>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={trendData?.departments || []}
                margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
              >
                <CartesianGrid vertical={false} stroke="#e9eaf3" strokeDasharray="3 5" />
                <XAxis dataKey="code" stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} />
                <YAxis domain={[0, 10]} stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{ backgroundColor: "rgba(255,255,255,.94)", borderRadius: "14px", border: "1px solid rgba(196,181,253,.65)", color: "#334155", fontSize: "11px", boxShadow: "0 12px 40px rgba(99,102,241,.14)", backdropFilter: "blur(12px)" }}
                />
                <Bar dataKey="avg_cgpa" name="Avg CGPA (0-10)" fill="#7659e8" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Placement Readiness Breakdown */}
        <Card title="Placement Readiness Distribution" action={<span className="text-xs text-slate-400">Evaluated Cohorts</span>}>
          <div className="h-64 w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data.readiness_distribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={85}
                  paddingAngle={4}
                  dataKey="count"
                  nameKey="category"
                >
                  {data.readiness_distribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={pieColors[entry.color] || "#6366f1"} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ backgroundColor: "rgba(255,255,255,.94)", borderRadius: "14px", border: "1px solid rgba(196,181,253,.65)", color: "#334155", fontSize: "11px", boxShadow: "0 12px 40px rgba(99,102,241,.14)" }} />
                <Legend verticalAlign="bottom" height={36} iconType="circle" wrapperStyle={{ fontSize: "11px" }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Student Success Score Distribution */}
      <Card title="Student Success Score Distribution" action={<span className="text-xs text-slate-400">Campus-wide cohorts</span>}>
        <div className="h-56 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data.success_score_distribution} margin={{ top: 12, right: 12, left: -20, bottom: 0 }}>
              <defs><linearGradient id="successFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#7c3aed" stopOpacity={.28}/><stop offset="95%" stopColor="#7c3aed" stopOpacity={0}/></linearGradient></defs>
              <CartesianGrid vertical={false} stroke="#e9eaf3" strokeDasharray="3 5" />
              <XAxis dataKey="range" stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} />
              <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} axisLine={false} />
              <Tooltip contentStyle={{ backgroundColor: "rgba(255,255,255,.94)", borderRadius: "14px", border: "1px solid rgba(196,181,253,.65)", color: "#334155", fontSize: "11px", boxShadow: "0 12px 40px rgba(99,102,241,.14)" }} formatter={(val) => [`${val} Students`, "Count"]}/>
              <Area type="monotone" dataKey="count" name="Students" stroke="#7c3aed" strokeWidth={2.5} fill="url(#successFill)" activeDot={{ r: 5, strokeWidth: 3, stroke: "#fff", fill: "#7c3aed" }} animationDuration={550}/>
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </Card>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4"><StatCard label="Campus Average CGPA" value={fmt(kpis.average_cgpa)} hint="Overall cumulative grade point"/><StatCard label="Average Attendance" value={`${kpis.average_attendance ?? "—"}%`} hint="Required minimum: 75%" tone={(kpis.average_attendance ?? 0) >= 75 ? "good" : "warn"}/><StatCard label="Active Faculty" value={kpis.total_faculty} hint="Instructional mentors"/><StatCard label="Plans Completed" value={`${kpis.completed_interventions}/${kpis.total_interventions}`} hint="Intervention resolution progress" tone="good"/></div>
    </div>
  );
}
