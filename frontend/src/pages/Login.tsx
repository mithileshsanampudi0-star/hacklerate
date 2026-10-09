import { useState, type FormEvent } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { errorMessage } from "../api/client";
import type { Role } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { Loading } from "../components/ui";
import { ThemeToggle } from "../components/ThemeToggle";
import { Activity, ArrowUpRight, BookOpenCheck, BrainCircuit, GraduationCap, ShieldCheck, Sparkles } from "lucide-react";

export default function Login() {
  const { user, loading, login } = useAuth();
  const navigate = useNavigate();
  const [role, setRole] = useState<Role>("student");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  if (loading) return <Loading full />;
  if (user) return <Navigate to={`/${user.role}`} replace />;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const me = await login(email, password, role);
      navigate(`/${me.role}`, { replace: true });
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  async function quickLogin(demoEmail: string, demoPassword: string, demoRole: Role) {
    setRole(demoRole);
    setEmail(demoEmail);
    setPassword(demoPassword);
    setError(null);
    setBusy(true);
    try {
      const me = await login(demoEmail, demoPassword, demoRole);
      navigate(`/${me.role}`, { replace: true });
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-shell relative isolate min-h-screen overflow-hidden bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-indigo-50/70 via-slate-50 to-purple-50/50 px-4 py-8 sm:px-8 lg:px-12">
      <div className="absolute right-4 top-4 z-10">
        <ThemeToggle />
      </div>
      <div aria-hidden="true" className="pointer-events-none fixed inset-0 -z-10 overflow-hidden"><div className="absolute -right-20 -top-28 h-[32rem] w-[32rem] rounded-full bg-violet-300/25 blur-[110px]"/><div className="absolute -bottom-52 left-[20%] h-[32rem] w-[32rem] rounded-full bg-indigo-300/20 blur-[110px]"/></div>
      <div className="mx-auto grid min-h-[calc(100vh-4rem)] w-full max-w-7xl items-center gap-10 lg:grid-cols-[1.05fr_.95fr] lg:gap-16">
        <section className="hidden lg:block">
          <div className="inline-flex items-center gap-2 rounded-full border border-violet-200/70 bg-white/70 px-3 py-1.5 text-[10px] font-bold uppercase tracking-[.17em] text-violet-700 shadow-sm"><Sparkles size={13}/> Student success intelligence</div>
          <h1 className="mt-7 max-w-2xl text-5xl font-extrabold leading-[1.04] tracking-tight text-slate-900 xl:text-6xl">Make every student journey <span className="bg-gradient-to-r from-violet-600 via-indigo-600 to-purple-500 bg-clip-text text-transparent">visible.</span></h1>
          <p className="mt-6 max-w-xl text-base leading-7 text-slate-600">One connected campus workspace for academic progress, timely support, and confident student outcomes.</p>
          <div className="relative mt-11 max-w-xl rounded-[1.75rem] border border-white/90 bg-white/55 p-5 shadow-[0_22px_70px_rgba(70,65,140,.12)] backdrop-blur-xl">
            <div aria-hidden="true" className="pointer-events-none absolute -right-5 -top-8 h-40 w-40 rounded-full bg-violet-300/30 blur-3xl"/>
            <div className="relative flex items-center justify-between"><div className="flex items-center gap-3"><span className="grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-violet-600 to-indigo-600 text-white shadow-lg shadow-indigo-500/20"><BrainCircuit size={20}/></span><div><p className="text-sm font-bold text-slate-800">A more connected campus</p><p className="text-xs text-slate-500">Progress, insight, and support in one place</p></div></div><span className="grid h-8 w-8 place-items-center rounded-full bg-white/80 text-violet-600"><ArrowUpRight size={16}/></span></div>
            <div className="relative mt-5 grid grid-cols-3 gap-3">
              <div className="rounded-2xl border border-white bg-white/75 p-3"><span className="grid h-8 w-8 place-items-center rounded-xl bg-violet-50 text-violet-600"><GraduationCap size={16}/></span><div className="mt-4 h-1.5 w-4/5 rounded-full bg-violet-200"/><div className="mt-2 h-1.5 w-2/3 rounded-full bg-slate-100"/><p className="mt-3 text-[10px] font-semibold text-slate-500">Student progress</p></div>
              <div className="translate-y-3 rounded-2xl border border-white bg-white/85 p-3 shadow-lg shadow-indigo-900/5"><span className="grid h-8 w-8 place-items-center rounded-xl bg-indigo-50 text-indigo-600"><Activity size={16}/></span><div className="mt-3 flex h-8 items-end gap-1"><i className="h-3 w-1/5 rounded-t bg-violet-200"/><i className="h-5 w-1/5 rounded-t bg-violet-300"/><i className="h-4 w-1/5 rounded-t bg-indigo-300"/><i className="h-7 w-1/5 rounded-t bg-indigo-500"/><i className="h-6 w-1/5 rounded-t bg-violet-400"/></div><p className="mt-2 text-[10px] font-semibold text-slate-500">Campus insight</p></div>
              <div className="rounded-2xl border border-white bg-white/75 p-3"><span className="grid h-8 w-8 place-items-center rounded-xl bg-emerald-50 text-emerald-600"><BookOpenCheck size={16}/></span><div className="mt-4 h-1.5 w-3/4 rounded-full bg-emerald-200"/><div className="mt-2 h-1.5 w-1/2 rounded-full bg-slate-100"/><p className="mt-3 text-[10px] font-semibold text-slate-500">Timely support</p></div>
            </div>
            <div className="relative mt-7 flex items-center gap-2 text-[11px] font-medium text-slate-500"><ShieldCheck size={14} className="text-emerald-600"/>Role-based access keeps each workspace focused and secure</div>
          </div>
        </section>

        <div className="mx-auto w-full max-w-[30rem]">
        <div className="mb-6 text-center lg:text-left">
          <span className="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-gradient-to-br from-violet-600 to-indigo-600 text-white shadow-lg shadow-indigo-500/25 lg:mx-0"><Activity size={23}/></span>
          <h2 className="mt-4 text-2xl font-extrabold tracking-tight text-slate-900">Smart Campus Analytics</h2>
          <p className="mt-1 text-sm text-slate-500">Sign in to your campus workspace</p>
        </div>

        <form onSubmit={onSubmit} className="rounded-[1.5rem] border border-white/90 bg-white/80 p-5 shadow-[0_18px_60px_rgba(70,65,140,.1)] backdrop-blur-xl sm:p-7">
          <div className="mb-6 grid grid-cols-3 rounded-xl border border-slate-100 bg-slate-100/80 p-1">
            {(["student", "faculty", "admin"] as Role[]).map((r) => (
              <button
                key={r}
                type="button"
                onClick={() => {
                  setRole(r);
                  setError(null);
                }}
                aria-pressed={role === r}
                className={`rounded-lg py-2 text-xs font-semibold capitalize transition ${role === r ? "bg-white text-indigo-700 shadow-sm ring-1 ring-slate-200/70" : "text-slate-500 hover:text-slate-900"}`}
              >
                {r === "admin" ? "Admin" : r}
              </button>
            ))}
          </div>

          <label className="label" htmlFor="email">
            Email
          </label>
          <input
            id="email"
            type="email"
            required
            autoComplete="username"
            className="input mb-4 rounded-xl border-slate-200/80 bg-white/85 py-2.5 focus:border-violet-400 focus:ring-violet-100"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder={role === "student" ? "24cse001@campus.edu" : role === "faculty" ? "anjali.rao@campus.edu" : "admin@campus.edu"}
          />

          <label className="label" htmlFor="password">
            Password
          </label>
          <input
            id="password"
            type="password"
            required
            autoComplete="current-password"
            className="input mb-5 rounded-xl border-slate-200/80 bg-white/85 py-2.5 focus:border-violet-400 focus:ring-violet-100"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />

          {error && <p role="alert" className="mb-4 rounded-xl border border-rose-100 bg-rose-50/80 px-3 py-2.5 text-sm text-rose-700">{error}</p>}

          <button type="submit" className="btn-primary w-full shadow-sm" disabled={busy}>
            {busy ? "Signing in…" : `Sign in as ${role === "student" ? "Student" : role === "faculty" ? "Faculty" : "Administrator"}`}
          </button>

          <div className="mt-6 border-t border-slate-100 pt-4">
            <p className="mb-3 text-center text-[10px] font-bold uppercase tracking-[.15em] text-slate-400">Demo accounts · one-click access</p>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <button
                type="button"
                disabled={busy}
                onClick={() => quickLogin("admin@campus.edu", "Admin@123", "admin")}
                className="rounded-xl border border-violet-200/80 bg-violet-50/60 p-3 text-left transition hover:-translate-y-0.5 hover:bg-violet-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500 disabled:opacity-60"
              >
                <span className="font-semibold text-purple-700 block">Administrator</span>
                <span className="text-slate-500 text-[11px]">Full Campus KPIs</span>
              </button>
              <button
                type="button"
                disabled={busy}
                onClick={() => quickLogin("anjali.rao@campus.edu", "Faculty@123", "faculty")}
                className="rounded-xl border border-indigo-200/80 bg-indigo-50/60 p-3 text-left transition hover:-translate-y-0.5 hover:bg-indigo-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 disabled:opacity-60"
              >
                <span className="font-semibold text-indigo-700 block">Faculty (CSE)</span>
                <span className="text-slate-500 text-[11px]">Dr. Anjali Rao</span>
              </button>
              <button
                type="button"
                disabled={busy}
                onClick={() => quickLogin("24cse001@campus.edu", "Student@123", "student")}
                className="rounded-xl border border-emerald-200/80 bg-emerald-50/60 p-3 text-left transition hover:-translate-y-0.5 hover:bg-emerald-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 disabled:opacity-60"
              >
                <span className="font-semibold text-emerald-700 block">Student (Top)</span>
                <span className="text-slate-500 text-[11px]">24cse001 (CGPA 9.1)</span>
              </button>
              <button
                type="button"
                disabled={busy}
                onClick={() => quickLogin("24cse007@campus.edu", "Student@123", "student")}
                className="rounded-xl border border-rose-200/80 bg-rose-50/60 p-3 text-left transition hover:-translate-y-0.5 hover:bg-rose-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-500 disabled:opacity-60"
              >
                <span className="font-semibold text-rose-700 block">Student (At-Risk)</span>
                <span className="text-slate-500 text-[11px]">24cse007 (Low Att)</span>
              </button>
            </div>
          </div>
        </form>
        <p className="mt-5 text-center text-[11px] text-slate-400">Smart Campus Analytics <span className="mx-1">·</span> Student Success &amp; Prediction Platform</p>
        </div>
      </div>
    </div>
  );
}
