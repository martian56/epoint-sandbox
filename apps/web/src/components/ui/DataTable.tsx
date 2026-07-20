import { Fragment, type ReactNode, useLayoutEffect, useRef, useState } from 'react'
import { useT } from '@/i18n'
import { cx } from '@/lib/cx'
import { EmptyState } from './Panel'

export interface Column<T> {
  key: string
  header: string
  render: (row: T) => ReactNode
  /** Lower survives longer when space runs out. */
  priority?: number
  minWidth?: number
  align?: 'left' | 'right'
}

interface DataTableProps<T> {
  columns: Column<T>[]
  rows: T[]
  getRowKey: (row: T) => string | number
  emptyMessage?: string
  footer?: ReactNode
}

const DEFAULT_MIN_WIDTH = 140
const CHEVRON_WIDTH = 44

function useContainerWidth() {
  const ref = useRef<HTMLDivElement>(null)
  const [width, setWidth] = useState(0)

  useLayoutEffect(() => {
    const element = ref.current
    if (!element) return

    const observer = new ResizeObserver(([entry]) => {
      if (entry) setWidth(entry.contentRect.width)
    })
    observer.observe(element)
    return () => observer.disconnect()
  }, [])

  return [ref, width] as const
}

function splitColumns<T>(columns: Column<T>[], available: number) {
  if (available === 0) return { visible: columns, hidden: [] as Column<T>[] }

  const byPriority = [...columns].sort(
    (a, b) => (a.priority ?? Number.MAX_SAFE_INTEGER) - (b.priority ?? Number.MAX_SAFE_INTEGER),
  )

  const keep = new Set<string>()
  let used = CHEVRON_WIDTH

  for (const column of byPriority) {
    const width = column.minWidth ?? DEFAULT_MIN_WIDTH
    if (used + width > available && keep.size > 0) break
    used += width
    keep.add(column.key)
  }

  return {
    visible: columns.filter((c) => keep.has(c.key)),
    hidden: columns.filter((c) => !keep.has(c.key)),
  }
}

export function DataTable<T>({
  columns,
  rows,
  getRowKey,
  emptyMessage,
  footer,
}: DataTableProps<T>) {
  const t = useT()
  const [ref, width] = useContainerWidth()
  const [expanded, setExpanded] = useState<Set<string | number>>(new Set())
  const { visible, hidden } = splitColumns(columns, width)

  const toggle = (key: string | number) => {
    setExpanded((current) => {
      const next = new Set(current)
      if (!next.delete(key)) next.add(key)
      return next
    })
  }

  return (
    <div ref={ref}>
      {rows.length === 0 ? (
        <EmptyState title={emptyMessage ?? t.common.noData} />
      ) : (
        <table className="w-full border-collapse">
          <thead>
            <tr>
              {visible.map((column) => (
                <th
                  key={column.key}
                  className={cx(
                    'h-[42px] px-4 bg-surface-alt text-muted text-sm font-bold whitespace-nowrap',
                    'border-y border-line',
                    column.align === 'right' ? 'text-right' : 'text-left',
                  )}
                >
                  {column.header}
                </th>
              ))}
              {hidden.length > 0 && <th className="w-11 border-y border-line bg-surface-alt" />}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const key = getRowKey(row)
              const isOpen = expanded.has(key)

              return (
                <Fragment key={key}>
                  <tr className="border-b border-line odd:bg-tint-50">
                    {visible.map((column) => (
                      <td
                        key={column.key}
                        className={cx(
                          'h-10 px-4 align-middle whitespace-nowrap',
                          column.align === 'right' ? 'text-right' : 'text-left',
                        )}
                      >
                        {column.render(row)}
                      </td>
                    ))}
                    {hidden.length > 0 && (
                      <td className="w-11 text-center">
                        <button
                          type="button"
                          aria-label={isOpen ? t.common.collapseRow : t.common.expandRow}
                          aria-expanded={isOpen}
                          onClick={() => toggle(key)}
                          className="h-8 w-8 rounded-pill text-muted hover:bg-tint-100 hover:text-brand"
                        >
                          {isOpen ? '▴' : '▾'}
                        </button>
                      </td>
                    )}
                  </tr>

                  {isOpen && hidden.length > 0 && (
                    <tr className="border-b border-line">
                      <td colSpan={visible.length + 1} className="bg-canvas p-4">
                        <dl className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                          {hidden.map((column) => (
                            <div key={column.key}>
                              <dt className="text-muted text-sm">{column.header}</dt>
                              <dd className="mt-0.5 break-all">{column.render(row)}</dd>
                            </div>
                          ))}
                        </dl>
                      </td>
                    </tr>
                  )}
                </Fragment>
              )
            })}
          </tbody>
        </table>
      )}
      {footer && <div className="px-4 pt-3 pb-2 text-right">{footer}</div>}
    </div>
  )
}
