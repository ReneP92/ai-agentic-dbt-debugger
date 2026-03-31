import clsx from 'clsx'
import { Database, Trash2 } from 'lucide-react'
import { useStore } from '../../store/useStore'
import type { ConnectionStatus } from '../../types'

const statusConfig: Record<ConnectionStatus, { label: string; dot: string; text: string }> = {
  connected: { label: 'live', dot: 'bg-accent-green animate-pulse', text: 'text-accent-green' },
  connecting: { label: 'connecting', dot: 'bg-accent-amber animate-pulse', text: 'text-accent-amber' },
  disconnected: { label: 'disconnected', dot: 'bg-accent-red', text: 'text-accent-red' },
}

export function StatusBar() {
  const status = useStore((s) => s.connectionStatus)
  const clearAll = useStore((s) => s.clearAll)
  const { label, dot, text } = statusConfig[status]

  return (
    <header className="h-12 flex items-center justify-between px-4 border-b border-border bg-panel shrink-0">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <img src="/corgi.png" alt="logo" className="w-7 h-7 rounded-md object-cover" />
          <span className="font-semibold text-sm text-text-primary tracking-tight">
            dbt Agent Monitor
          </span>
        </div>

        <div className={clsx('flex items-center gap-1.5 text-xs font-medium', text)}>
          <span className={clsx('w-1.5 h-1.5 rounded-full', dot)} />
          {label}
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 text-text-muted">
          <Database size={13} />
          <span className="text-xs">SQLite</span>
        </div>
        <button
          onClick={clearAll}
          className="flex items-center gap-1.5 px-2.5 py-1 rounded text-xs text-text-muted border border-border hover:border-accent-red/50 hover:text-accent-red hover:bg-accent-red/10 transition-colors"
          title="Clear all runs from view"
        >
          <Trash2 size={12} />
          Clear
        </button>
      </div>
    </header>
  )
}
