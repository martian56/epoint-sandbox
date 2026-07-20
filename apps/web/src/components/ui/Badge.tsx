import { cx } from '@/lib/cx'
import type { CallbackStatus, TransactionStatus } from '@/lib/types'

type Tone = 'success' | 'danger' | 'warning' | 'neutral' | 'info'

const TONES: Record<Tone, string> = {
  success: 'bg-[#28a745] text-white',
  danger: 'bg-[#dc3545] text-white',
  warning: 'bg-[#ffc107] text-ink',
  neutral: 'bg-line text-body',
  info: 'bg-tint-200 text-brand-deep',
}

const STATUS_TONES: Record<TransactionStatus | CallbackStatus, Tone> = {
  new: 'info',
  success: 'success',
  failed: 'danger',
  error: 'danger',
  returned: 'warning',
  server_error: 'neutral',
  pending: 'info',
  delivered: 'success',
  dropped: 'neutral',
}

interface BadgeProps {
  tone?: Tone
  children: React.ReactNode
  className?: string
}

export function Badge({ tone = 'neutral', children, className }: BadgeProps) {
  return (
    <span
      className={cx(
        'inline-flex items-center rounded-pill px-2.5 py-1 text-xs font-bold',
        TONES[tone],
        className,
      )}
    >
      {children}
    </span>
  )
}

export function StatusBadge({ status }: { status: TransactionStatus | CallbackStatus }) {
  return <Badge tone={STATUS_TONES[status]}>{status.replace('_', ' ')}</Badge>
}
