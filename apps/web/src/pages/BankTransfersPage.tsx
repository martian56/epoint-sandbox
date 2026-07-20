import { useQueryClient } from '@tanstack/react-query'
import { PageHeader } from '@/components/layout/AppLayout'
import { Async } from '@/components/ui/Async'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { type Column, DataTable } from '@/components/ui/DataTable'
import { TablePanel } from '@/components/ui/Panel'
import { useT } from '@/i18n'
import type { Dictionary } from '@/i18n/en'
import { money, timestamp } from '@/lib/format'
import { useB2B } from '@/lib/queries'
import type { B2BRow, B2BStatus } from '@/lib/types'

const TONES: Record<B2BStatus, 'success' | 'danger' | 'info' | 'neutral'> = {
  PENDING: 'info',
  PROCESSING: 'info',
  SUCCESS: 'success',
  FAILED: 'danger',
}

const TERMINAL: B2BStatus[] = ['SUCCESS', 'FAILED']

function columns(t: Dictionary, advance: (orderId: string) => void): Column<B2BRow>[] {
  const c = t.b2b
  return [
    {
      key: 'order_id',
      header: c.orderId,
      priority: 1,
      minWidth: 180,
      render: (r) => <span className="font-mono text-sm">{r.order_id}</span>,
    },
    {
      key: 'status',
      header: c.status,
      priority: 2,
      minWidth: 140,
      render: (r) => <Badge tone={TONES[r.status]}>{r.status}</Badge>,
    },
    {
      key: 'amount',
      header: c.amount,
      priority: 3,
      minWidth: 120,
      align: 'right',
      render: (r) => <span className="font-medium">{money(r.amount)}</span>,
    },
    { key: 'payee_name', header: c.payee, priority: 4, minWidth: 190, render: (r) => r.payee_name },
    {
      key: 'payee_iban',
      header: c.iban,
      priority: 6,
      minWidth: 260,
      render: (r) => <span className="font-mono text-sm">{r.payee_iban}</span>,
    },
    {
      key: 'bank_code',
      header: c.bankCode,
      priority: 8,
      minWidth: 130,
      render: (r) => r.bank_code,
    },
    {
      key: 'webhook_sent',
      header: c.webhookSent,
      priority: 7,
      minWidth: 140,
      render: (r) => (
        <Badge tone={r.webhook_sent ? 'success' : 'neutral'}>{r.webhook_sent ? c.yes : c.no}</Badge>
      ),
    },
    {
      key: 'created_at',
      header: c.created,
      priority: 9,
      minWidth: 160,
      render: (r) => timestamp(r.created_at),
    },
    {
      key: 'advance',
      header: '',
      priority: 5,
      minWidth: 120,
      align: 'right',
      render: (r) =>
        TERMINAL.includes(r.status) ? null : (
          <Button variant="tinted" onClick={() => advance(r.order_id)}>
            {c.advance}
          </Button>
        ),
    },
  ]
}

export function BankTransfersPage() {
  const t = useT()
  const query = useB2B()
  const queryClient = useQueryClient()

  const advance = async (orderId: string) => {
    await fetch(`/api/1/b2b/payment/${orderId}/advance`, { method: 'POST' })
    await queryClient.invalidateQueries({ queryKey: ['b2b'] })
  }

  return (
    <>
      <PageHeader title={t.b2b.title} />
      <TablePanel>
        <Async query={query}>
          {(rows) => (
            <DataTable
              columns={columns(t, advance)}
              rows={rows}
              getRowKey={(r) => r.order_id}
              emptyMessage={t.b2b.empty}
            />
          )}
        </Async>
      </TablePanel>
    </>
  )
}
