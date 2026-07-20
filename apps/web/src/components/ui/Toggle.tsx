import { cx } from '@/lib/cx'

interface ToggleProps {
  checked: boolean
  onChange: (next: boolean) => void
  label: string
  hint?: string
  disabled?: boolean
}

export function Toggle({ checked, onChange, label, hint, disabled }: ToggleProps) {
  return (
    <label className="flex items-start justify-between gap-4 border-b border-line py-3 last:border-0">
      <span>
        <span className="block font-medium">{label}</span>
        {hint && <span className="block text-subtle text-xs">{hint}</span>}
      </span>

      <button
        type="button"
        role="switch"
        aria-checked={checked}
        aria-label={label}
        disabled={disabled}
        onClick={() => onChange(!checked)}
        className={cx(
          'relative h-6 w-11 shrink-0 rounded-pill transition-colors',
          checked ? 'bg-brand' : 'bg-line-strong',
          disabled && 'opacity-50',
        )}
      >
        <span
          className={cx(
            'absolute top-0.5 h-5 w-5 rounded-pill bg-surface transition-all',
            checked ? 'left-[22px]' : 'left-0.5',
          )}
        />
      </button>
    </label>
  )
}
