import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

const queryClient = new QueryClient()

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-background text-foreground">
        <h1 className="text-2xl font-medium p-8">MetSyn Dashboard</h1>
        <p className="px-8 text-muted-foreground">Sprint 0 — skeleton OK</p>
      </div>
    </QueryClientProvider>
  )
}
