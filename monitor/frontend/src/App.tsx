import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useWebSocket } from './hooks/useWebSocket'
import { AppShell } from './components/layout/AppShell'

const queryClient = new QueryClient()

function MonitorApp() {
  useWebSocket()
  return <AppShell />
}

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <MonitorApp />
    </QueryClientProvider>
  )
}
