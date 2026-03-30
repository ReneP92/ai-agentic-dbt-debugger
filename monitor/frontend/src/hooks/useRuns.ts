import { useQuery } from '@tanstack/react-query'
import type { RunInfo, MonitorEvent } from '../types'

export function useRunsList() {
  return useQuery<RunInfo[]>({
    queryKey: ['runs'],
    queryFn: async () => {
      const res = await fetch('/api/runs')
      if (!res.ok) throw new Error('Failed to fetch runs')
      return res.json() as Promise<RunInfo[]>
    },
    refetchInterval: 10_000,
    staleTime: 5_000,
  })
}

export function useRunEvents(runId: string | null) {
  return useQuery<MonitorEvent[]>({
    queryKey: ['run-events', runId],
    queryFn: async () => {
      const res = await fetch(`/api/runs/${runId}`)
      if (!res.ok) throw new Error('Failed to fetch run events')
      return res.json() as Promise<MonitorEvent[]>
    },
    enabled: !!runId,
    staleTime: Infinity,
  })
}
