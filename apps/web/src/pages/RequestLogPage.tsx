import { PageHeader } from '@/components/layout/AppLayout'
import { Async } from '@/components/ui/Async'
import { Badge } from '@/components/ui/Badge'
import { type Column, DataTable } from '@/components/ui/DataTable'
import { TablePanel } from '@/components/ui/Panel'
import { useT } from '@/i18n'
import type { Dictionary } from '@/i18n/en'
import { duration, timestamp } from '@/lib/format'
import { useRequestLog } from '@/lib/queries'
import type { RequestLogEntry } from '@/lib/types'

function json(value: Record<string, unknown> | null) {
  return value ? (
    <pre className="max-w-md overflow-x-auto font-mono text-xs">
      {JSON.stringify(value, null, 2)}
    </pre>
  ) : (
    '-'
  )
}

function columns(t: Dictionary): Column<RequestLogEntry>[] {
  const c = t.requestLog
  return [
    { key: 'method', header: c.method, priority: 3, minWidth: 100, render: (r) => r.method },
    {
      key: 'path',
      header: c.path,
      priority: 1,
      minWidth: 220,
      render: (r) => <span className="font-mono text-sm">{r.path}</span>,
    },
    {
      key: 'status_code',
      header: c.status,
      priority: 2,
      minWidth: 100,
      render: (r) => (
        <Badge tone={r.status_code < 400 ? 'success' : 'danger'}>{r.status_code}</Badge>
      ),
    },
    {
      key: 'signature_valid',
      header: c.signature,
      priority: 4,
      minWidth: 130,
      render: (r) =>
        r.signature_valid === null ? (
          '-'
        ) : (
          <Badge tone={r.signature_valid ? 'success' : 'danger'}>
            {r.signature_valid ? c.valid : c.invalid}
          </Badge>
        ),
    },
    {
      key: 'duration_ms',
      header: c.time,
      priority: 6,
      minWidth: 100,
      align: 'right',
      render: (r) => duration(r.duration_ms),
    },
    {
      key: 'trace_id',
      header: t.transactions.traceId,
      priority: 5,
      minWidth: 200,
      render: (r) => <span className="font-mono text-sm">{r.trace_id}</span>,
    },
    {
      key: 'request',
      header: c.request,
      priority: 8,
      minWidth: 240,
      render: (r) => json(r.request),
    },
    {
      key: 'response',
      header: c.response,
      priority: 9,
      minWidth: 240,
      render: (r) => json(r.response),
    },
    {
      key: 'created_at',
      header: t.transactions.date,
      priority: 7,
      minWidth: 160,
      render: (r) => timestamp(r.created_at),
    },
  ]
}

export function RequestLogPage() {
  const t = useT()
  const query = useRequestLog()

  return (
    <>
      <PageHeader title={t.requestLog.title} />
      <TablePanel>
        <Async query={query}>
          {(rows) => (
            <DataTable
              columns={columns(t)}
              rows={rows}
              getRowKey={(r) => r.trace_id}
              emptyMessage={t.requestLog.empty}
            />
          )}
        </Async>
      </TablePanel>
    </>
  )
}
