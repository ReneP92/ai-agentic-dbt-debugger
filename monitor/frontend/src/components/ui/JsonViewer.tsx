import { CopyButton } from './CopyButton'
import { tryFormatJson } from '../../lib/formatters'

interface JsonViewerProps {
  value: string | unknown
  label?: string
  maxHeight?: string
}

export function JsonViewer({ value, label, maxHeight = '300px' }: JsonViewerProps) {
  const raw = typeof value === 'string' ? value : JSON.stringify(value, null, 2)
  const formatted = tryFormatJson(raw)

  return (
    <div className="rounded border border-border bg-base/60">
      {label && (
        <div className="flex items-center justify-between px-3 py-1.5 border-b border-border">
          <span className="text-xs font-medium text-text-muted uppercase tracking-wide">{label}</span>
          <CopyButton text={formatted} />
        </div>
      )}
      {!label && (
        <div className="absolute top-2 right-2">
          <CopyButton text={formatted} />
        </div>
      )}
      <div
        className="overflow-auto scrollbar-thin"
        style={{ maxHeight }}
      >
        <pre className="p-3 text-xs font-mono text-text-secondary whitespace-pre-wrap break-words leading-relaxed">
          {formatted}
        </pre>
      </div>
    </div>
  )
}
