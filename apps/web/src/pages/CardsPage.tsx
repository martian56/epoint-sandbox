import { PageHeader } from '@/components/layout/AppLayout'
import { Async } from '@/components/ui/Async'
import { Badge } from '@/components/ui/Badge'
import { type Column, DataTable } from '@/components/ui/DataTable'
import { TablePanel } from '@/components/ui/Panel'
import { useT } from '@/i18n'
import type { Dictionary } from '@/i18n/en'
import { timestamp } from '@/lib/format'
import { useSavedCards } from '@/lib/queries'
import type { CardStatus, SavedCard } from '@/lib/types'

const TONES: Record<CardStatus, 'success' | 'danger' | 'warning' | 'neutral' | 'info'> = {
  new: 'info',
  active: 'success',
  pending: 'info',
  rejected: 'danger',
  expired: 'neutral',
  session_expired: 'neutral',
}

function columns(t: Dictionary): Column<SavedCard>[] {
  const c = t.cards
  return [
    {
      key: 'card_id',
      header: c.cardId,
      priority: 1,
      minWidth: 140,
      render: (r) => <span className="font-mono text-sm">{r.card_id}</span>,
    },
    {
      key: 'mask',
      header: c.mask,
      priority: 2,
      minWidth: 180,
      render: (r) => <span className="font-mono text-sm">{r.mask ?? '-'}</span>,
    },
    {
      key: 'status',
      header: c.status,
      priority: 3,
      minWidth: 130,
      render: (r) => <Badge tone={TONES[r.status]}>{r.status.replace('_', ' ')}</Badge>,
    },
    {
      key: 'holder_name',
      header: c.holder,
      priority: 5,
      minWidth: 180,
      render: (r) => r.holder_name ?? '-',
    },
    { key: 'expiry', header: c.expiry, priority: 6, minWidth: 110, render: (r) => r.expiry ?? '-' },
    {
      key: 'is_payout_card',
      header: c.type,
      priority: 4,
      minWidth: 150,
      render: (r) => (r.is_payout_card ? c.payout : c.payment),
    },
    {
      key: 'description',
      header: c.description,
      priority: 7,
      minWidth: 200,
      render: (r) => r.description ?? '-',
    },
    {
      key: 'created_at',
      header: c.added,
      priority: 8,
      minWidth: 160,
      render: (r) => timestamp(r.created_at),
    },
  ]
}

export function CardsPage() {
  const t = useT()
  const query = useSavedCards()

  return (
    <>
      <PageHeader title={t.cards.title} />
      <TablePanel>
        <Async query={query}>
          {(rows) => (
            <DataTable
              columns={columns(t)}
              rows={rows}
              getRowKey={(r) => r.card_id}
              emptyMessage={t.cards.empty}
            />
          )}
        </Async>
      </TablePanel>
    </>
  )
}
