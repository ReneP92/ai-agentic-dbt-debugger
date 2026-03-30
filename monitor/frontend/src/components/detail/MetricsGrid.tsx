import type { InvocationMetrics } from '../../types'
import { formatTokens, formatCost, formatDuration, formatNumber } from '../../lib/formatters'

interface MetricsGridProps {
  metrics: InvocationMetrics
}

export function MetricsGrid({ metrics }: MetricsGridProps) {
  const items = [
    { label: 'Input Tokens', value: formatTokens(metrics.input_tokens), color: 'text-accent-blue' },
    { label: 'Output Tokens', value: formatTokens(metrics.output_tokens), color: 'text-accent-cyan' },
    { label: 'Cache Read', value: formatTokens(metrics.cache_read_tokens), color: 'text-accent-purple' },
    { label: 'Cache Write', value: formatTokens(metrics.cache_write_tokens), color: 'text-text-secondary' },
    { label: 'Latency', value: formatDuration(metrics.latency_ms != null ? metrics.latency_ms / 1000 : null), color: 'text-text-secondary' },
    { label: 'Cost', value: formatCost(metrics.estimated_cost_usd), color: 'text-accent-amber' },
    { label: 'Cycles', value: formatNumber(metrics.cycle_count), color: 'text-text-secondary' },
    { label: 'Total Tokens', value: formatTokens(metrics.total_tokens), color: 'text-text-secondary' },
  ]

  return (
    <div className="grid grid-cols-2 gap-1.5">
      {items.map(({ label, value, color }) => (
        <div key={label} className="bg-base/60 rounded p-2 border border-border">
          <div className="text-[10px] text-text-muted mb-0.5">{label}</div>
          <div className={`text-xs font-mono font-medium ${color}`}>{value}</div>
        </div>
      ))}
    </div>
  )
}

interface ToolSummaryTableProps {
  tools: InvocationMetrics['tools']
}

export function ToolSummaryTable({ tools }: ToolSummaryTableProps) {
  const entries = Object.entries(tools)
  if (entries.length === 0) return null

  return (
    <div className="mt-3">
      <div className="text-[10px] font-semibold text-text-muted uppercase tracking-wider mb-1.5">
        Tool Usage
      </div>
      <div className="rounded border border-border overflow-hidden">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-border bg-elevated/50">
              <th className="text-left px-2.5 py-1.5 text-text-muted font-medium">Tool</th>
              <th className="text-right px-2.5 py-1.5 text-text-muted font-medium">Calls</th>
              <th className="text-right px-2.5 py-1.5 text-text-muted font-medium">Errors</th>
              <th className="text-right px-2.5 py-1.5 text-text-muted font-medium">Avg Time</th>
            </tr>
          </thead>
          <tbody>
            {entries.map(([tool, m]) => (
              <tr key={tool} className="border-b border-border-subtle last:border-0">
                <td className="px-2.5 py-1.5 font-mono text-text-primary">{tool}</td>
                <td className="px-2.5 py-1.5 text-right text-text-secondary">{m.call_count}</td>
                <td className={`px-2.5 py-1.5 text-right ${m.error_count > 0 ? 'text-accent-red' : 'text-text-muted'}`}>
                  {m.error_count}
                </td>
                <td className="px-2.5 py-1.5 text-right text-text-secondary font-mono">
                  {m.call_count > 0 ? formatDuration(m.total_time_s / m.call_count) : '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
