import { useMemo } from 'react'
import { useStore } from '../../store/useStore'
import type { TreeNode } from '../../types'
import { formatDuration } from '../../lib/formatters'

const TYPE_COLORS: Record<string, string> = {
  run: '#3b82f6',
  invocation: '#f59e0b',
  llm: '#06b6d4',
  tool: '#10b981',
  agent: '#8b5cf6',
  metrics: '#f59e0b',
}

interface FlatNode {
  node: TreeNode
  depth: number
}

function flattenTree(nodesById: Record<string, TreeNode>, roots: string[]): FlatNode[] {
  const result: FlatNode[] = []

  function walk(nodeId: string, depth: number) {
    const node = nodesById[nodeId]
    if (!node) return
    result.push({ node, depth })
    if (node.expanded) {
      for (const childId of node.childIds) {
        walk(childId, depth + 1)
      }
    }
  }

  for (const id of roots) walk(id, 0)
  return result
}

export function TimelineView() {
  const treeRoots = useStore((s) => s.tree.treeRoots)
  const nodesById = useStore((s) => s.tree.nodesById)
  const selectedNodeId = useStore((s) => s.selectedNodeId)
  const selectNode = useStore((s) => s.selectNode)

  const flatNodes = useMemo(() => flattenTree(nodesById, treeRoots), [nodesById, treeRoots])

  const { minTime, maxTime } = useMemo(() => {
    let min = Infinity
    let max = -Infinity
    for (const { node } of flatNodes) {
      if (node.startTime) min = Math.min(min, new Date(node.startTime).getTime())
      if (node.endTime) max = Math.max(max, new Date(node.endTime).getTime())
    }
    return { minTime: min === Infinity ? 0 : min, maxTime: max === -Infinity ? Date.now() : max }
  }, [flatNodes])

  const totalDuration = Math.max(maxTime - minTime, 1)

  if (flatNodes.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-text-muted text-sm">
        No trace data
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full overflow-auto scrollbar-thin p-3 gap-1">
      {flatNodes.map(({ node, depth }) => {
        const start = node.startTime ? new Date(node.startTime).getTime() : minTime
        const end = node.endTime ? new Date(node.endTime).getTime() : Date.now()
        const left = ((start - minTime) / totalDuration) * 100
        const width = Math.max(((end - start) / totalDuration) * 100, 0.5)
        const color = TYPE_COLORS[node.type] ?? '#3b82f6'
        const isSelected = node.id === selectedNodeId

        return (
          <div
            key={node.id}
            className="flex items-center gap-2 h-7 group cursor-pointer"
            onClick={() => selectNode(isSelected ? null : node.id)}
          >
            {/* Label */}
            <div
              className="shrink-0 text-[10px] text-text-muted truncate text-right"
              style={{ width: 140, paddingLeft: Math.min(depth, 5) * 10 }}
              title={node.name}
            >
              <span style={{ color }}>{node.name}</span>
            </div>

            {/* Bar track */}
            <div className="flex-1 relative h-5 bg-elevated rounded overflow-hidden">
              <div
                className={`absolute top-0 h-full rounded transition-opacity ${isSelected ? 'opacity-100' : 'opacity-70 group-hover:opacity-100'}`}
                style={{
                  left: `${left}%`,
                  width: `${width}%`,
                  backgroundColor: color,
                  minWidth: 3,
                }}
              >
                {width > 8 && (
                  <span className="absolute inset-0 flex items-center px-1.5 text-[9px] text-white/90 font-mono overflow-hidden">
                    {node.duration != null ? formatDuration(node.duration) : '...'}
                  </span>
                )}
              </div>
            </div>

            {/* Duration */}
            <div className="shrink-0 w-14 text-[10px] text-text-muted font-mono text-right">
              {node.duration != null ? formatDuration(node.duration) : (node.status === 'running' ? '...' : '')}
            </div>
          </div>
        )
      })}
    </div>
  )
}
