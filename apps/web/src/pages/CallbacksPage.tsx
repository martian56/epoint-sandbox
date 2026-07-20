import { type ReactNode, useState } from 'react'
import { PageHeader } from '@/components/layout/AppLayout'
import { Async } from '@/components/ui/Async'
import { StatusBadge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { EmptyState, Panel } from '@/components/ui/Panel'
import { useT } from '@/i18n'
import { duration, timestamp } from '@/lib/format'
import { useCallbacks } from '@/lib/queries'
import type { CallbackAttempt } from '@/lib/types'

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <div className="text-muted text-sm mb-1">{label}</div>
      <pre className="overflow-x-auto rounded-field border border-line bg-surface-alt p-3 font-mono text-xs">
        {children}
      </pre>
    </div>
  )
}

function CallbackDetail({ attempt }: { attempt: CallbackAttempt }) {
  const t = useT()

  return (
    <div className="grid gap-4 border-t border-line pt-4">
      <Field label={t.callbacks.decodedPayload}>{JSON.stringify(attempt.decoded, null, 2)}</Field>
      <div className="grid gap-4 lg:grid-cols-2">
        <Field label={t.callbacks.rawData}>{attempt.data}</Field>
        <Field label={t.callbacks.signature}>{attempt.signature}</Field>
      </div>
      {attempt.response_body && (
        <Field label={t.callbacks.yourResponse}>{attempt.response_body}</Field>
      )}
      {attempt.error && (
        <div>
          <div className="text-muted text-sm mb-1">{t.callbacks.error}</div>
          <pre className="overflow-x-auto whitespace-pre-wrap rounded-field border border-danger/30 bg-danger/5 p-3 text-xs text-danger">
            {attempt.error}
          </pre>
        </div>
      )}
    </div>
  )
}

function CallbackCard({ attempt }: { attempt: CallbackAttempt }) {
  const t = useT()
  const [open, setOpen] = useState(false)

  return (
    <Panel>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <StatusBadge status={attempt.status} />
          <span className="font-mono text-sm">{attempt.target_url}</span>
        </div>
        <div className="flex items-center gap-4 text-muted">
          <span>
            {t.callbacks.attempt} {attempt.attempt}
          </span>
          <span>{attempt.response_status ?? t.callbacks.noResponse}</span>
          <span>{duration(attempt.duration_ms)}</span>
          <span>{timestamp(attempt.created_at)}</span>
          <Button variant="ghost" onClick={() => setOpen((v) => !v)}>
            {open ? t.common.hide : t.common.inspect}
          </Button>
        </div>
      </div>
      {open && <CallbackDetail attempt={attempt} />}
    </Panel>
  )
}

export function CallbacksPage() {
  const t = useT()
  const query = useCallbacks()

  return (
    <>
      <PageHeader title={t.callbacks.title} />
      <Async query={query}>
        {(rows) =>
          rows.length === 0 ? (
            <Panel>
              <EmptyState title={t.callbacks.empty} hint={t.callbacks.emptyHint} />
            </Panel>
          ) : (
            <div className="grid gap-4">
              {rows.map((attempt) => (
                <CallbackCard key={attempt.id} attempt={attempt} />
              ))}
            </div>
          )
        }
      </Async>
    </>
  )
}
