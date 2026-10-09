import { useEffect, useRef, useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { NotificationCenter } from "./NotificationCenter";
import { ChatAssistantModal } from "./ChatAssistantModal";
import { Activity, BookOpen, ChevronRight, GraduationCap, LayoutDashboard, LogOut, Menu, X } from "lucide-react";
import { ThemeToggle } from "./ThemeToggle";

export interface NavItem {
  to: string;
  label: string;
  end?: boolean;
}

export function Layout({ nav, portal }: { nav: NavItem[]; portal: string }) {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const menuButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
    document.querySelector<HTMLAnchorElement>("#mobile-navigation a")?.focus();

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setOpen(false);
        menuButtonRef.current?.focus();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open]);

  const sidebar = (
    <nav aria-label={`${portal} navigation`} className="flex flex-col gap-1 p-4">
      <p className="px-3 pb-2 pt-1 text-[10px] font-bold uppercase tracking-[.18em] text-slate-400">Workspace</p>
      {nav.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.end}
          onClick={() => setOpen(false)}
          className={({ isActive }) =>
            `group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold transition-all duration-200 ${
              isActive
                ? "bg-gradient-to-r from-violet-600 to-indigo-600 text-white shadow-[0_8px_20px_rgba(99,102,241,.22)]"
                : "text-slate-600 hover:bg-white/80 hover:text-slate-900"
            }`
          }
        >
          <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-white/60 text-current group-[.active]:bg-white/15">
            {item.end || item.to.endsWith("/student") || item.to.endsWith("/faculty") || item.to.endsWith("/admin") ? <LayoutDashboard size={16} /> : item.label.toLowerCase().includes("student") ? <GraduationCap size={16} /> : <BookOpen size={16} />}
          </span>
          <span className="min-w-0 flex-1">{item.label}</span>
          <ChevronRight size={14} className="opacity-0 transition group-hover:opacity-50" />
        </NavLink>
      ))}
    </nav>
  );

  return (
    <div className="portal-shell relative isolate min-h-screen overflow-hidden bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-indigo-50/70 via-slate-50 to-purple-50/50">
      <div aria-hidden="true" className="pointer-events-none fixed inset-0 -z-10 overflow-hidden"><div className="absolute -right-24 -top-40 h-[26rem] w-[26rem] rounded-full bg-violet-300/20 blur-[100px]"/><div className="absolute -left-40 top-[42%] h-[28rem] w-[28rem] rounded-full bg-indigo-300/20 blur-[100px]"/></div>
      <a href="#main-content" className="skip-link">Skip to main content</a>
      <header className="sticky top-0 z-20 flex h-[4.25rem] items-center justify-between border-b border-white/70 bg-white/75 px-4 shadow-[0_8px_30px_rgba(44,46,90,.04)] backdrop-blur-xl sm:px-6">
        <div className="flex items-center gap-3">
          <button
            ref={menuButtonRef}
            className="grid h-11 w-11 place-items-center rounded-xl text-slate-600 hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500 lg:hidden"
            onClick={() => setOpen((o) => !o)}
            aria-label={open ? "Close navigation menu" : "Open navigation menu"}
            aria-expanded={open}
          >
            {open ? <X size={19} /> : <Menu size={19} />}
          </button>
          <span className="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-violet-600 to-indigo-600 text-white shadow-[0_6px_16px_rgba(99,102,241,.3)]">
            <Activity size={18} />
          </span>
          <div className="leading-tight">
            <p className="text-sm font-semibold text-slate-900">Campus Portal</p>
            <p className="text-xs text-slate-500">{portal}</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <ThemeToggle />
          <NotificationCenter />

          <div className="hidden text-right leading-tight sm:block">
            <p className="text-sm font-medium text-slate-800">{user?.name}</p>
            <p className="text-xs text-slate-500">{user?.email}</p>
          </div>

          <button onClick={logout} className="inline-flex min-h-11 items-center gap-2 rounded-full border border-slate-200/80 bg-white/75 px-3 py-2 text-xs font-semibold text-slate-600 shadow-sm transition hover:border-violet-200 hover:text-violet-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500">
            <LogOut size={14} /><span className="hidden sm:inline">Log out</span>
          </button>
        </div>
      </header>

      <div className="flex">
        <aside className="sticky top-[4.25rem] hidden h-[calc(100vh-4.25rem)] w-64 shrink-0 overflow-y-auto border-r border-white/70 bg-white/50 backdrop-blur-xl lg:block">
          {sidebar}
        </aside>
        {open && (
          <div
            className="fixed inset-0 top-[4.25rem] z-10 bg-slate-900/25 backdrop-blur-sm lg:hidden"
            onClick={() => setOpen(false)}
            role="presentation"
          >
            <aside
              id="mobile-navigation"
              className="h-full w-[min(20rem,86vw)] overflow-y-auto border-r border-white/70 bg-white/90 shadow-2xl backdrop-blur-xl"
              onClick={(e) => e.stopPropagation()}
            >
              {sidebar}
            </aside>
          </div>
        )}
        <main id="main-content" tabIndex={-1} className="min-w-0 flex-1 px-4 py-6 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-[88rem]">
            <Outlet />
          </div>
        </main>
      </div>

      {/* Floating campus assistant grounded in database with strict RBAC */}
      <ChatAssistantModal />
    </div>
  );
}
