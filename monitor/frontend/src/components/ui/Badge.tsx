import clsx from 'clsx'

interface BadgeProps {
  variant?: 'ticket' | 'code-fix' | 'default' | 'green' | 'red' | 'amber' | 'blue' | 'cyan' | 'purple'
  size?: 'sm' | 'xs'
  children: React.ReactNode
  className?: string
}

const variantClasses: Record<string, string> = {
  ticket: 'bg-accent-purple/20 text-accent-purple border-accent-purple/30',
  'code-fix': 'bg-accent-cyan/20 text-accent-cyan border-accent-cyan/30',
  default: 'bg-accent-blue/20 text-accent-blue border-accent-blue/30',
  green: 'bg-accent-green/20 text-accent-green border-accent-green/30',
  red: 'bg-accent-red/20 text-accent-red border-accent-red/30',
  amber: 'bg-accent-amber/20 text-accent-amber border-accent-amber/30',
  blue: 'bg-accent-blue/20 text-accent-blue border-accent-blue/30',
  cyan: 'bg-accent-cyan/20 text-accent-cyan border-accent-cyan/30',
  purple: 'bg-accent-purple/20 text-accent-purple border-accent-purple/30',
}

export function Badge({ variant = 'default', size = 'sm', children, className }: BadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center font-medium border rounded',
        size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-1.5 py-px text-[10px]',
        variantClasses[variant],
        className,
      )}
    >
      {children}
    </span>
  )
}
