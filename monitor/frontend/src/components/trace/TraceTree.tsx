import { useEffect, useRef } from 'react'
import { ChevronsDownUp, ChevronsUpDown } from 'lucide-react'
import { useStore } from '../../store/useStore'
import { TraceNode } from './TraceNode'

export function TraceTree() {
  const treeRoots = useStore((s) => s.tree.treeRoots)
  const nodesById = useStore((s) => s.tree.nodesById)
  const autoScroll = useStore((s) => s.autoScroll)
  const bottomRef = useRef<HTMLDivElement>(null)
  const prevRootsLen = useRef(0)

  // Auto-scroll when new nodes appear
  useEffect(() => {
    if (autoScroll && treeRoots.length > prevRootsLen.current) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
    prevRootsLen.current = treeRoots.length
  }, [treeRoots.length, autoScroll])

  function expandAll() {
    Object.values(nodesById).forEach((node) => {
      if (!node.expanded) {
        useStore.getState().toggleNodeExpand(node.id)
      }
    })
  }

  function collapseAll() {
    Object.values(nodesById).forEach((node) => {
      if (node.expanded && node.childIds.length > 0) {
        useStore.getState().toggleNodeExpand(node.id)
      }
    })
  }

  if (treeRoots.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-3 text-text-muted">
        <div className="w-12 h-12 rounded-xl bg-elevated flex items-center justify-center">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="opacity-40">
            <rect x="3" y="5" width="18" height="14" rx="2" stroke="currentColor" strokeWidth="1.5" />
            <path d="M7 10h10M7 14h6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        </div>
        <div className="text-center">
          <p className="text-sm text-text-muted">Select a run to view its trace</p>
          <p className="text-xs text-text-muted/60 mt-1">Or start an agent run to see live events</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center gap-1 px-3 py-1.5 border-b border-border shrink-0">
        <button
          onClick={expandAll}
          className="flex items-center gap-1 text-[10px] text-text-muted hover:text-text-secondary px-1.5 py-1 rounded hover:bg-elevated transition-colors"
          title="Expand all"
        >
          <ChevronsUpDown size={11} />
          Expand all
        </button>
        <button
          onClick={collapseAll}
          className="flex items-center gap-1 text-[10px] text-text-muted hover:text-text-secondary px-1.5 py-1 rounded hover:bg-elevated transition-colors"
          title="Collapse all"
        >
          <ChevronsDownUp size={11} />
          Collapse all
        </button>
      </div>

      {/* Tree */}
      <div className="flex-1 overflow-y-auto scrollbar-thin py-1">
        {treeRoots.map((id) => (
          <TraceNode key={id} nodeId={id} depth={0} />
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
