import { useState } from 'react'
import { cx } from '@/lib/cx'
import { Button } from './Button'

interface CopyFieldProps {
  label: string
  value: string
  mono?: boolean
  secret?: boolean
}

export function CopyField({ label, value, mono = true, secret = false }: CopyFieldProps) {
  const [copied, setCopied] = useState(false)
  const [revealed, setRevealed] = useState(!secret)

  const copy = async () => {
    await navigator.clipboard.writeText(value)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <div>
      <div className="text-muted text-sm mb-1.5">{label}</div>
      <div className="flex items-center gap-2">
        <code
          className={cx(
            'flex-1 min-w-0 truncate rounded-field border border-line bg-surface-alt px-3 py-2',
            mono && 'font-mono text-sm',
          )}
        >
          {revealed ? value : '•'.repeat(Math.min(value.length, 24))}
        </code>
        {secret && (
          <Button variant="ghost" onClick={() => setRevealed((v) => !v)}>
            {revealed ? 'Hide' : 'Show'}
          </Button>
        )}
        <Button variant="tinted" onClick={copy}>
          {copied ? 'Copied' : 'Copy'}
        </Button>
      </div>
    </div>
  )
}
