"use client";

import { useCallback, useEffect, useRef, useState } from "react";

/** Loads data once on mount; `reload()` re-runs the latest loader. */
export function useAsync<T>(fn: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const fnRef = useRef(fn);

  useEffect(() => {
    fnRef.current = fn;
  });

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setData(await fnRef.current());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- initial data load
    void reload();
  }, [reload]);

  return { data, setData, error, loading, reload };
}
