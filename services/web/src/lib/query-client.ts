import { MutationCache, QueryCache, QueryClient } from "@tanstack/react-query";

import { ApiError } from "@/lib/api";

export const SESSION_KEY = ["session"] as const;
export const NETWORK_KEY = ["network"] as const;
export const HEALTH_KEY = ["health"] as const;

const isClientError = (error: unknown): boolean =>
  error instanceof ApiError && error.status !== null && error.status < 500;

/**
 * Un 401 en cualquier consulta significa que la sesión del BFF caducó: se vuelve al inicio de
 * sesión. Solo se reintenta una vez ante fallos de red o 5xx; un 4xx es una respuesta definitiva.
 */
export function createQueryClient({ retry = true }: { retry?: boolean } = {}): QueryClient {
  const onError = (error: unknown) => {
    if (error instanceof ApiError && error.status === 401) client.setQueryData(SESSION_KEY, null);
  };
  const client: QueryClient = new QueryClient({
    queryCache: new QueryCache({ onError }),
    mutationCache: new MutationCache({ onError }),
    defaultOptions: {
      queries: {
        retry: (count, error) => retry && !isClientError(error) && count < 1,
        refetchOnWindowFocus: false,
      },
      mutations: { retry: false },
    },
  });
  return client;
}
