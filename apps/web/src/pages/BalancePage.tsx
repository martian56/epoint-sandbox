import { PageHeader } from '@/components/layout/AppLayout'
import { Async } from '@/components/ui/Async'
import { Badge } from '@/components/ui/Badge'
import { type Column, DataTable } from '@/components/ui/DataTable'
import { Panel, TablePanel } from '@/components/ui/Panel'
import { useT } from '@/i18n'
import type { Dictionary } from '@/i18n/en'
import { money, timestamp } from '@/lib/format'
import { useBalance } from '@/lib/queries'
import type { BalanceRow } from '@/lib/types'

const CREDIT_KINDS = new Set(['payment', 'split_in'])

function kindLabel(t: Dictionary, kind: string): string {
  return t.balance.kinds[kind as keyof Dictionary['balance']['kinds']] ?? kind
}

function columns(t: Dictionary): Column<BalanceRow>[] {
  const c = t.balance
  return [
    { key: 'id', header: c.entry, priority: 4, minWidth: 90, render: (r) => `#${r.id}` },
    {
      key: 'kind',
      header: c.kind,
      priority: 2,
      minWidth: 160,
      render: (r) => (
        <Badge tone={CREDIT_KINDS.has(r.kind) ? 'success' : 'neutral'}>
          {kindLabel(t, r.kind)}
        </Badge>
      ),
    },
    {
      key: 'amount',
      header: c.amount,
      priority: 1,
      minWidth: 120,
      align: 'right',
      render: (r) => (
        <span className={r.amount < 0 ? 'font-medium text-danger' : 'font-medium'}>
          {money(r.amount)}
        </span>
      ),
    },
    {
      key: 'balance_after',
      header: c.runningTotal,
      priority: 3,
      minWidth: 140,
      align: 'right',
      render: (r) => money(r.balance_after),
    },
    {
      key: 'description',
      header: c.description,
      priority: 5,
      minWidth: 220,
      render: (r) => r.description ?? '-',
    },
    {
      key: 'created_at',
      header: c.date,
      priority: 6,
      minWidth: 160,
      render: (r) => timestamp(r.created_at),
    },
  ]
}

export function BalancePage() {
  const t = useT()
  const query = useBalance()

  return (
    <>
      <PageHeader title={t.balance.title} />
      <Async query={query}>
        {(rows) => (
          <div className="grid gap-6">
            <Panel>
              <div className="flex items-baseline justify-between">
                <span className="text-muted">{t.balance.current}</span>
                <span className="text-[28px] font-medium">
                  {money(rows[0]?.balance_after ?? 0)}
                </span>
              </div>
            </Panel>
            <TablePanel>
              <DataTable
                columns={columns(t)}
                rows={rows}
                getRowKey={(r) => r.id}
                emptyMessage={t.balance.empty}
              />
            </TablePanel>
          </div>
        )}
      </Async>
    </>
  )
}
