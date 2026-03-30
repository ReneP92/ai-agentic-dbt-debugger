export type ConnectionStatus = 'connected' | 'connecting' | 'disconnected'

export type NodeStatus = 'running' | 'success' | 'error' | null

export type NodeType = 'run' | 'invocation' | 'llm' | 'tool' | 'agent' | 'metrics'

export interface RunInfo {
  run_id: string
  agent_type: string
  started_at: string
  ended_at: string | null
  success: number | null
  total_input_tokens: number
  total_output_tokens: number
  total_duration_s: number | null
  estimated_cost_usd: number | null
}

export interface TreeNode {
  id: string
  type: NodeType
  name: string
  startTime: string | null
  endTime: string | null
  duration: number | null
  status: NodeStatus
  data: Record<string, unknown>
  childIds: string[]
  parentId: string | null
  expanded: boolean
  tokenText: string
  reasoningText: string
  toolUseId: string | null
}

export interface ReasoningBlock {
  id: string
  invocationIdx: number
  text: string
  timestamp: string
}

export interface MonitorEvent {
  type: string
  run_id: string
  agent: string
  timestamp: string
  data: Record<string, unknown>
}

export interface ToolMetrics {
  call_count: number
  success_count: number
  error_count: number
  total_time_s: number
}

export interface InvocationMetrics {
  input_tokens: number
  output_tokens: number
  total_tokens: number
  cache_read_tokens: number
  cache_write_tokens: number
  latency_ms: number
  cycle_count: number
  estimated_cost_usd: number
  tools: Record<string, ToolMetrics>
}
