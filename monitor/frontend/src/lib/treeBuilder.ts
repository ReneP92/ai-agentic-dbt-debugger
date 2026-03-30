import type { TreeNode, NodeType, MonitorEvent, ReasoningBlock } from '../types'

export interface TreeState {
  nodesById: Record<string, TreeNode>
  treeRoots: string[]
  nodeStack: string[]
  nextId: number
  reasoningBlocks: ReasoningBlock[]
  invocationCount: number
}

export function createEmptyTreeState(): TreeState {
  return {
    nodesById: {},
    treeRoots: [],
    nodeStack: [],
    nextId: 0,
    reasoningBlocks: [],
    invocationCount: 0,
  }
}

function createNode(
  state: TreeState,
  type: NodeType,
  name: string,
  event: MonitorEvent,
): TreeNode {
  const id = `n${state.nextId++}`
  const node: TreeNode = {
    id,
    type,
    name,
    startTime: event.timestamp ?? null,
    endTime: null,
    duration: null,
    status: 'running',
    data: event.data ?? {},
    childIds: [],
    parentId: null,
    expanded: true,
    tokenText: '',
    reasoningText: '',
    toolUseId: (event.data?.tool_use_id as string) ?? null,
  }
  state.nodesById[id] = node
  return node
}

function calcDuration(node: TreeNode): number | null {
  if (!node.startTime || !node.endTime) return null
  return Math.max(0, (new Date(node.endTime).getTime() - new Date(node.startTime).getTime()) / 1000)
}

function currentParentId(state: TreeState): string | null {
  return state.nodeStack.length > 0 ? state.nodeStack[state.nodeStack.length - 1] : null
}

function attachToParent(state: TreeState, node: TreeNode): void {
  const parentId = currentParentId(state)
  if (parentId) {
    node.parentId = parentId
    const parent = state.nodesById[parentId]
    if (parent) parent.childIds.push(node.id)
  } else {
    state.treeRoots.push(node.id)
  }
}

function popStack(state: TreeState, type: NodeType): TreeNode | null {
  for (let i = state.nodeStack.length - 1; i >= 0; i--) {
    const node = state.nodesById[state.nodeStack[i]]
    if (node?.type === type) {
      state.nodeStack.splice(i, 1)
      return node
    }
  }
  return null
}

function popStackByToolId(state: TreeState, toolUseId: string | null, type: NodeType): TreeNode | null {
  if (toolUseId) {
    for (let i = state.nodeStack.length - 1; i >= 0; i--) {
      const node = state.nodesById[state.nodeStack[i]]
      if (node?.toolUseId === toolUseId) {
        state.nodeStack.splice(i, 1)
        return node
      }
    }
  }
  return popStack(state, type)
}

function findNearestOnStack(state: TreeState, type: NodeType): TreeNode | null {
  for (let i = state.nodeStack.length - 1; i >= 0; i--) {
    const node = state.nodesById[state.nodeStack[i]]
    if (node?.type === type) return node
  }
  return null
}

export function applyEvent(state: TreeState, event: MonitorEvent): void {
  const data = event.data ?? {}

  switch (event.type) {
    case 'run_start': {
      const node = createNode(state, 'run', `Run: ${(data.agent_type as string) ?? event.agent ?? 'agent'}`, event)
      state.treeRoots.push(node.id)
      state.nodeStack.push(node.id)
      break
    }

    case 'run_end': {
      const node = popStack(state, 'run')
      if (node) {
        node.endTime = event.timestamp
        node.duration = (data.duration_s as number) ?? calcDuration(node)
        node.status = (data.success as boolean) ? 'success' : 'error'
        node.data = { ...node.data, ...data }
      }
      break
    }

    case 'invocation_start': {
      state.invocationCount++
      const node = createNode(state, 'invocation', `Invocation: ${(data.agent_name as string) ?? event.agent ?? 'agent'}`, event)
      attachToParent(state, node)
      state.nodeStack.push(node.id)
      break
    }

    case 'invocation_end': {
      const node = popStack(state, 'invocation')
      if (node) {
        node.endTime = event.timestamp
        node.duration = calcDuration(node)
        node.status = 'success'
        node.data = { ...node.data, ...data }
      }
      break
    }

    case 'model_call_start': {
      const node = createNode(state, 'llm', 'LLM Call', event)
      attachToParent(state, node)
      state.nodeStack.push(node.id)
      break
    }

    case 'model_call_end': {
      const node = popStack(state, 'llm')
      if (node) {
        node.endTime = event.timestamp
        node.duration = calcDuration(node)
        node.status = (data.error as string) ? 'error' : 'success'
        node.data = { ...node.data, ...data }
        if (node.data.stop_reason) {
          node.name = `LLM Call (${node.data.stop_reason as string})`
        }
      }
      break
    }

    case 'tool_start': {
      const toolName = (data.tool_name as string) ?? 'unknown'
      const node = createNode(state, 'tool', `Tool: ${toolName}`, event)
      node.toolUseId = (data.tool_use_id as string) ?? null
      attachToParent(state, node)
      state.nodeStack.push(node.id)
      break
    }

    case 'tool_end': {
      const node = popStackByToolId(state, (data.tool_use_id as string) ?? null, 'tool')
      if (node) {
        node.endTime = event.timestamp
        node.duration = (data.duration_s as number) ?? calcDuration(node)
        node.status = data.status === 'error' ? 'error' : 'success'
        node.data = { ...node.data, ...data }
      }
      break
    }

    case 'sub_agent_start': {
      const agentName = (data.sub_agent_name as string) ?? 'unknown'
      const node = createNode(state, 'agent', `Agent: ${agentName}`, event)
      node.toolUseId = (data.tool_use_id as string) ?? null
      attachToParent(state, node)
      state.nodeStack.push(node.id)
      break
    }

    case 'sub_agent_end': {
      const node = popStackByToolId(state, (data.tool_use_id as string) ?? null, 'agent')
      if (node) {
        node.endTime = event.timestamp
        node.duration = (data.duration_s as number) ?? calcDuration(node)
        node.status = data.status === 'error' ? 'error' : 'success'
        node.data = { ...node.data, ...data }
      }
      break
    }

    case 'token': {
      const llmNode = findNearestOnStack(state, 'llm')
      if (llmNode) {
        llmNode.tokenText += (data.text as string) ?? ''
      }
      break
    }

    case 'reasoning': {
      const llmNode = findNearestOnStack(state, 'llm')
      const text = (data.text as string) ?? ''
      if (llmNode) {
        llmNode.reasoningText += text
      }
      state.reasoningBlocks.push({
        id: `rb_${state.reasoningBlocks.length}`,
        invocationIdx: state.invocationCount,
        text,
        timestamp: event.timestamp,
      })
      break
    }

    case 'metrics': {
      const node = createNode(state, 'metrics', 'Final Metrics', event)
      attachToParent(state, node)
      node.status = null
      break
    }
  }
}

export function buildTreeFromEvents(events: MonitorEvent[]): TreeState {
  const state = createEmptyTreeState()
  for (const event of events) {
    applyEvent(state, event)
  }
  return state
}
