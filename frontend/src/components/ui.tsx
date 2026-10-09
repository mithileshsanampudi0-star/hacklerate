import type { ReactNode } from "react";
import { errorMessage } from "../api/client";
import type { Risk } from "../api/types";

export function fmtDate(value: string | null | undefined): string {
  if (!value) return "—";
  return new Date(value.length === 10 ? `${value}T00:00:00` : value).toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export function fmt(value: number | null | undefined, digits = 2): string {
  return value === null || value === undefined ? "—" : value.toFixed(digits);
}

export const titleCase = (s: string) => s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

export function Card({ title, action, children, className = "" }: { title?: ReactNode; action?: ReactNode; children: ReactNode; className?: string }) {
  return (
    <section className={`rounded-2xl border border-white/80 bg-white/75 p-5 shadow-[0_8px_32px_rgba(31,38,135,.045)] backdrop-blur-md transition-shadow duration-300 hover:shadow-[0_12px_40px_rgba(99,102,241,.08)] sm:p-6 ${className}`}>
      {(title || action) && (
        <div className="mb-4 flex items-center justify-between gap-3">
          {title && <h2 className="text-sm font-semibold text-slate-900">{title}</h2>}
          {action}
        </div>
      )}
      {children}
    </section>
  );
}

const TONES = {
  default: "text-slate-900",
  good: "text-emerald-600",
  warn: "text-amber-600",
  bad: "text-rose-600",
};

export function StatCard({ label, value, hint, tone = "default" }: { label: string; value: ReactNode; hint?: ReactNode; tone?: keyof typeof TONES }) {
  return (
    <div className="group relative overflow-hidden rounded-2xl border border-white/80 bg-white/75 p-4 shadow-[0_8px_32px_rgba(31,38,135,.045)] backdrop-blur-md transition-all duration-300 hover:-translate-y-0.5 hover:shadow-[0_12px_40px_rgba(99,102,241,.1)] sm:p-5">
      <div aria-hidden="true" className="pointer-events-none absolute -right-8 -top-10 h-28 w-28 rounded-full bg-violet-300/10 blur-2xl transition group-hover:bg-violet-300/20" />
      <p className="relative text-[10px] font-bold uppercase tracking-[.16em] text-slate-500">{label}</p>
      <p className={`relative mt-2 text-2xl font-extrabold tabular-nums sm:text-[1.75rem] ${TONES[tone]}`}>{value}</p>
      {hint && <p className="relative mt-1.5 text-xs leading-relaxed text-slate-500">{hint}</p>}
    </div>
  );
}

const BADGE = {
  green: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  amber: "bg-amber-50 text-amber-700 ring-amber-200",
  red: "bg-rose-50 text-rose-700 ring-rose-200",
  blue: "bg-indigo-50 text-indigo-700 ring-indigo-200",
  gray: "bg-slate-100 text-slate-600 ring-slate-200",
};

export function Badge({ color = "gray", children }: { color?: keyof typeof BADGE; children: ReactNode }) {
  return (
    <span className={`inline-flex items-center whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset ${BADGE[color]}`}>
      {children}
    </span>
  );
}

export function RiskBadge({ risk }: { risk: Risk }) {
  const map = { safe: ["green", "Safe"], warning: ["amber", "Warning"], critical: ["red", "Critical"] } as const;
  const [color, label] = map[risk];
  return <Badge color={color}>{label}</Badge>;
}

const STATUS_COLORS: Record<string, keyof typeof BADGE> = {
  pending: "amber",
  overdue: "red",
  submitted: "blue",
  late: "amber",
  graded: "green",
  open: "amber",
  in_progress: "blue",
  resolved: "green",
};

export function StatusBadge({ status }: { status: string }) {
  return <Badge color={STATUS_COLORS[status] ?? "gray"}>{titleCase(status)}</Badge>;
}

export function ProgressBar({ value, risk }: { value: number | null; risk: Risk }) {
  const color = { safe: "bg-emerald-500", warning: "bg-amber-500", critical: "bg-rose-500" }[risk];
  return (
    <div className="relative h-2 w-full overflow-hidden rounded-full bg-slate-100">
      <div className={`h-full ${color}`} style={{ width: `${Math.min(value ?? 0, 100)}%` }} />
      <div className="absolute inset-y-0 w-px bg-slate-500" style={{ left: "75%" }} title="75% minimum" />
    </div>
  );
}

export function PageHeader({ title, subtitle, action }: { title: string; subtitle?: ReactNode; action?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-slate-500">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}

export function Loading({ full = false }: { full?: boolean }) {
  return (
    <div className={`flex items-center justify-center text-sm text-slate-500 ${full ? "h-screen" : "py-16"}`}>
      <span className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-indigo-600" />
      Loading…
    </div>
  );
}

export function ErrorBox({ error }: { error: unknown }) {
  return <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">{errorMessage(error)}</div>;
}

export function Empty({ children }: { children: ReactNode }) {
  return <p className="py-6 text-center text-sm text-slate-500">{children}</p>;
}

/** Renders loading / error states around a query result. */
export function QueryState<T>({ query, children }: { query: { data?: T; isLoading: boolean; error: unknown }; children: (data: T) => ReactNode }) {
  if (query.isLoading) return <Loading />;
  if (query.error) return <ErrorBox error={query.error} />;
  if (query.data === undefined) return null;
  return <>{children(query.data)}</>;
}

export function Table({ head, children }: { head: ReactNode[]; children: ReactNode }) {
  return (
    <div className="-mx-5 overflow-x-auto">
      <table className="w-full min-w-[560px] text-left text-sm">
        <thead>
          <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
            {head.map((h, i) => (
              <th key={i} className="px-5 py-2 font-medium">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">{children}</tbody>
      </table>
    </div>
  );
}

export function Td({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <td className={`px-5 py-2.5 align-middle ${className}`}>{children}</td>;
}

export function Tabs<T extends string>({ tabs, value, onChange }: { tabs: { id: T; label: string }[]; value: T; onChange: (id: T) => void }) {
  return (
    <div className="mb-5 flex gap-1 overflow-x-auto border-b border-slate-200">
      {tabs.map((t) => (
        <button
          key={t.id}
          onClick={() => onChange(t.id)}
          className={`-mb-px whitespace-nowrap border-b-2 px-3 py-2 text-sm font-medium transition ${
            value === t.id ? "border-indigo-600 text-indigo-700" : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}
