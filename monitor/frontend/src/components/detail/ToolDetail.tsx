import { JsonViewer } from '../ui/JsonViewer'
import { Badge } from '../ui/Badge'
import type { TreeNode } from '../../types'
import { formatDuration } from '../../lib/formatters'

interface ToolDetailProps {
  node: TreeNode
}

export function ToolDetail({ node }: ToolDetailProps) {
  const toolName = (node.data.tool_name as string) ?? node.name
  const input = node.data.input as string | undefined
  const result = node.data.result as string | undefined
  const error = node.data.error as string | undefined
  const isAgent = node.type === 'agent'

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <Badge variant={isAgent ? 'purple' : 'green'} size="xs">
            {isAgent ? 'AGENT' : 'TOOL'}
          </Badge>
          <span className="text-sm font-medium text-text-primary font-mono">{toolName}</span>
        </div>
        <div className="flex items-center gap-2">
          {node.duration != null && (
            <span className="text-xs text-text-muted font-mono">{formatDuration(node.duration)}</span>
          )}
          {node.status === 'error' && <Badge variant="red" size="xs">error</Badge>}
          {node.status === 'success' && <Badge variant="green" size="xs">success</Badge>}
        </div>
      </div>

      {error && (
        <div className="rounded border border-accent-red/30 bg-accent-red/10 p-2.5">
          <div className="text-[10px] font-semibold text-accent-red uppercase tracking-wider mb-1">Error</div>
          <div className="text-xs text-accent-red font-mono">{error}</div>
        </div>
      )}

      {input && (
        <JsonViewer value={input} label="Input" maxHeight="200px" />
      )}

      {result && (
        <JsonViewer value={result} label="Output" maxHeight="200px" />
      )}

      {!input && !result && (
        <div className="text-xs text-text-muted py-2">
          {node.status === 'running' ? 'Tool is running...' : 'No input/output captured.'}
        </div>
      )}
    </div>
  )
}
