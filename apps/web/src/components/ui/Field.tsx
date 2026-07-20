import type { InputHTMLAttributes } from 'react'
import { cx } from '@/lib/cx'

interface FieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string
  hint?: string
  mono?: boolean
}

export function Field({ label, hint, mono, className, ...props }: FieldProps) {
  return (
    <label className="grid gap-1.5">
      <span className="text-muted">{label}</span>
      <input
        className={cx(
          'h-10 rounded-field border border-line px-3',
          'focus:border-brand disabled:bg-surface-alt disabled:text-muted',
          mono && 'font-mono text-sm',
          className,
        )}
        {...props}
      />
      {hint && <span className="text-subtle text-xs">{hint}</span>}
    </label>
  )
}
