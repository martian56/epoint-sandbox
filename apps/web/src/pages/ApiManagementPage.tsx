import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { PageHeader } from '@/components/layout/AppLayout'
import { Async } from '@/components/ui/Async'
import { Button } from '@/components/ui/Button'
import { CopyField } from '@/components/ui/CopyField'
import { Field } from '@/components/ui/Field'
import { Panel } from '@/components/ui/Panel'
import { Toggle } from '@/components/ui/Toggle'
import { useT } from '@/i18n'
import { api } from '@/lib/api'
import { money } from '@/lib/format'
import { useMerchant } from '@/lib/merchant'
import { useMerchants } from '@/lib/queries'
import type { Merchant, MerchantInput } from '@/lib/types'

const URL_FIELDS = ['site_url', 'success_url', 'error_url', 'result_url'] as const

type UrlField = (typeof URL_FIELDS)[number]

function useMerchantMutations() {
  const queryClient = useQueryClient()
  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['merchants'] })

  return {
    update: useMutation({
      mutationFn: ({ key, changes }: { key: string; changes: MerchantInput }) =>
        api.updateMerchant(key, changes),
      onSuccess: invalidate,
    }),
    create: useMutation({ mutationFn: api.createMerchant, onSuccess: invalidate }),
    remove: useMutation({ mutationFn: api.deleteMerchant, onSuccess: invalidate }),
    rotate: useMutation({ mutationFn: api.rotateKey, onSuccess: invalidate }),
  }
}

function IntegrationUrls({ merchant }: { merchant: Merchant }) {
  const t = useT()
  const { update } = useMerchantMutations()
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState<Record<UrlField, string>>(() => blank(merchant))

  useEffect(() => {
    if (!editing) setDraft(blank(merchant))
  }, [merchant, editing])

  const labels: Record<UrlField, string> = {
    site_url: t.apiManagement.websiteAddress,
    success_url: t.apiManagement.successLink,
    error_url: t.apiManagement.failedLink,
    result_url: t.apiManagement.resultLink,
  }

  const save = async () => {
    await update.mutateAsync({ key: merchant.public_key, changes: draft })
    setEditing(false)
  }

  if (!editing) {
    return (
      <Panel
        title={t.apiManagement.connectionOptions}
        actions={
          <Button variant="outline" onClick={() => setEditing(true)}>
            {t.common.edit}
          </Button>
        }
      >
        <dl className="grid gap-3">
          {URL_FIELDS.map((field) => (
            <div
              key={field}
              className="flex flex-wrap justify-between gap-2 border-b border-line pb-2"
            >
              <dt className="text-muted">{labels[field]}</dt>
              <dd className="font-mono text-sm">{merchant[field] ?? t.common.notSet}</dd>
            </div>
          ))}
        </dl>
      </Panel>
    )
  }

  return (
    <Panel title={t.apiManagement.connectionOptions}>
      <div className="grid gap-4">
        {URL_FIELDS.map((field) => (
          <Field
            key={field}
            label={labels[field]}
            value={draft[field]}
            placeholder="https://"
            mono
            onChange={(e) => setDraft((d) => ({ ...d, [field]: e.target.value }))}
          />
        ))}

        <p className="text-subtle text-xs">{t.apiManagement.callbackNote}</p>

        <div className="flex gap-2">
          <Button onClick={save} disabled={update.isPending}>
            {update.isPending ? t.common.saving : t.common.save}
          </Button>
          <Button variant="ghost" onClick={() => setEditing(false)}>
            {t.common.cancel}
          </Button>
        </div>
      </div>
    </Panel>
  )
}

function blank(merchant: Merchant): Record<UrlField, string> {
  return {
    site_url: merchant.site_url ?? '',
    success_url: merchant.success_url ?? '',
    error_url: merchant.error_url ?? '',
    result_url: merchant.result_url ?? '',
  }
}

function Keys({ merchant }: { merchant: Merchant }) {
  const t = useT()
  const { rotate } = useMerchantMutations()

  return (
    <Panel
      title={merchant.name}
      actions={<span className="text-muted">{money(merchant.balance)}</span>}
    >
      <div className="grid gap-4">
        <CopyField label={t.apiManagement.publicKey} value={merchant.public_key} />
        <CopyField label={t.apiManagement.privateKey} value={merchant.private_key} secret />

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            onClick={() => rotate.mutate(merchant.public_key)}
            disabled={rotate.isPending}
          >
            {t.apiManagement.rotateKey}
          </Button>
          <span className="text-subtle text-xs">{t.apiManagement.rotateNote}</span>
        </div>
      </div>
    </Panel>
  )
}

