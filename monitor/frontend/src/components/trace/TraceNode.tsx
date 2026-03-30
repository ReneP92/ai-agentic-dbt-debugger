import { ChevronRight, Check, X, Loader2 } from 'lucide-react'
import clsx from 'clsx'
import type { TreeNode } from '../../types'
import { formatDuration } from '../../lib/formatters'
import { useStore } from '../../store/useStore'

const TYPE_STYLES: Record<string, { dot: string; badge: string; label: string }> = {
  run: { dot: 'bg-accent-blue', badge: 'bg-accent-blue/20 text-accent-blue border-accent-blue/30', label: 'RUN' },
  invocation: { dot: 'bg-accent-amber', badge: 'bg-accent-amber/20 text-accent-amber border-accent-amber/30', label: 'CYCLE' },
  llm: { dot: 'bg-accent-cyan', badge: 'bg-accent-cyan/20 text-accent-cyan border-accent-cyan/30', label: 'LLM' },
  tool: { dot: 'bg-accent-green', badge: 'bg-accent-green/20 text-accent-green border-accent-green/30', label: 'TOOL' },
  agent: { dot: 'bg-accent-purple', badge: 'bg-accent-purple/20 text-accent-purple border-accent-purple/30', label: 'AGENT' },
  metrics: { dot: 'bg-accent-amber', badge: 'bg-accent-amber/20 text-accent-amber border-accent-amber/30', label: 'STATS' },
}

interface TraceNodeProps {
  nodeId: string
  depth: number
}

export function TraceNode({ nodeId, depth }: TraceNodeProps) {
  const node = useStore((s) => s.tree.nodesById[nodeId]) as TreeNode | undefined
  const selectedNodeId = useStore((s) => s.selectedNodeId)
  const toggleNodeExpand = useStore((s) => s.toggleNodeExpand)
  const selectNode = useStore((s) => s.selectNode)

  if (!node) return null

  const styles = TYPE_STYLES[node.type] ?? TYPE_STYLES.run
  const isSelected = node.id === selectedNodeId
  const hasChildren = node.childIds.length > 0
  const paddingLeft = 12 + Math.min(depth, 7) * 20

  return (
    <div>
      {/* Node row */}
      <div
        className={clsx(
          'flex items-center gap-2 py-1.5 pr-3 cursor-pointer rounded-sm transition-colors group select-none',
          isSelected ? 'bg-accent-blue/10' : 'hover:bg-elevated/50',
        )}
        style={{ paddingLeft }}
        onClick={() => {
          if (hasChildren) toggleNodeExpand(node.id)
          selectNode(isSelected ? null : node.id)
        }}
      >
        {/* Chevron */}
        <span className={clsx('transition-transform shrink-0', hasChildren ? 'opacity-50 group-hover:opacity-100' : 'opacity-0')}>
          <ChevronRight
            size={12}
            className={clsx('transition-transform', node.expanded && hasChildren ? 'rotate-90' : '')}
          />
        </span>

        {/* Type dot */}
        <span className={clsx('w-1.5 h-1.5 rounded-full shrink-0', styles.dot)} />

        {/* Type badge */}
        <span
          className={clsx(
            'text-[9px] font-semibold px-1 py-px rounded border shrink-0 uppercase tracking-wide',
            styles.badge,
          )}
        >
          {styles.label}
        </span>

        {/* Label */}
        <span className={clsx('text-xs flex-1 truncate', isSelected ? 'text-text-primary' : 'text-text-secondary')}>
          {node.name}
        </span>

        {/* Token count for LLM nodes */}
        {node.type === 'llm' && node.tokenText && (
          <span className="text-[10px] text-text-muted font-mono shrink-0">
            {node.tokenText.length}c
          </span>
        )}

        {/* Duration */}
        {node.duration != null && (
          <span className="text-[10px] text-text-muted font-mono shrink-0">
            {formatDuration(node.duration)}
          </span>
        )}

        {/* Status icon */}
        <span className="shrink-0">
          {node.status === 'success' && <Check size={11} className="text-accent-green" />}
          {node.status === 'error' && <X size={11} className="text-accent-red" />}
          {node.status === 'running' && (
            <Loader2 size={11} className="text-accent-amber animate-spin" />
          )}
        </span>
      </div>

      {/* Children */}
      {hasChildren && node.expanded && (
        <div>
          {node.childIds.map((childId) => (
            <TraceNode key={childId} nodeId={childId} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  )
}
