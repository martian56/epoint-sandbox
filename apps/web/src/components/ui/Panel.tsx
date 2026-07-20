import type { ReactNode } from 'react'
import { cx } from '@/lib/cx'

interface PanelProps {
  title?: ReactNode
  actions?: ReactNode
  children: ReactNode
  className?: string
  bodyClassName?: string
}

export function Panel({ title, actions, children, className, bodyClassName }: PanelProps) {
  return (
    <section className={cx('min-w-0 bg-surface rounded-card border border-line', className)}>
      {(title || actions) && (
        <header className="flex items-center justify-between gap-4 px-6 py-4 border-b border-line">
          {title && <h2 className="text-lg font-medium">{title}</h2>}
          {actions && <div className="flex items-center gap-2">{actions}</div>}
        </header>
      )}
      <div className={cx('p-6', bodyClassName)}>{children}</div>
    </section>
  )
}

/** Panel for full-bleed tables. */
export function TablePanel({ title, actions, children }: PanelProps) {
  return (
    <Panel title={title} actions={actions} className="overflow-hidden" bodyClassName="p-0">
      {children}
    </Panel>
  )
}

export function EmptyState({ title, hint }: { title: string; hint?: ReactNode }) {
  return (
    <div className="py-12 text-center">
      <p className="text-body">{title}</p>
      {hint && <p className="mt-2 text-sm text-subtle">{hint}</p>}
    </div>
  )
}
