import clsx from 'clsx'
import { Activity, Database } from 'lucide-react'
import { useStore } from '../../store/useStore'
import type { ConnectionStatus } from '../../types'

const statusConfig: Record<ConnectionStatus, { label: string; dot: string; text: string }> = {
  connected: { label: 'live', dot: 'bg-accent-green animate-pulse', text: 'text-accent-green' },
  connecting: { label: 'connecting', dot: 'bg-accent-amber animate-pulse', text: 'text-accent-amber' },
  disconnected: { label: 'disconnected', dot: 'bg-accent-red', text: 'text-accent-red' },
}

export function StatusBar() {
  const status = useStore((s) => s.connectionStatus)
  const { label, dot, text } = statusConfig[status]

  return (
    <header className="h-12 flex items-center justify-between px-4 border-b border-border bg-panel shrink-0">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-md bg-accent-blue/20 flex items-center justify-center">
            <Activity size={14} className="text-accent-blue" />
          </div>
          <span className="font-semibold text-sm text-text-primary tracking-tight">
            dbt Agent Monitor
          </span>
        </div>

        <div className={clsx('flex items-center gap-1.5 text-xs font-medium', text)}>
          <span className={clsx('w-1.5 h-1.5 rounded-full', dot)} />
          {label}
        </div>
      </div>

      <div className="flex items-center gap-2 text-text-muted">
        <Database size={13} />
        <span className="text-xs">SQLite</span>
      </div>
    </header>
  )
}
