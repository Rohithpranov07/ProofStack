"use client";

import { useEffect, useState, useCallback } from "react";
import { getDashboard } from "@/lib/api";
import type { DashboardResponse } from "@/types/dashboard";

interface UseDashboardResult {
  data: DashboardResponse | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useDashboard(jobId: string | undefined): UseDashboardResult {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);

  const fetchData = useCallback(async () => {
    if (!jobId) return;

    setLoading(true);
    setError(null);

    try {
      const result = await getDashboard(jobId);
      setData(result);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to load dashboard";

      // Auto-retry once
      if (retryCount < 1) {
        setRetryCount((prev) => prev + 1);
        return;
      }

      setError(message);
    } finally {
      setLoading(false);
    }
  }, [jobId, retryCount]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const refetch = useCallback(() => {
    setRetryCount(0);
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch };
}
