import { PageHeader } from '@/components/layout/AppLayout'
import { Async } from '@/components/ui/Async'
import { Badge } from '@/components/ui/Badge'
import { type Column, DataTable } from '@/components/ui/DataTable'
import { Panel, TablePanel } from '@/components/ui/Panel'
import { useT } from '@/i18n'
import type { Dictionary } from '@/i18n/en'
import { useTestCards } from '@/lib/queries'
import type { TestCard } from '@/lib/types'

function formatNumber(value: string) {
  return value.replace(/(.{4})/g, '$1 ').trim()
}

function columns(t: Dictionary): Column<TestCard>[] {
  const c = t.testCards
  return [
    {
      key: 'number',
      header: c.cardNumber,
      priority: 1,
      minWidth: 200,
      render: (r) => <span className="font-mono">{formatNumber(r.number)}</span>,
    },
    {
      key: 'code',
      header: c.bankCode,
      priority: 3,
      minWidth: 120,
      render: (r) => <span className="font-mono">{r.code || '-'}</span>,
    },
    { key: 'outcome', header: c.outcome, priority: 2, minWidth: 260, render: (r) => r.outcome },
    {
      key: 'approved',
      header: c.result,
      priority: 4,
      minWidth: 120,
      render: (r) => (
        <Badge tone={r.approved ? 'success' : 'danger'}>
          {r.approved ? c.approved : c.declined}
        </Badge>
      ),
    },
  ]
}

export function TestCardsPage() {
  const t = useT()
  const query = useTestCards()

  return (
    <>
      <PageHeader title={t.testCards.title} />
      <Async query={query}>
        {({ scheme, cards }) => (
          <div className="grid gap-6">
            <Panel>
              <p className="text-body">
                {t.testCards.intro} {scheme}. {t.testCards.outro}
              </p>
            </Panel>
            <TablePanel>
              <DataTable columns={columns(t)} rows={cards} getRowKey={(c) => c.number} />
            </TablePanel>
          </div>
        )}
      </Async>
    </>
  )
}
