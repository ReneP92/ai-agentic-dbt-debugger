import { useState } from 'react'
import { ChevronDown, Brain } from 'lucide-react'
import clsx from 'clsx'
import { useStore } from '../../store/useStore'
import { CopyButton } from '../ui/CopyButton'
import type { ReasoningBlock } from '../../types'

export function ThinkingViewer() {
  const reasoningBlocks = useStore((s) => s.tree.reasoningBlocks) as ReasoningBlock[]
  const [open, setOpen] = useState(true)

  const totalText = reasoningBlocks.map((b) => b.text).join('\n\n---\n\n')

  if (reasoningBlocks.length === 0) return null

  return (
    <div
      className={clsx(
        'border-t border-border shrink-0 bg-panel transition-all',
        open ? 'h-48' : 'h-8',
      )}
    >
      {/* Toggle header */}
      <button
        className="w-full flex items-center justify-between px-3 h-8 hover:bg-elevated/50 transition-colors"
        onClick={() => setOpen((v) => !v)}
      >
        <div className="flex items-center gap-2">
          <Brain size={12} className="text-accent-purple" />
          <span className="text-[11px] font-semibold text-text-secondary">
            Thinking
          </span>
          <span className="text-[10px] text-text-muted bg-elevated px-1.5 py-px rounded">
            {reasoningBlocks.length} block{reasoningBlocks.length !== 1 ? 's' : ''}
          </span>
        </div>
        <div className="flex items-center gap-2">
          {open && <CopyButton text={totalText} />}
          <ChevronDown
            size={12}
            className={clsx('text-text-muted transition-transform', !open && '-rotate-90')}
          />
        </div>
      </button>

      {/* Content */}
      {open && (
        <div className="overflow-y-auto scrollbar-thin h-[calc(100%-2rem)] px-3 py-2 space-y-2">
          {reasoningBlocks.map((block) => (
            <div key={block.id} className="flex gap-2">
              <div className="shrink-0 mt-1">
                <div className="w-1 h-full min-h-[20px] rounded-full bg-accent-purple/40" />
              </div>
              <div>
                <div className="text-[9px] text-text-muted mb-0.5">
                  Cycle {block.invocationIdx}
                </div>
                <p className="text-[11px] font-mono text-text-secondary/80 italic leading-relaxed whitespace-pre-wrap">
                  {block.text}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
