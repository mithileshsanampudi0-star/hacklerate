import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import {
  Users,
  Search,
  Filter,
  CheckCircle,
  XCircle,
  Shield,
  GraduationCap,
  Briefcase,
  AlertCircle,
  RefreshCw,
} from "lucide-react";
import { api, errorMessage, useApi } from "../../api/client";
import type { UserProfile } from "../../api/types";

export default function AdminUsers() {
  const queryClient = useQueryClient();
  const [roleFilter, setRoleFilter] = useState<string>("");
  const [search, setSearch] = useState("");
  const [updatingId, setUpdatingId] = useState<number | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const queryParams = new URLSearchParams();
  if (roleFilter) queryParams.set("role", roleFilter);
  if (search.trim()) queryParams.set("search", search.trim());
  const queryString = queryParams.toString() ? `?${queryParams.toString()}` : "";

  const { data: users, isLoading, error } = useApi<UserProfile[]>(`/admin/users${queryString}`);

  const handleToggleActive = async (user: UserProfile) => {
    setUpdatingId(user.id);
    setActionError(null);
    try {
      await api.patch(`/admin/users/${user.id}`, { is_active: !user.is_active });
      await queryClient.invalidateQueries({ queryKey: [`/admin/users${queryString}`] });
    } catch (err) {
      setActionError(errorMessage(err));
    } finally {
      setUpdatingId(null);
    }
  };

  const getRoleBadge = (role: string) => {
    switch (role) {
      case "admin":
        return (
          <span className="inline-flex items-center gap-1 rounded-md bg-purple-50 px-2 py-1 text-xs font-semibold text-purple-700">
            <Shield className="h-3 w-3" />
            Admin
          </span>
        );
      case "faculty":
        return (
          <span className="inline-flex items-center gap-1 rounded-md bg-blue-50 px-2 py-1 text-xs font-semibold text-blue-700">
            <Briefcase className="h-3 w-3" />
            Faculty
          </span>
        );
      case "student":
        return (
          <span className="inline-flex items-center gap-1 rounded-md bg-emerald-50 px-2 py-1 text-xs font-semibold text-emerald-700">
            <GraduationCap className="h-3 w-3" />
            Student
          </span>
        );
      default:
        return (
          <span className="rounded-md bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-700">
            {role}
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <div className="inline-flex items-center gap-2 rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700">
          <Users className="h-3.5 w-3.5" />
          Access & Security
        </div>
        <h1 className="mt-1 text-2xl font-bold tracking-tight text-slate-900">
          User Management
        </h1>
        <p className="text-sm text-slate-500">
          View all registered portal accounts, filter by role, and control active status.
        </p>
      </div>

      {actionError && (
        <div className="flex items-center gap-3 rounded-xl border border-rose-200 bg-rose-50 p-4 text-rose-800 text-sm">
          <AlertCircle className="h-5 w-5 text-rose-600 shrink-0" />
          <span>{actionError}</span>
        </div>
      )}

      {/* Filters and Search Bar */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search by email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-xl border border-slate-200 bg-white py-2 pl-10 pr-4 text-sm text-slate-900 placeholder:text-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-slate-400" />
          <span className="text-xs font-medium text-slate-500">Role:</span>
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="">All Roles</option>
            <option value="student">Students</option>
            <option value="faculty">Faculty</option>
            <option value="admin">Administrators</option>
          </select>
        </div>
      </div>

      {/* Users Table */}
      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        {isLoading ? (
          <div className="flex h-64 items-center justify-center">
            <RefreshCw className="h-8 w-8 animate-spin text-indigo-600" />
          </div>
        ) : error ? (
          <div className="p-6 text-center text-sm text-rose-600">
            Failed to load users: {errorMessage(error)}
          </div>
        ) : !users || users.length === 0 ? (
          <div className="p-12 text-center text-sm text-slate-500">
            No users match the selected criteria.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-600">
              <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-wider text-slate-500">
                <tr>
                  <th className="px-6 py-3.5">Name / Identity</th>
                  <th className="px-6 py-3.5">Email</th>
                  <th className="px-6 py-3.5">Role</th>
                  <th className="px-6 py-3.5">Details</th>
                  <th className="px-6 py-3.5">Registered</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-50/70 transition-colors">
                    <td className="px-6 py-4 font-semibold text-slate-900">
                      {u.name || u.email}
                    </td>
                    <td className="px-6 py-4 font-mono text-xs text-slate-600">
                      {u.email}
                    </td>
                    <td className="px-6 py-4">
                      {getRoleBadge(u.role)}
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-500">
                      {u.extra || "—"}
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-400">
                      {u.created_at || "—"}
                    </td>
                    <td className="px-6 py-4">
                      {u.is_active ? (
                        <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700">
                          <CheckCircle className="h-3 w-3" />
                          Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 rounded-full bg-rose-50 px-2 py-0.5 text-xs font-medium text-rose-700">
                          <XCircle className="h-3 w-3" />
                          Inactive
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => handleToggleActive(u)}
                        disabled={updatingId === u.id}
                        className={`text-xs font-semibold px-3 py-1.5 rounded-lg border transition-colors ${
                          u.is_active
                            ? "border-rose-200 text-rose-700 hover:bg-rose-50"
                            : "border-emerald-200 text-emerald-700 hover:bg-emerald-50"
                        } disabled:opacity-50`}
                      >
                        {updatingId === u.id
                          ? "Saving..."
                          : u.is_active
                          ? "Deactivate"
                          : "Activate"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
