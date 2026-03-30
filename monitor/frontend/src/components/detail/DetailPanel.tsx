import { X } from 'lucide-react'
import { useStore } from '../../store/useStore'
import { LLMDetail } from './LLMDetail'
import { ToolDetail } from './ToolDetail'
import { MetricsGrid, ToolSummaryTable } from './MetricsGrid'
import { Badge } from '../ui/Badge'
import { formatDuration, agentBadgeVariant } from '../../lib/formatters'
import type { InvocationMetrics } from '../../types'

export function DetailPanel() {
  const selectedNodeId = useStore((s) => s.selectedNodeId)
  const nodesById = useStore((s) => s.tree.nodesById)
  const selectNode = useStore((s) => s.selectNode)

  const node = selectedNodeId ? nodesById[selectedNodeId] : null

  if (!node) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-3 text-text-muted px-6">
        <div className="w-10 h-10 rounded-lg bg-elevated flex items-center justify-center">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none" className="opacity-40">
            <rect x="2" y="4" width="16" height="12" rx="2" stroke="currentColor" strokeWidth="1.5" />
            <path d="M5 8h10M5 12h6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        </div>
        <p className="text-xs text-center">Click a node in the trace to view details</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Panel header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border shrink-0">
        <span className="text-xs font-semibold text-text-secondary uppercase tracking-wider">
          Node Detail
        </span>
        <button
          onClick={() => selectNode(null)}
          className="p-1 rounded text-text-muted hover:text-text-secondary hover:bg-elevated transition-colors"
        >
          <X size={13} />
        </button>
      </div>

      {/* Panel content */}
      <div className="flex-1 overflow-y-auto scrollbar-thin p-4 space-y-4">
        {node.type === 'llm' && <LLMDetail node={node} />}

        {(node.type === 'tool' || node.type === 'agent') && <ToolDetail node={node} />}

        {node.type === 'invocation' && (
          <div className="space-y-3">
            <div className="flex items-center gap-2 flex-wrap">
              <Badge variant="amber" size="xs">CYCLE</Badge>
              {!!node.data.agent_name && (
                <span className="text-sm font-medium text-text-primary font-mono">
                  {String(node.data.agent_name)}
                </span>
              )}
            </div>
            <div className="grid grid-cols-2 gap-1.5">
              {node.duration != null && (
                <div className="bg-base/60 rounded p-2 border border-border">
                  <div className="text-[10px] text-text-muted mb-0.5">Duration</div>
                  <div className="text-xs font-mono text-text-secondary">{formatDuration(node.duration)}</div>
                </div>
              )}
              {!!node.data.stop_reason && (
                <div className="bg-base/60 rounded p-2 border border-border">
                  <div className="text-[10px] text-text-muted mb-0.5">Stop Reason</div>
                  <div className="text-xs font-mono text-text-secondary">{String(node.data.stop_reason)}</div>
                </div>
              )}
            </div>
            {!!node.data.metrics && (
              <>
                <MetricsGrid metrics={node.data.metrics as InvocationMetrics} />
                {(node.data.metrics as InvocationMetrics).tools && (
                  <ToolSummaryTable tools={(node.data.metrics as InvocationMetrics).tools} />
                )}
              </>
            )}
          </div>
        )}

        {node.type === 'run' && (
          <div className="space-y-3">
            <div className="flex items-center gap-2 flex-wrap">
              <Badge variant={agentBadgeVariant(String(node.data.agent_type ?? ''))} size="xs">
                {String(node.data.agent_type ?? 'run')}
              </Badge>
              {node.status === 'success' && <Badge variant="green" size="xs">success</Badge>}
              {node.status === 'error' && <Badge variant="red" size="xs">failed</Badge>}
              {node.status === 'running' && <Badge variant="amber" size="xs">running</Badge>}
            </div>
            <div className="grid grid-cols-2 gap-1.5">
              {node.duration != null && (
                <div className="bg-base/60 rounded p-2 border border-border">
                  <div className="text-[10px] text-text-muted mb-0.5">Duration</div>
                  <div className="text-xs font-mono text-text-secondary">{formatDuration(node.duration)}</div>
                </div>
              )}
            </div>
            {!!node.data.error && (
              <div className="rounded border border-accent-red/30 bg-accent-red/10 p-2.5">
                <div className="text-xs text-accent-red font-mono">{String(node.data.error)}</div>
              </div>
            )}
          </div>
        )}

        {node.type === 'metrics' && node.data && (
          <div className="space-y-3">
            <Badge variant="amber" size="xs">METRICS</Badge>
            <MetricsGrid metrics={node.data as unknown as InvocationMetrics} />
            {(node.data as unknown as InvocationMetrics).tools && (
              <ToolSummaryTable tools={(node.data as unknown as InvocationMetrics).tools} />
            )}
          </div>
        )}
      </div>
    </div>
  )
}
