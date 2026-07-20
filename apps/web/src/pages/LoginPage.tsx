import { type FormEvent, useState } from 'react'
import logoUrl from '@/assets/epoint-logo.svg'
import { Button } from '@/components/ui/Button'
import { Field } from '@/components/ui/Field'
import { useT } from '@/i18n'
import { ApiError } from '@/lib/api'
import { useAuth } from '@/lib/auth'

export function LoginPage() {
  const t = useT()
  const { signIn } = useAuth()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError(null)

    try {
      await signIn(email, password)
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : t.login.failed)
      setBusy(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-canvas px-4">
      <form onSubmit={submit} className="w-full max-w-sm">
        <div className="mb-8 flex items-center justify-center gap-3">
          <img src={logoUrl} alt="Epoint" className="h-[26px] w-auto" />
          <span className="rounded-pill bg-tint-200 px-2.5 py-1 text-xs font-bold text-brand-deep">
            SANDBOX
          </span>
        </div>

        <div className="rounded-card border border-line bg-surface p-6">
          <h1 className="mb-1 text-xl font-medium">{t.login.title}</h1>
          <p className="mb-5 text-muted text-sm">{t.login.subtitle}</p>

          <div className="grid gap-4">
            <Field
              label={t.login.email}
              type="email"
              value={email}
              autoComplete="username"
              required
              onChange={(e) => setEmail(e.target.value)}
            />
            <Field
              label={t.login.password}
              type="password"
              value={password}
              autoComplete="current-password"
              required
              onChange={(e) => setPassword(e.target.value)}
            />

            {error && (
              <p role="alert" className="text-danger text-sm">
                {error}
              </p>
            )}

            <Button type="submit" size="md" disabled={busy} className="w-full">
              {busy ? t.login.signingIn : t.login.signIn}
            </Button>
          </div>
        </div>

        <p className="mt-4 text-center text-subtle text-xs">{t.login.hint}</p>
      </form>
    </div>
  )
}
