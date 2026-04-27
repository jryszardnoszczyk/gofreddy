import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useDocumentTitle } from "@/hooks/useDocumentTitle";
import { useSessions } from "@/hooks/useSessions";
import { PageHeader } from "@/components/shared/PageHeader";
import { AlertBanner } from "@/components/shared/AlertBanner";
import { Briefcase } from "lucide-react";
import { cn } from "@/lib/cn";

function formatDuration(startedAt: string, completedAt: string | null): string {
  if (!completedAt) return "running…";
  const ms = new Date(completedAt).getTime() - new Date(startedAt).getTime();
  if (ms <= 0) return "0m";
  const totalMinutes = Math.floor(ms / 60000);
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}

function formatTime(dateStr: string): string {
  return new Date(dateStr).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

const STATUS_FILTERS = ["all", "running", "completed"] as const;

const statusBadgeClass: Record<string, string> = {
  running: "bg-blue-500/20 text-blue-400",
  completed: "bg-emerald-500/20 text-emerald-400",
  failed: "bg-red-500/20 text-red-400",
};

export function SessionsPage() {
  useDocumentTitle("Sessions");
  const [searchParams] = useSearchParams();
  const clientFilter = searchParams.get("client") ?? undefined;
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined);
  const {
    sessions,
    isLoading,
    error,
    selectedActions,
    actionsLoading,
    actionsError,
    selectSession,
    selectedSessionId,
  } = useSessions(statusFilter, clientFilter);

  const totalHours = sessions.reduce((sum, s) => {
    if (!s.completed_at) return sum;
    return sum + (new Date(s.completed_at).getTime() - new Date(s.started_at).getTime()) / 3600000;
  }, 0);
  const totalActions = sessions.reduce((sum, s) => sum + s.action_count, 0);
  const totalCredits = sessions.reduce((sum, s) => sum + s.total_credits, 0);

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
      <PageHeader
        icon={<Briefcase className="h-5 w-5" />}
        title="Sessions"
        description="Contractor work tracking"
      />

      {error && <AlertBanner message={error} variant="error" className="mt-4" />}

      {/* Status toggle */}
      <div className="mt-4 flex gap-2">
        {STATUS_FILTERS.map((s) => (
          <button
            key={s}
            onClick={() => setStatusFilter(s === "all" ? undefined : s)}
            className={cn(
              "rounded-lg px-3 py-1 text-sm capitalize transition-colors",
              (s === "all" && !statusFilter) || statusFilter === s
                ? "bg-white/8 text-zinc-100"
                : "text-zinc-500 hover:bg-surface-raised hover:text-zinc-300",
            )}
          >
            {s}
          </button>
        ))}
      </div>

      {/* Aggregation stats */}
      <div className="mt-4 flex gap-3">
        {[
          { label: "Sessions", value: sessions.length },
          { label: "Hours", value: totalHours.toFixed(1) },
          { label: "Actions", value: totalActions },
          { label: "Credits", value: totalCredits },
        ].map((stat) => (
          <div key={stat.label} className="rounded-lg border border-border-subtle bg-surface px-4 py-2">
            <div className="text-xs text-zinc-500">{stat.label}</div>
            <div className="text-lg font-semibold text-zinc-100">{stat.value}</div>
          </div>
        ))}
      </div>

      {/* Session cards */}
      {isLoading ? (
        <div className="mt-6 space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 animate-pulse rounded-lg bg-surface" />
          ))}
        </div>
      ) : sessions.length === 0 ? (
        <div className="mt-12 flex flex-col items-center text-center">
          <Briefcase className="h-12 w-12 text-zinc-600" />
          <h3 className="mt-4 text-lg font-medium text-zinc-300">No sessions yet</h3>
          <p className="mt-2 max-w-md text-sm text-zinc-500">
            When contractors use the freddy CLI, their work will appear here.
          </p>
        </div>
      ) : (
        <div className="mt-6 space-y-3">
          {sessions.map((session) => (
            <div
              key={session.id}
              className={cn(
                "rounded-xl border p-5 transition-colors cursor-pointer",
                selectedSessionId === session.id
                  ? "border-brand-500 bg-brand-500/5"
                  : "border-border-subtle bg-surface hover:border-zinc-600",
              )}
              onClick={() => selectSession(session.id === selectedSessionId ? null : session.id)}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  <span className="rounded bg-zinc-800 px-1.5 py-0.5 text-[10px] text-zinc-400">
                    {session.session_type}
                  </span>
                  <h3 className="font-medium text-zinc-100">{session.client_name}</h3>
                  <span className={cn("rounded px-1.5 py-0.5 text-[10px] font-medium", statusBadgeClass[session.status] ?? "bg-zinc-700 text-zinc-400")}>
                    {session.status}
                  </span>
                </div>
                <span className="text-xs text-zinc-500">{formatDate(session.started_at)}</span>
              </div>

              {session.summary && (
                <p className="mt-2 text-sm text-zinc-400 line-clamp-2">{session.summary}</p>
              )}

              <div className="mt-3 flex items-center gap-4 text-xs text-zinc-500">
                <span>{session.action_count} actions</span>
                <span>{session.total_credits} credits</span>
                <span>{formatDuration(session.started_at, session.completed_at)}</span>
                {session.purpose && <span className="truncate max-w-[200px]">{session.purpose}</span>}
              </div>

              {/* Expandable action timeline */}
              {selectedSessionId === session.id && (
                <div className="mt-4 border-t border-white/5 pt-4">
                  {actionsLoading ? (
                    <div className="space-y-2">
                      {[1, 2, 3].map((i) => (
                        <div key={i} className="h-10 animate-pulse rounded-lg bg-surface-raised" />
                      ))}
                    </div>
                  ) : actionsError ? (
                    <p className="text-sm text-red-400">Failed to load actions: {actionsError}</p>
                  ) : selectedActions.length === 0 ? (
                    <p className="text-sm text-zinc-500">No actions recorded.</p>
                  ) : (
                    selectedActions.map((action) => (
                      <div key={action.id} className="py-2 border-b border-white/5 last:border-0">
                        <div className="flex items-center gap-2 text-sm">
                          <span className="text-zinc-500">{formatTime(action.created_at)}</span>
                          <span className="font-medium text-zinc-200">{action.tool_name}</span>
                          <span className={action.status === "success" ? "text-emerald-400" : "text-red-400"}>●</span>
                          {action.duration_ms != null && (
                            <span className="text-zinc-600">{action.duration_ms}ms</span>
                          )}
                          {action.cost_credits > 0 && (
                            <span className="text-zinc-600">{action.cost_credits}cr</span>
                          )}
                        </div>
                        <div className="text-sm text-zinc-400 mt-1">
                          {typeof action.output_summary?.summary === "string" ? action.output_summary.summary : "No summary"}
                        </div>
                        <details className="mt-1" onClick={(e) => e.stopPropagation()}>
                          <summary className="text-xs text-zinc-600 cursor-pointer hover:text-zinc-400">
                            Raw data
                          </summary>
                          <pre className="text-xs text-zinc-500 mt-1 overflow-x-auto max-h-40 overflow-y-auto rounded bg-surface-raised p-2">
                            {JSON.stringify({ input: action.input_summary, output: action.output_summary }, null, 2)}
                          </pre>
                        </details>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
