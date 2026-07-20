import { PageHeader } from '@/components/layout/AppLayout'
import { Async } from '@/components/ui/Async'
import { Badge } from '@/components/ui/Badge'
import { type Column, DataTable } from '@/components/ui/DataTable'
import { EmptyState, Panel, TablePanel } from '@/components/ui/Panel'
import { useT } from '@/i18n'
import type { Dictionary } from '@/i18n/en'
import { money, timestamp } from '@/lib/format'
import { useInvoices, useNotifications } from '@/lib/queries'
import type { InvoiceRow, InvoiceStatus, NotificationRow } from '@/lib/types'

const TONES: Record<InvoiceStatus, 'success' | 'danger' | 'info'> = {
  waiting_for_payment: 'info',
  paid: 'success',
  canceled: 'danger',
}

function statusLabel(t: Dictionary, status: InvoiceStatus): string {
  return t.invoices.statuses[status] ?? status
}

function invoiceColumns(t: Dictionary): Column<InvoiceRow>[] {
  const c = t.invoices
  return [
    { key: 'id', header: c.id, priority: 1, minWidth: 80, render: (r) => `#${r.id}` },
    {
      key: 'total',
      header: c.total,
      priority: 2,
      minWidth: 120,
      align: 'right',
      render: (r) => <span className="font-medium">{money(r.total)}</span>,
    },
    {
      key: 'status',
      header: c.status,
      priority: 3,
      minWidth: 190,
      render: (r) => <Badge tone={TONES[r.status]}>{statusLabel(t, r.status)}</Badge>,
    },
    {
      key: 'recipient_name',
      header: c.recipient,
      priority: 4,
      minWidth: 170,
      render: (r) => r.recipient_name ?? '-',
    },
    {
      key: 'contact',
      header: c.contact,
      priority: 6,
      minWidth: 200,
      render: (r) => r.email ?? r.phone ?? '-',
    },
    {
      key: 'description',
      header: c.description,
      priority: 7,
      minWidth: 200,
      render: (r) => r.description ?? '-',
    },
    {
      key: 'period',
      header: c.period,
      priority: 8,
      minWidth: 200,
      render: (r) => (r.period_from ? `${r.period_from} to ${r.period_to}` : '-'),
    },
    {
      key: 'is_template',
      header: c.template,
      priority: 9,
      minWidth: 120,
      render: (r) => (r.is_template ? '✓' : '-'),
    },
    {
      key: 'created_at',
      header: c.created,
      priority: 5,
      minWidth: 160,
      render: (r) => timestamp(r.created_at),
    },
  ]
}

function notificationColumns(t: Dictionary): Column<NotificationRow>[] {
  const c = t.invoices
  return [
    { key: 'channel', header: c.channel, priority: 1, minWidth: 110, render: (r) => r.channel },
    {
      key: 'recipient',
      header: c.recipientLabel,
      priority: 2,
      minWidth: 200,
      render: (r) => <span className="font-mono text-sm">{r.recipient}</span>,
    },
    {
      key: 'invoice_id',
      header: c.id,
      priority: 4,
      minWidth: 80,
      render: (r) => `#${r.invoice_id}`,
    },
    {
      key: 'subject',
      header: c.subject,
      priority: 5,
      minWidth: 180,
      render: (r) => r.subject ?? '-',
    },
    { key: 'body', header: c.body, priority: 3, minWidth: 300, render: (r) => r.body },
    {
      key: 'created_at',
      header: c.created,
      priority: 6,
      minWidth: 160,
      render: (r) => timestamp(r.created_at),
    },
  ]
}

export function InvoicesPage() {
  const t = useT()
  const invoices = useInvoices()
  const notifications = useNotifications()

  return (
    <>
      <PageHeader title={t.invoices.title} />
      <div className="grid gap-6">
        <TablePanel>
          <Async query={invoices}>
            {(rows) => (
              <DataTable
                columns={invoiceColumns(t)}
                rows={rows}
                getRowKey={(r) => r.id}
                emptyMessage={t.invoices.empty}
              />
            )}
          </Async>
        </TablePanel>

        <Async query={notifications}>
          {(rows) =>
            rows.length === 0 ? (
              <Panel title={t.invoices.sent}>
                <EmptyState title={t.invoices.sentEmpty} />
              </Panel>
            ) : (
              <TablePanel title={t.invoices.sent}>
                <DataTable columns={notificationColumns(t)} rows={rows} getRowKey={(r) => r.id} />
              </TablePanel>
            )
          }
        </Async>
      </div>
    </>
  )
}
