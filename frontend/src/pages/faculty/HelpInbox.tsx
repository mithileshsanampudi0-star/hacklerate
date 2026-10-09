import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, useApi } from "../../api/client";
import type { HelpThread } from "../../api/types";
import { useAuth } from "../../auth/AuthContext";
import { HelpThreadCard } from "../../components/HelpThread";
import { Empty, PageHeader, QueryState, Tabs } from "../../components/ui";

type StatusTab = "active" | "open" | "in_progress" | "resolved";

export default function HelpInbox() {
  const qc = useQueryClient();
  const { user } = useAuth();
  const [status, setStatus] = useState<StatusTab>("active");
  const [scope, setScope] = useState<"mine" | "all">("mine");
  const url = `/faculty/help-requests?scope=${scope}${status === "active" ? "" : `&status=${status}`}`;
  const q = useApi<HelpThread[]>(url);
  const refresh = () => qc.invalidateQueries({ queryKey: [url] });

  const update = useMutation({
    mutationFn: ({ id, body }: { id: number; body: object }) => api.patch(`/faculty/help-requests/${id}`, body),
    onSuccess: refresh,
  });

  return (
    <>
      <PageHeader
        title="Help requests"
        subtitle="Study doubts and support requests from students"
        action={
          <select className="input w-auto" value={scope} onChange={(e) => setScope(e.target.value as "mine" | "all")}>
            <option value="mine">Assigned to me + unassigned</option>
            <option value="all">All requests</option>
          </select>
        }
      />
      <Tabs
        tabs={[
          { id: "active", label: "All" },
          { id: "open", label: "Open" },
          { id: "in_progress", label: "In progress" },
          { id: "resolved", label: "Resolved" },
        ]}
        value={status}
        onChange={setStatus}
      />
      <QueryState query={q}>
        {(threads) =>
          threads.length === 0 ? (
            <Empty>No requests here.</Empty>
          ) : (
            <ul className="space-y-3">
              {threads.map((t) => (
                <HelpThreadCard
                  key={t.id}
                  thread={t}
                  replyUrl={`/faculty/help-requests/${t.id}/replies`}
                  onChanged={refresh}
                  studentLink={`/faculty/students/${t.student_id}`}
                  actions={
                    <>
                      {t.assigned_to === null || (user && t.assigned_to !== user.name) ? (
                        <button className="btn-secondary px-3 py-1.5" onClick={() => update.mutate({ id: t.id, body: { assign_to_me: true } })}>
                          Assign to me
                        </button>
                      ) : null}
                      {t.status !== "resolved" ? (
                        <button className="btn-secondary px-3 py-1.5" onClick={() => update.mutate({ id: t.id, body: { status: "resolved" } })}>
                          Mark resolved
                        </button>
                      ) : (
                        <button className="btn-secondary px-3 py-1.5" onClick={() => update.mutate({ id: t.id, body: { status: "open" } })}>
                          Reopen
                        </button>
                      )}
                    </>
                  }
                />
              ))}
            </ul>
          )
        }
      </QueryState>
    </>
  );
}
