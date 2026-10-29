import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { HEALTH_KEY, SESSION_KEY } from "@/lib/query-client";
import type { Role } from "@/lib/types";

export const ROLE_LABELS: Record<Role, string> = {
  coordinator: "Coordinador de operaciones",
  operator: "Operador de atención",
};

export function useSession() {
  return useQuery({
    queryKey: SESSION_KEY,
    queryFn: async (): Promise<Role | null> => (await api.session()).role,
  });
}

export function useLogin() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: api.login,
    onSuccess: ({ role }) => {
      client.setQueryData(SESSION_KEY, role);
    },
  });
}

export function useLogout() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: api.logout,
    onSettled: () => {
      client.removeQueries({
        predicate: ({ queryKey }) =>
          queryKey[0] !== SESSION_KEY[0] && queryKey[0] !== HEALTH_KEY[0],
      });
      client.setQueryData(SESSION_KEY, null);
    },
  });
}
