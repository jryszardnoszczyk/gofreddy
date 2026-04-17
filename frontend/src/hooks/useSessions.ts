import { useCallback, useEffect, useState } from "react";
import {
  listSessions as apiListSessions,
  getSessionActions as apiGetSessionActions,
  type AgentSession,
  type ActionLogEntry,
} from "@/lib/api";

export interface UseSessionsReturn {
  sessions: AgentSession[];
  isLoading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  selectedActions: ActionLogEntry[];
  actionsLoading: boolean;
  actionsError: string | null;
  selectSession: (id: string | null) => void;
  selectedSessionId: string | null;
}

export function useSessions(statusFilter?: string): UseSessionsReturn {
  const [sessions, setSessions] = useState<AgentSession[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [selectedActions, setSelectedActions] = useState<ActionLogEntry[]>([]);
  const [actionsLoading, setActionsLoading] = useState(false);
  const [actionsError, setActionsError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await apiListSessions(statusFilter);
      data.sort((a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime());
      setSessions(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load sessions");
    } finally {
      setIsLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const selectSession = useCallback((id: string | null) => {
    setSelectedSessionId(id);
    setActionsError(null);
    if (!id) {
      setSelectedActions([]);
      return;
    }
    setActionsLoading(true);
    apiGetSessionActions(id)
      .then(setSelectedActions)
      .catch((err) => {
        setSelectedActions([]);
        setActionsError(err instanceof Error ? err.message : "Failed to load actions");
      })
      .finally(() => setActionsLoading(false));
  }, []);

  return {
    sessions,
    isLoading,
    error,
    refresh,
    selectedActions,
    actionsLoading,
    actionsError,
    selectSession,
    selectedSessionId,
  };
}
