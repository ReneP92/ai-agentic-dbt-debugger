export function formatRelativeTime(iso: string | null | undefined): string {
  if (!iso) return ''
  const diffS = Math.floor((Date.now() - new Date(iso).getTime()) / 1000)
  if (diffS < 5) return 'just now'
  if (diffS < 60) return `${diffS}s ago`
  const diffM = Math.floor(diffS / 60)
  if (diffM < 60) return `${diffM}m ago`
  const diffH = Math.floor(diffM / 60)
  if (diffH < 24) return `${diffH}h ago`
  return new Date(iso).toLocaleTimeString('en-US', { hour12: false })
}

export function formatDuration(seconds: number | null | undefined): string {
  if (seconds == null) return '-'
  if (seconds < 0.1) return '<0.1s'
  if (seconds < 60) return `${seconds.toFixed(1)}s`
  const m = Math.floor(seconds / 60)
  const s = Math.round(seconds % 60)
  return `${m}m ${s}s`
}

export function formatNumber(n: number | null | undefined): string {
  if (n == null || n === 0) return '-'
  return Number(n).toLocaleString('en-US')
}

export function formatCost(usd: number | null | undefined): string {
  if (usd == null) return '-'
  if (usd < 0.0001) return '<$0.0001'
  return `$${usd.toFixed(4)}`
}

export function formatTokens(n: number | null | undefined): string {
  if (n == null || n === 0) return '-'
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`
  return String(n)
}

export function formatTime(iso: string | null | undefined): string {
  if (!iso) return ''
  return new Date(iso).toLocaleTimeString('en-US', { hour12: false })
}

export function agentBadgeVariant(agentType: string): 'ticket' | 'code-fix' | 'default' {
  const t = (agentType || '').toLowerCase()
  if (t.includes('ticket')) return 'ticket'
  if (t.includes('code') || t.includes('fix')) return 'code-fix'
  return 'default'
}

export function tryFormatJson(str: string): string {
  try {
    return JSON.stringify(JSON.parse(str), null, 2)
  } catch {
    return str
  }
}
