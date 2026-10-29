import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { api } from "@/lib/api";
import { HEALTH_KEY, NETWORK_KEY } from "@/lib/query-client";

export const useNetwork = () => useQuery({ queryKey: NETWORK_KEY, queryFn: api.network });

export const useHealth = () =>
  useQuery({ queryKey: HEALTH_KEY, queryFn: api.health, refetchInterval: 15_000 });

/** Acción del coordinador: si sale bien, avisa y vuelve a leer la red; el error queda en `error`. */
export function useNetworkMutation<TVariables, TResult>(
  mutationFn: (variables: TVariables) => Promise<TResult>,
  successMessage: (variables: TVariables, result: TResult) => string,
) {
  const client = useQueryClient();
  return useMutation({
    mutationFn,
    onSuccess: async (result, variables) => {
      toast.success(successMessage(variables, result));
      await client.invalidateQueries({ queryKey: NETWORK_KEY });
    },
  });
}
