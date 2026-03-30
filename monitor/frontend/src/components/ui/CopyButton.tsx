import { useState } from 'react'
import { Check, Copy } from 'lucide-react'
import clsx from 'clsx'

interface CopyButtonProps {
  text: string
  className?: string
}

export function CopyButton({ text, className }: CopyButtonProps) {
  const [copied, setCopied] = useState(false)

  async function handleCopy() {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <button
      onClick={handleCopy}
      className={clsx(
        'p-1 rounded transition-colors',
        copied
          ? 'text-accent-green'
          : 'text-text-muted hover:text-text-secondary hover:bg-elevated',
        className,
      )}
      title={copied ? 'Copied!' : 'Copy to clipboard'}
    >
      {copied ? <Check size={13} /> : <Copy size={13} />}
    </button>
  )
}
