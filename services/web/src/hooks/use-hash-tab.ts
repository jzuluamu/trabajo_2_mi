import { useCallback, useEffect, useState } from "react";

/** Pestaña activa en `#hash`: recargar o compartir el enlace conserva la vista. */
export function useHashTab<T extends string>(allowed: readonly T[], fallback: T) {
  const read = useCallback((): T => {
    const hash = window.location.hash.slice(1);
    return (allowed as readonly string[]).includes(hash) ? (hash as T) : fallback;
  }, [allowed, fallback]);
  const [tab, setTab] = useState<T>(read);

  useEffect(() => {
    const onHashChange = () => {
      setTab(read());
    };
    window.addEventListener("hashchange", onHashChange);
    return () => {
      window.removeEventListener("hashchange", onHashChange);
    };
  }, [read]);

  const select = useCallback((next: string) => {
    setTab(next as T);
    window.history.replaceState(null, "", `#${next}`);
  }, []);

  return [allowed.includes(tab) ? tab : fallback, select] as const;
}
