import { useState, useEffect } from 'react'
import { Search, RefreshCw, Filter } from 'lucide-react'
import clsx from 'clsx'
import { useStore } from '../../store/useStore'
import { useRunsList, useRunEvents } from '../../hooks/useRuns'
import { RunCard } from './RunCard'

const STATUS_OPTIONS = ['all', 'running', 'success', 'error'] as const
type StatusFilter = (typeof STATUS_OPTIONS)[number]

export function RunsList() {
  const runs = useStore((s) => s.runs)
  const runOrder = useStore((s) => s.runOrder)
  const selectedRunId = useStore((s) => s.selectedRunId)
  const liveRunId = useStore((s) => s.liveRunId)
  const prependRuns = useStore((s) => s.prependRuns)
  const selectRun = useStore((s) => s.selectRun)
  const loadHistoricalRun = useStore((s) => s.loadHistoricalRun)

  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
  const [pendingHistoricalRunId, setPendingHistoricalRunId] = useState<string | null>(null)

  const { data: historicalRuns, refetch } = useRunsList()
  const { data: historicalEvents } = useRunEvents(pendingHistoricalRunId)

  // Populate store with historical runs from API
  useEffect(() => {
    if (historicalRuns) {
      prependRuns(historicalRuns)
    }
  }, [historicalRuns, prependRuns])

  // Load events when we get them back
  useEffect(() => {
    if (pendingHistoricalRunId && historicalEvents) {
      loadHistoricalRun(pendingHistoricalRunId, historicalEvents)
      setPendingHistoricalRunId(null)
    }
  }, [pendingHistoricalRunId, historicalEvents, loadHistoricalRun])

  function handleSelectRun(runId: string) {
    if (runId === liveRunId) {
      selectRun(runId)
    } else {
      selectRun(runId)
      setPendingHistoricalRunId(runId)
    }
  }

  const filteredRunIds = runOrder.filter((id) => {
    const run = runs[id]
    if (!run) return false

    if (search) {
      const q = search.toLowerCase()
      if (!run.agent_type.toLowerCase().includes(q) && !run.run_id.toLowerCase().includes(q)) {
        return false
      }
    }

    if (statusFilter !== 'all') {
      const status = run.success === null ? 'running' : run.success === 1 ? 'success' : 'error'
      if (status !== statusFilter) return false
    }

    return true
  })

  return (
    <aside className="w-[280px] shrink-0 flex flex-col border-r border-border bg-panel">
      {/* Header */}
      <div className="px-3 pt-3 pb-2 border-b border-border">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold text-text-secondary uppercase tracking-wider">
            Runs
          </span>
          <div className="flex items-center gap-1">
            <span className="text-xs text-text-muted bg-elevated px-1.5 py-0.5 rounded">
              {filteredRunIds.length}
            </span>
            <button
              onClick={() => void refetch()}
              className="p-1 rounded text-text-muted hover:text-text-secondary hover:bg-elevated transition-colors"
              title="Refresh runs"
            >
              <RefreshCw size={12} />
            </button>
          </div>
        </div>

        {/* Search */}
        <div className="relative mb-2">
          <Search size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-text-muted" />
          <input
            type="text"
            placeholder="Search runs..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-elevated border border-border rounded text-xs py-1.5 pl-7 pr-2 text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent-blue/60 transition-colors"
          />
        </div>

        {/* Status filter */}
        <div className="flex gap-1">
          {STATUS_OPTIONS.map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={clsx(
                'flex-1 text-[10px] py-1 rounded capitalize transition-colors border',
                statusFilter === s
                  ? 'bg-accent-blue/20 text-accent-blue border-accent-blue/40'
                  : 'text-text-muted border-transparent hover:border-border hover:text-text-secondary',
              )}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Runs list */}
      <div className="flex-1 overflow-y-auto scrollbar-thin">
        {filteredRunIds.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-32 gap-2">
            <Filter size={20} className="text-text-muted" />
            <p className="text-xs text-text-muted">
              {runOrder.length === 0 ? 'No runs yet' : 'No matching runs'}
            </p>
          </div>
        ) : (
          filteredRunIds.map((id) => {
            const run = runs[id]
            if (!run) return null
            return (
              <RunCard
                key={id}
                run={run}
                isSelected={id === selectedRunId}
                isLive={id === liveRunId}
                onClick={() => handleSelectRun(id)}
              />
            )
          })
        )}
      </div>
    </aside>
  )
}