const FEATURE_FIELDS = [
  'amex_enabled',
  'token_payments_enabled',
  'installments_enabled',
  'wallets_enabled',
  'b2b_enabled',
] as const

function Features({ merchant }: { merchant: Merchant }) {
  const t = useT()
  const { update } = useMerchantMutations()

  return (
    <Panel title={t.features.title}>
      <p className="mb-4 text-body">{t.features.intro}</p>
      {FEATURE_FIELDS.map((field) => (
        <Toggle
          key={field}
          label={t.features[field]}
          checked={merchant.features[field]}
          disabled={update.isPending}
          onChange={(next) =>
            update.mutate({ key: merchant.public_key, changes: { [field]: next } })
          }
        />
      ))}
    </Panel>
  )
}

function CreateAccount() {
  const t = useT()
  const { create } = useMerchantMutations()
  const [name, setName] = useState('')

  const submit = async () => {
    if (!name.trim()) return
    await create.mutateAsync({ name: name.trim() })
    setName('')
  }

  return (
    <div className="flex flex-wrap items-end gap-3">
      <Field
        label={t.accounts.newName}
        value={name}
        placeholder="Marketplace Vendor"
        onChange={(e) => setName(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && submit()}
        className="min-w-[240px]"
      />
      <Button onClick={submit} disabled={!name.trim() || create.isPending}>
        {t.accounts.create}
      </Button>
    </div>
  )
}

function AccountRow({ merchant, isActive }: { merchant: Merchant; isActive: boolean }) {
  const t = useT()
  const { setActive } = useMerchant()
  const { remove } = useMerchantMutations()

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line py-3 last:border-0">
      <div>
        <div className="font-medium">
          {merchant.name}
          {isActive && <span className="ml-2 text-brand-bright text-xs">{t.accounts.active}</span>}
        </div>
        <div className="font-mono text-muted text-xs">{merchant.public_key}</div>
      </div>

      <div className="flex items-center gap-2">
        <span className="text-muted">{money(merchant.balance)}</span>
        {!isActive && (
          <Button variant="tinted" onClick={() => setActive(merchant.public_key)}>
            {t.accounts.select}
          </Button>
        )}
        <Button
          variant="ghost"
          onClick={() => remove.mutate(merchant.public_key)}
          disabled={remove.isPending}
        >
          {t.accounts.remove}
        </Button>
      </div>
    </div>
  )
}

export function ApiManagementPage() {
  const t = useT()
  const query = useMerchants()
  const { active } = useMerchant()
  const { remove } = useMerchantMutations()

  return (
    <>
      <PageHeader title={t.apiManagement.title} />
      <Async query={query}>
        {(merchants) => {
          const current = merchants.find((m) => m.public_key === active?.public_key) ?? merchants[0]
          if (!current) return null

          return (
            <div className="grid gap-6">
              <div className="rounded-card border border-[#28a745]/30 bg-[#28a745]/5 px-4 py-3 text-[#28a745]">
                {t.apiManagement.accessEnabled}
              </div>

              <Keys merchant={current} />
              <IntegrationUrls merchant={current} />
              <Features merchant={current} />

              <Panel title={t.apiManagement.pointHere}>
                <p className="mb-3 text-body">{t.apiManagement.pointHereBody}</p>
                <pre className="overflow-x-auto rounded-field border border-line bg-surface-alt p-4 font-mono text-xs">
                  {'https://epoint.az/api/1/request   →   http://localhost:8181/api/1/request'}
                </pre>
              </Panel>

              <Panel title={t.accounts.title}>
                <p className="mb-4 text-body">{t.accounts.intro}</p>
                {merchants.map((merchant) => (
                  <AccountRow
                    key={merchant.public_key}
                    merchant={merchant}
                    isActive={merchant.public_key === current.public_key}
                  />
                ))}
                <div className="mt-5 border-t border-line pt-5">
                  <CreateAccount />
                </div>
                {remove.isError && (
                  <p className="mt-3 text-[#dc3545]">{(remove.error as Error).message}</p>
                )}
              </Panel>
            </div>
          )
        }}
      </Async>
    </>
  )
}
