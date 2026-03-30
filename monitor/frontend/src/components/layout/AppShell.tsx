import { useState, useCallback, useRef } from 'react'
import { StatusBar } from './StatusBar'
import { RunsList } from '../runs/RunsList'
import { TracePanel } from '../trace/TracePanel'
import { DetailPanel } from '../detail/DetailPanel'

const MIN_DETAIL_WIDTH = 280
const MAX_DETAIL_WIDTH = 600
const DEFAULT_DETAIL_WIDTH = 380

export function AppShell() {
  const [detailWidth, setDetailWidth] = useState(DEFAULT_DETAIL_WIDTH)
  const dragging = useRef(false)
  const startX = useRef(0)
  const startWidth = useRef(DEFAULT_DETAIL_WIDTH)

  const onMouseDown = useCallback((e: React.MouseEvent) => {
    dragging.current = true
    startX.current = e.clientX
    startWidth.current = detailWidth
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'

    const onMove = (ev: MouseEvent) => {
      if (!dragging.current) return
      const delta = startX.current - ev.clientX
      const newWidth = Math.min(MAX_DETAIL_WIDTH, Math.max(MIN_DETAIL_WIDTH, startWidth.current + delta))
      setDetailWidth(newWidth)
    }

    const onUp = () => {
      dragging.current = false
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
      document.removeEventListener('mousemove', onMove)
      document.removeEventListener('mouseup', onUp)
    }

    document.addEventListener('mousemove', onMove)
    document.addEventListener('mouseup', onUp)
  }, [detailWidth])

  return (
    <div className="flex flex-col h-full bg-base">
      <StatusBar />

      <div className="flex flex-1 min-h-0">
        {/* Sidebar */}
        <RunsList />

        {/* Main trace area */}
        <div className="flex-1 min-w-0 flex flex-col border-r border-border">
          <TracePanel />
        </div>

        {/* Resize handle */}
        <div
          className="w-1 cursor-col-resize bg-border hover:bg-accent-blue/40 transition-colors shrink-0"
          onMouseDown={onMouseDown}
        />

        {/* Detail panel */}
        <div
          className="shrink-0 flex flex-col bg-panel overflow-hidden"
          style={{ width: detailWidth }}
        >
          <DetailPanel />
        </div>
      </div>
    </div>
  )
}
