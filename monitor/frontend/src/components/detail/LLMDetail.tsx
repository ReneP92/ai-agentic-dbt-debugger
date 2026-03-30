import { CopyButton } from '../ui/CopyButton'
import { Badge } from '../ui/Badge'
import type { TreeNode } from '../../types'
import { formatDuration } from '../../lib/formatters'

interface LLMDetailProps {
  node: TreeNode
}

export function LLMDetail({ node }: LLMDetailProps) {
  const stopReason = node.data.stop_reason as string | undefined
  const error = node.data.error as string | undefined

  return (
    <div className="space-y-3">
      {/* Header row */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <Badge variant="cyan" size="xs">LLM</Badge>
          {stopReason && (
            <Badge variant="default" size="xs">{stopReason}</Badge>
          )}
          {error && <Badge variant="red" size="xs">error</Badge>}
        </div>
        {node.duration != null && (
          <span className="text-xs text-text-muted font-mono">{formatDuration(node.duration)}</span>
        )}
      </div>

      {error && (
        <div className="rounded border border-accent-red/30 bg-accent-red/10 p-2.5">
          <div className="text-xs text-accent-red font-mono">{error}</div>
        </div>
      )}

      {/* Reasoning */}
      {node.reasoningText && (
        <div className="rounded border border-accent-purple/20 bg-accent-purple/5">
          <div className="flex items-center justify-between px-3 py-1.5 border-b border-accent-purple/20">
            <span className="text-[10px] font-semibold text-accent-purple uppercase tracking-wider">
              Thinking
            </span>
            <CopyButton text={node.reasoningText} />
          </div>
          <div className="p-3 max-h-64 overflow-y-auto scrollbar-thin">
            <p className="text-xs font-mono text-text-secondary/80 italic whitespace-pre-wrap leading-relaxed">
              {node.reasoningText}
              {node.status === 'running' && (
                <span className="inline-block w-0.5 h-3 bg-accent-purple ml-0.5 animate-blink-cursor" />
              )}
            </p>
          </div>
        </div>
      )}

      {/* Response */}
      {node.tokenText && (
        <div className="rounded border border-border bg-base/60">
          <div className="flex items-center justify-between px-3 py-1.5 border-b border-border">
            <span className="text-[10px] font-semibold text-text-muted uppercase tracking-wider">
              Response
            </span>
            <CopyButton text={node.tokenText} />
          </div>
          <div className="p-3 max-h-64 overflow-y-auto scrollbar-thin">
            <p className="text-xs font-mono text-text-primary whitespace-pre-wrap leading-relaxed">
              {node.tokenText}
              {node.status === 'running' && (
                <span className="inline-block w-0.5 h-3 bg-accent-blue ml-0.5 animate-blink-cursor" />
              )}
            </p>
          </div>
        </div>
      )}

      {!node.tokenText && !node.reasoningText && (
        <div className="text-xs text-text-muted py-2">
          {node.status === 'running' ? 'Waiting for response...' : 'No response captured.'}
        </div>
      )}
    </div>
  )
}
