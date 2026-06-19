/**
 * Hook TanStack Query para GET /api/prevalencia.
 * Se re-ejecuta automáticamente cuando cambian los filtros (Zustand).
 */
import { useQuery } from "@tanstack/react-query"
import { useFilters } from "../store/filters"

async function fetchPrevalencia(params: Record<string, string>) {
  const qs = new URLSearchParams(params).toString()
  const res = await fetch(`/api/prevalencia?${qs}`, {
    headers: { Authorization: `Bearer ${localStorage.getItem("jwt") ?? ""}` },
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export function usePrevalencia() {
  const { periodo, sexo } = useFilters()
  return useQuery({
    queryKey: ["prevalencia", periodo, sexo],
    queryFn: () =>
      fetchPrevalencia({
        ...(periodo ? { period: periodo } : {}),
        ...(sexo ? { sexo } : {}),
      }),
  })
}
