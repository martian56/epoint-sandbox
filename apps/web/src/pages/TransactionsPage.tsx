import { PageHeader } from '@/components/layout/AppLayout'
import { Async } from '@/components/ui/Async'
import { StatusBadge } from '@/components/ui/Badge'
import { type Column, DataTable } from '@/components/ui/DataTable'
import { TablePanel } from '@/components/ui/Panel'
import { useT } from '@/i18n'
import type { Dictionary } from '@/i18n/en'
import { money, timestamp } from '@/lib/format'
import { useTransactions } from '@/lib/queries'
import type { Transaction } from '@/lib/types'

const mono = (value: string) => <span className="font-mono text-sm">{value}</span>

function columns(t: Dictionary): Column<Transaction>[] {
  const c = t.transactions
  return [
    {
      key: 'transaction',
      header: c.transaction,
      priority: 1,
      minWidth: 150,
      render: (r) => mono(r.transaction),
    },
    {
      key: 'order_id',
      header: c.orderId,
      priority: 3,
      minWidth: 180,
      render: (r) => mono(r.order_id),
    },
    {
      key: 'status',
      header: c.status,
      priority: 2,
      minWidth: 120,
      render: (r) => <StatusBadge status={r.status} />,
    },
    {
      key: 'amount',
      header: c.sum,
      priority: 2,
      minWidth: 110,
      align: 'right',
      render: (r) => <span className="font-medium">{money(r.amount, r.currency)}</span>,
    },
    { key: 'code', header: c.bankCode, priority: 5, minWidth: 110, render: (r) => r.code ?? '-' },
    {
      key: 'card_mask',
      header: c.card,
      priority: 6,
      minWidth: 160,
      render: (r) => mono(r.card_mask ?? '-'),
    },
    { key: 'rrn', header: c.rrn, priority: 7, minWidth: 140, render: (r) => r.rrn ?? '-' },
    { key: 'endpoint', header: c.endpoint, priority: 8, minWidth: 150, render: (r) => r.endpoint },
    {
      key: 'description',
      header: c.description,
      priority: 9,
      minWidth: 200,
      render: (r) => r.description ?? '-',
    },
    {
      key: 'trace_id',
      header: c.traceId,
      priority: 10,
      minWidth: 180,
      render: (r) => mono(r.trace_id),
    },
    {
      key: 'created_at',
      header: c.date,
      priority: 4,
      minWidth: 160,
      render: (r) => timestamp(r.created_at),
    },
  ]
}

export function TransactionsPage() {
  const t = useT()
  const query = useTransactions()

  return (
    <>
      <PageHeader title={t.transactions.title} />
      <TablePanel>
        <Async query={query}>
          {(rows) => (
            <DataTable
              columns={columns(t)}
              rows={rows}
              getRowKey={(r) => r.transaction}
              emptyMessage={t.transactions.empty}
              footer={
                rows.length > 0 && (
                  <span className="text-sm">
                    {t.common.total}:{' '}
                    <strong>
                      {money(
                        rows
                          .filter((r) => r.status === 'success')
                          .reduce((s, r) => s + r.amount, 0),
                      )}
                    </strong>
                  </span>
                )
              }
            />
          )}
        </Async>
      </TablePanel>
    </>
  )
}
