import { useState } from 'react'
import { PageHeader } from '@/components/layout/AppLayout'
import { Button } from '@/components/ui/Button'
import { Panel } from '@/components/ui/Panel'
import { useT } from '@/i18n'
import { api } from '@/lib/api'
import type { SignatureExplanation } from '@/lib/types'

const DEFAULT_PRIVATE_KEY = 'sandbox_private_key_0000000001'
const DEFAULT_PAYLOAD = JSON.stringify(
  { public_key: 'i000000001', amount: '30.75', currency: 'AZN', order_id: 'order-1' },
  null,
  2,
)

function Row({ label, value, mono = true }: { label: string; value: string; mono?: boolean }) {
  return (
    <div>
      <div className="text-muted text-sm mb-1">{label}</div>
      <pre
        className={`overflow-x-auto rounded-field border border-line bg-surface-alt p-3 text-xs ${mono ? 'font-mono' : ''}`}
      >
        {value}
      </pre>
    </div>
  )
}

function Verdict({ result }: { result: SignatureExplanation }) {
  const t = useT()
  if (result.matches === undefined) return null

  return result.matches ? (
    <div className="rounded-field border border-[#28a745]/30 bg-[#28a745]/5 p-4 text-[#28a745]">
      {t.signature.matches}
    </div>
  ) : (
    <div className="rounded-field border border-[#dc3545]/30 bg-[#dc3545]/5 p-4">
      <p className="font-bold text-[#dc3545]">{t.signature.noMatch}</p>
      {result.hint && <p className="mt-1.5 text-body">{result.hint}</p>}
    </div>
  )
}

function Verify() {
  const t = useT()
  const [privateKey, setPrivateKey] = useState(DEFAULT_PRIVATE_KEY)
  const [data, setData] = useState('')
  const [signature, setSignature] = useState('')
  const [result, setResult] = useState<SignatureExplanation | null>(null)

  const run = async () => {
    setResult(await api.verifySignature(privateKey, data, signature))
  }

  return (
    <Panel title={t.signature.verifyTitle}>
      <div className="grid gap-4">
        <label className="grid gap-1.5">
          <span className="text-muted text-sm">{t.signature.privateKey}</span>
          <input
            value={privateKey}
            onChange={(e) => setPrivateKey(e.target.value)}
            className="h-10 rounded-field border border-line px-3 font-mono text-sm"
          />
        </label>

        <label className="grid gap-1.5">
          <span className="text-muted text-sm">{t.signature.data}</span>
          <textarea
            value={data}
            onChange={(e) => setData(e.target.value)}
            rows={3}
            className="rounded-field border border-line p-3 font-mono text-sm"
          />
        </label>

        <label className="grid gap-1.5">
          <span className="text-muted text-sm">{t.signature.signature}</span>
          <input
            value={signature}
            onChange={(e) => setSignature(e.target.value)}
            className="h-10 rounded-field border border-line px-3 font-mono text-sm"
          />
        </label>

        <div>
          <Button onClick={run} disabled={!data}>
            {t.signature.check}
          </Button>
        </div>

        {result && (
          <div className="grid gap-4">
            <Verdict result={result} />
            <Row label={t.signature.formula} value={result.formula} mono={false} />
            <Row label={t.signature.hashedString} value={result.concatenated} />
            <Row label={t.signature.expected} value={result.expected_signature} />
            {result.decoded_payload && (
              <Row
                label={t.signature.decoded}
                value={JSON.stringify(result.decoded_payload, null, 2)}
              />
            )}
          </div>
        )}
      </div>
    </Panel>
  )
}

function Build() {
  const t = useT()
  const invalidJsonMessage = t.signature.invalidJson
  const [privateKey, setPrivateKey] = useState(DEFAULT_PRIVATE_KEY)
  const [payload, setPayload] = useState(DEFAULT_PAYLOAD)
  const [built, setBuilt] = useState<{ data: string; signature: string } | null>(null)
  const [error, setError] = useState<string | null>(null)

  const run = async () => {
    try {
      setError(null)
      setBuilt(await api.buildSignature(privateKey, JSON.parse(payload)))
    } catch {
      setError(invalidJsonMessage)
      setBuilt(null)
    }
  }

  const curl = built
    ? `curl -X POST http://localhost:8181/api/1/request \\\n  -d "data=${built.data}" \\\n  -d "signature=${built.signature}"`
    : ''

  return (
    <Panel title={t.signature.buildTitle}>
      <div className="grid gap-4">
        <label className="grid gap-1.5">
          <span className="text-muted text-sm">{t.signature.privateKey}</span>
          <input
            value={privateKey}
            onChange={(e) => setPrivateKey(e.target.value)}
            className="h-10 rounded-field border border-line px-3 font-mono text-sm"
          />
        </label>

        <label className="grid gap-1.5">
          <span className="text-muted text-sm">{t.signature.payload}</span>
          <textarea
            value={payload}
            onChange={(e) => setPayload(e.target.value)}
            rows={7}
            className="rounded-field border border-line p-3 font-mono text-sm"
          />
        </label>

        <div>
          <Button onClick={run}>{t.signature.sign}</Button>
        </div>

        {error && <p className="text-[#dc3545]">{error}</p>}

        {built && (
          <div className="grid gap-4">
            <Row label={t.signature.data} value={built.data} />
            <Row label={t.signature.signature} value={built.signature} />
            <Row label={t.signature.readyToRun} value={curl} />
          </div>
        )}
      </div>
    </Panel>
  )
}

export function SignaturePage() {
  const t = useT()
  return (
    <>
      <PageHeader title={t.signature.title} />
      <p className="mb-6 max-w-3xl text-body">
        {t.signature.intro}{' '}
        <code className="font-mono">base64(sha1_raw(private_key + data + private_key))</code>.{' '}
        {t.signature.introAfter}
      </p>
      <div className="grid gap-6 xl:grid-cols-2">
        <Verify />
        <Build />
      </div>
    </>
  )
}
