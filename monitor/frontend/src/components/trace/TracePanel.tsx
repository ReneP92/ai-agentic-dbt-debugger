import { useState, useEffect } from 'react'
import { GitBranch, Clock, ToggleLeft } from 'lucide-react'
import clsx from 'clsx'
import { useStore } from '../../store/useStore'
import { TraceTree } from './TraceTree'
import { TimelineView } from './TimelineView'
import { ThinkingViewer } from './ThinkingViewer'
import { formatDuration, formatTokens, formatCost } from '../../lib/formatters'

type Tab = 'tree' | 'timeline'

export function TracePanel() {
  const [activeTab, setActiveTab] = useState<Tab>('tree')
  const selectedRunId = useStore((s) => s.selectedRunId)
  const liveRunId = useStore((s) => s.liveRunId)
  const runs = useStore((s) => s.runs)
  const autoScroll = useStore((s) => s.autoScroll)
  const setAutoScroll = useStore((s) => s.setAutoScroll)

  const run = selectedRunId ? runs[selectedRunId] : null
  const isLive = selectedRunId === liveRunId

  const status = !run ? null
    : run.success === null ? 'running'
    : run.success === 1 ? 'success'
    : 'error'

  return (
    <div className="flex flex-col h-full flex-1 min-w-0">
      {/* Metrics bar */}
      {run && (
        <div className="grid grid-cols-4 gap-px border-b border-border bg-border shrink-0">
          <MetricCard label="Status">
            {status === 'running' && (
              <span className="flex items-center gap-1.5 text-accent-amber">
                <span className="w-1.5 h-1.5 rounded-full bg-accent-amber animate-pulse" />
                running
              </span>
            )}
            {status === 'success' && (
              <span className="flex items-center gap-1.5 text-accent-green">
                <span className="w-1.5 h-1.5 rounded-full bg-accent-green" />
                success
              </span>
            )}
            {status === 'error' && (
              <span className="flex items-center gap-1.5 text-accent-red">
                <span className="w-1.5 h-1.5 rounded-full bg-accent-red" />
                failed
              </span>
            )}
          </MetricCard>
          <MetricCard label="Agent">
            <span className="truncate">{run.agent_type || '-'}</span>
          </MetricCard>
          <MetricCard label="Duration">
            <LiveDuration run={run} isLive={isLive} />
          </MetricCard>
          <MetricCard label="Input">
            {formatTokens(run.total_input_tokens)}
          </MetricCard>
          <MetricCard label="Output">
            {formatTokens(run.total_output_tokens)}
          </MetricCard>
          <MetricCard label="Cost">
            <span className="text-accent-amber">{formatCost(run.estimated_cost_usd)}</span>
          </MetricCard>
          <MetricCard label="Run ID">
            <span className="font-mono truncate text-text-muted" title={run.run_id}>
              {run.run_id.slice(0, 16)}
            </span>
          </MetricCard>
          <MetricCard label="Live">
            {isLive ? (
              <span className="flex items-center gap-1 text-accent-green">
                <span className="w-1.5 h-1.5 rounded-full bg-accent-green animate-pulse" />
                yes
              </span>
            ) : (
              <span className="text-text-muted">no</span>
            )}
          </MetricCard>
        </div>
      )}

      {/* Tab bar */}
      <div className="flex items-center justify-between px-3 border-b border-border shrink-0 h-9">
        <div className="flex">
          <TabButton
            active={activeTab === 'tree'}
            onClick={() => setActiveTab('tree')}
            icon={<GitBranch size={12} />}
          >
            Trace
          </TabButton>
          <TabButton
            active={activeTab === 'timeline'}
            onClick={() => setActiveTab('timeline')}
            icon={<Clock size={12} />}
          >
            Timeline
          </TabButton>
        </div>

        {/* Auto-scroll toggle */}
        <label className="flex items-center gap-1.5 cursor-pointer text-[10px] text-text-muted hover:text-text-secondary select-none">
          <ToggleLeft size={12} />
          <span>Auto-scroll</span>
          <input
            type="checkbox"
            checked={autoScroll}
            onChange={(e) => setAutoScroll(e.target.checked)}
            className="sr-only"
          />
          <div
            className={clsx(
              'w-7 h-4 rounded-full relative transition-colors',
              autoScroll ? 'bg-accent-blue/60' : 'bg-elevated',
            )}
          >
            <div
              className={clsx(
                'absolute top-0.5 w-3 h-3 rounded-full transition-transform bg-white/80',
                autoScroll ? 'translate-x-3.5' : 'translate-x-0.5',
              )}
            />
          </div>
        </label>
      </div>

      {/* Main content */}
      <div className="flex-1 min-h-0 flex flex-col">
        <div className="flex-1 min-h-0">
          {activeTab === 'tree' && <TraceTree />}
          {activeTab === 'timeline' && <TimelineView />}
        </div>

        {/* Thinking drawer */}
        <ThinkingViewer />
      </div>
    </div>
  )
}

function MetricCard({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="bg-panel px-3 py-2">
      <div className="text-[9px] text-text-muted uppercase tracking-wider mb-0.5">{label}</div>
      <div className="text-[11px] font-medium text-text-secondary truncate">{children}</div>
    </div>
  )
}

function TabButton({
  active,
  onClick,
  icon,
  children,
}: {
  active: boolean
  onClick: () => void
  icon: React.ReactNode
  children: React.ReactNode
}) {
  return (
    <button
      onClick={onClick}
      className={clsx(
        'flex items-center gap-1.5 px-3 h-full text-xs transition-colors border-b-2',
        active
          ? 'text-text-primary border-accent-blue'
          : 'text-text-muted border-transparent hover:text-text-secondary',
      )}
    >
      {icon}
      {children}
    </button>
  )
}

function LiveDuration({ run, isLive }: { run: { started_at: string; total_duration_s: number | null }; isLive: boolean }) {
  const [, setTick] = useState(0)

  useEffect(() => {
    if (!isLive) return
    const interval = setInterval(() => setTick((t) => t + 1), 1000)
    return () => clearInterval(interval)
  }, [isLive])

  if (run.total_duration_s != null) {
    return <>{formatDuration(run.total_duration_s)}</>
  }
  if (isLive) {
    const elapsed = (Date.now() - new Date(run.started_at).getTime()) / 1000
    return <span className="text-accent-amber">{formatDuration(elapsed)}</span>
  }
  return <>-</>
}
