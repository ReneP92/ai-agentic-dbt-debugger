import clsx from 'clsx'
import type { RunInfo } from '../../types'
import { Badge } from '../ui/Badge'
import { formatRelativeTime, formatDuration, formatCost, agentBadgeVariant } from '../../lib/formatters'

interface RunCardProps {
  run: RunInfo
  isSelected: boolean
  isLive: boolean
  onClick: () => void
}

export function RunCard({ run, isSelected, isLive, onClick }: RunCardProps) {
  const status =
    run.success === null ? 'running' : run.success === 1 ? 'success' : 'error'

  return (
    <button
      onClick={onClick}
      className={clsx(
        'w-full text-left px-3 py-2.5 border-b border-border-subtle transition-colors',
        'hover:bg-elevated/60',
        isSelected && 'bg-elevated border-l-2 border-l-accent-blue',
        !isSelected && 'border-l-2 border-l-transparent',
        isLive && !isSelected && 'border-l-accent-green',
      )}
    >
      <div className="flex items-center justify-between gap-2 mb-1">
        <Badge variant={agentBadgeVariant(run.agent_type)} size="xs">
          {run.agent_type || 'agent'}
        </Badge>
        <div className="flex items-center gap-1.5">
          {status === 'running' && (
            <span className="w-1.5 h-1.5 rounded-full bg-accent-green animate-pulse" />
          )}
          {status === 'success' && (
            <span className="w-1.5 h-1.5 rounded-full bg-accent-green" />
          )}
          {status === 'error' && (
            <span className="w-1.5 h-1.5 rounded-full bg-accent-red" />
          )}
          <span className="text-[10px] text-text-muted">
            {formatRelativeTime(run.started_at)}
          </span>
        </div>
      </div>

      <div className="flex items-center justify-between text-[11px] text-text-muted">
        <span className="font-mono truncate max-w-[120px]" title={run.run_id}>
          {run.run_id}
        </span>
        <div className="flex items-center gap-2 shrink-0">
          {run.total_duration_s != null && (
            <span>{formatDuration(run.total_duration_s)}</span>
          )}
          {run.estimated_cost_usd != null && (
            <span className="text-accent-amber">{formatCost(run.estimated_cost_usd)}</span>
          )}
        </div>
      </div>
    </button>
  )
}
