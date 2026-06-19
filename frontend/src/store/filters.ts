/**
 * Estado global de filtros — Zustand.
 * Período, género y rango de edad son las query-keys compartidas
 * entre todos los componentes de ECharts.
 */
import { create } from "zustand"

interface FiltersState {
  periodo: string | null
  sexo: "M" | "F" | null
  edadMin: number
  edadMax: number
  setPeriodo: (p: string | null) => void
  setSexo: (s: "M" | "F" | null) => void
  setEdad: (min: number, max: number) => void
}

export const useFilters = create<FiltersState>((set) => ({
  periodo: null,
  sexo: null,
  edadMin: 18,
  edadMax: 70,
  setPeriodo: (periodo) => set({ periodo }),
  setSexo: (sexo) => set({ sexo }),
  setEdad: (edadMin, edadMax) => set({ edadMin, edadMax }),
}))
