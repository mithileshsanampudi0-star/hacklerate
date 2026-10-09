import { useState, useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { NotificationItem } from "../api/types";

export function NotificationCenter() {
  const [open, setOpen] = useState(false);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  async function fetchNotifications() {
    try {
      setLoading(true);
      const res = await api.get<{ unread_count: number; items: NotificationItem[] }>("/notifications?limit=15");
      setNotifications(res.data.items);
      setUnreadCount(res.data.unread_count);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 30000); // 30s polling
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  async function handleMarkRead(id: number, e: React.MouseEvent) {
    e.stopPropagation();
    try {
      await api.patch(`/notifications/${id}/read`);
      setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, is_read: true } : n)));
      setUnreadCount((c) => Math.max(0, c - 1));
    } catch {
      // ignore
    }
  }

  async function handleMarkAllRead() {
    try {
      await api.post("/notifications/read-all");
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
      setUnreadCount(0);
    } catch {
      // ignore
    }
  }

  const severityColors = {
    critical: "bg-rose-500",
    warning: "bg-amber-500",
    info: "bg-indigo-500",
    success: "bg-emerald-500",
  };

  return (
    <div className="relative" ref={menuRef}>
      <button
        onClick={() => {
          setOpen((o) => !o);
          if (!open) fetchNotifications();
        }}
        className="relative grid h-11 w-11 place-items-center rounded-lg text-slate-500 hover:bg-slate-100 hover:text-slate-800 transition"
        title="Notifications"
        aria-label="View notifications"
        aria-expanded={open}
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
          <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
        </svg>
        {unreadCount > 0 && (
          <span className="absolute top-1 right-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-rose-600 px-1 text-[10px] font-bold text-white shadow-sm ring-1 ring-white">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-80 sm:w-96 rounded-2xl border border-slate-200 bg-white p-3 shadow-xl z-50 animate-in fade-in slide-in-from-top-2 duration-150">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2 px-1">
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-slate-900">Notifications</span>
              {unreadCount > 0 && (
                <span className="rounded-full bg-rose-100 px-2 py-0.5 text-[11px] font-semibold text-rose-700">
                  {unreadCount} new
                </span>
              )}
            </div>
            {unreadCount > 0 && (
              <button
                onClick={handleMarkAllRead}
                className="text-xs font-medium text-indigo-600 hover:text-indigo-800"
              >
                Mark all read
              </button>
            )}
          </div>

          <div className="mt-2 max-h-80 overflow-y-auto divide-y divide-slate-100">
            {loading && notifications.length === 0 ? (
              <p className="py-6 text-center text-xs text-slate-400">Loading alerts…</p>
            ) : notifications.length === 0 ? (
              <div className="py-8 text-center">
                <span className="text-2xl">🔔</span>
                <p className="mt-1 text-xs text-slate-500">No notifications at this time.</p>
              </div>
            ) : (
              notifications.map((n) => (
                <div
                  key={n.id}
                  className={`flex items-start gap-2.5 p-2.5 rounded-lg transition ${
                    n.is_read ? "opacity-75 hover:bg-slate-50" : "bg-indigo-50/50 hover:bg-indigo-50"
                  }`}
                >
                  <span className={`mt-1 h-2 w-2 shrink-0 rounded-full ${severityColors[n.severity] || "bg-slate-400"}`} />
                  <div className="flex-1 min-w-0">
                    <p className={`text-xs ${n.is_read ? "font-medium text-slate-700" : "font-semibold text-slate-900"}`}>
                      {n.title}
                    </p>
                    <p className="mt-0.5 text-xs text-slate-600 leading-relaxed line-clamp-2">{n.message}</p>
                    <div className="mt-1.5 flex items-center justify-between gap-2">
                      <span className="text-[10px] text-slate-400">
                        {n.created_at ? new Date(n.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "Recent"}
                      </span>
                      {n.link_url && (
                        <Link
                          to={n.link_url}
                          onClick={() => setOpen(false)}
                          className="text-[11px] font-semibold text-indigo-600 hover:underline"
                        >
                          View Details →
                        </Link>
                      )}
                    </div>
                  </div>
                  {!n.is_read && (
                    <button
                      onClick={(e) => handleMarkRead(n.id, e)}
                      title="Mark as read"
                      className="text-slate-400 hover:text-slate-600 p-0.5 text-xs"
                    >
                      ✓
                    </button>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
