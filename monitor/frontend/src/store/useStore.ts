import { create } from 'zustand'
import { immer } from 'zustand/middleware/immer'
import type { RunInfo, TreeNode, ConnectionStatus, MonitorEvent } from '../types'
import { applyEvent, buildTreeFromEvents, createEmptyTreeState, type TreeState } from '../lib/treeBuilder'

interface State {
  connectionStatus: ConnectionStatus
  runs: Record<string, RunInfo>
  runOrder: string[]
  selectedRunId: string | null
  liveRunId: string | null
  tree: TreeState
  selectedNodeId: string | null
  autoScroll: boolean

  setConnectionStatus: (s: ConnectionStatus) => void
  handleLiveEvent: (event: MonitorEvent) => void
  loadHistoricalRun: (runId: string, events: MonitorEvent[]) => void
  selectRun: (runId: string | null) => void
  selectNode: (nodeId: string | null) => void
  toggleNodeExpand: (nodeId: string) => void
  setAutoScroll: (v: boolean) => void
  upsertRun: (run: RunInfo) => void
  prependRuns: (runs: RunInfo[]) => void
}

export const useStore = create<State>()(
  immer((set) => ({
    connectionStatus: 'disconnected',
    runs: {},
    runOrder: [],
    selectedRunId: null,
    liveRunId: null,
    tree: createEmptyTreeState(),
    selectedNodeId: null,
    autoScroll: true,

    setConnectionStatus: (s) =>
      set((state) => {
        state.connectionStatus = s
      }),

    upsertRun: (run) =>
      set((state) => {
        if (!state.runs[run.run_id]) {
          state.runOrder.unshift(run.run_id)
        }
        state.runs[run.run_id] = run
      }),

    prependRuns: (runs) =>
      set((state) => {
        for (const run of runs) {
          if (!state.runs[run.run_id]) {
            state.runOrder.push(run.run_id)
            state.runs[run.run_id] = run
          }
        }
      }),

    handleLiveEvent: (event) =>
      set((state) => {
        const runId = event.run_id

        if (event.type === 'run_start') {
          state.liveRunId = runId
          const newRun: RunInfo = {
            run_id: runId,
            agent_type: (event.data?.agent_type as string) ?? event.agent ?? 'unknown',
            started_at: event.timestamp,
            ended_at: null,
            success: null,
            total_input_tokens: 0,
            total_output_tokens: 0,
            total_duration_s: null,
            estimated_cost_usd: null,
          }
          if (!state.runs[runId]) {
            state.runOrder.unshift(runId)
          }
          state.runs[runId] = newRun
          // Auto-select this new live run
          state.selectedRunId = runId
          state.tree = createEmptyTreeState()
          state.selectedNodeId = null
        }

        if (event.type === 'run_end') {
          const run = state.runs[runId]
          if (run) {
            run.ended_at = event.timestamp
            run.success = (event.data?.success as boolean) ? 1 : 0
            run.total_duration_s = (event.data?.duration_s as number) ?? null
          }
          if (runId === state.liveRunId) {
            state.liveRunId = null
          }
        }

        if (event.type === 'invocation_end') {
          const run = state.runs[runId]
          const m = (event.data?.metrics ?? {}) as Record<string, unknown>
          if (run && m.input_tokens) {
            run.total_input_tokens = m.input_tokens as number
            run.total_output_tokens = (m.output_tokens as number) ?? 0
            run.estimated_cost_usd = (m.estimated_cost_usd as number) ?? null
          }
        }

        // Only process tree events for selected run
        if (runId === state.selectedRunId) {
          applyEvent(state.tree, event)
        }
      }),

    loadHistoricalRun: (runId, events) =>
      set((state) => {
        state.selectedRunId = runId
        state.tree = buildTreeFromEvents(events)
        state.selectedNodeId = null
      }),

    selectRun: (runId) =>
      set((state) => {
        state.selectedRunId = runId
        if (runId !== state.liveRunId) {
          state.tree = createEmptyTreeState()
        }
        state.selectedNodeId = null
      }),

    selectNode: (nodeId) =>
      set((state) => {
        state.selectedNodeId = nodeId
      }),

    toggleNodeExpand: (nodeId) =>
      set((state) => {
        const node = state.tree.nodesById[nodeId] as TreeNode | undefined
        if (node) {
          node.expanded = !node.expanded
        }
      }),

    setAutoScroll: (v) =>
      set((state) => {
        state.autoScroll = v
      }),
  })),
)
