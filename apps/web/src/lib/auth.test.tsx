import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { ReactNode } from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { I18nProvider } from '@/i18n'
import { LoginPage } from '@/pages/LoginPage'
import { AuthProvider, useAuth } from './auth'
import type { SessionState } from './types'

function respond(body: unknown, status = 200) {
  return Promise.resolve(
    new Response(JSON.stringify(body), {
      status,
      headers: { 'Content-Type': 'application/json' },
    }),
  )
}

function mockSession(session: SessionState) {
  vi.stubGlobal(
    'fetch',
    vi.fn((input: RequestInfo | URL) => {
      const url = String(input)
      if (url.includes('/auth/session')) return respond(session)
      if (url.includes('/auth/login')) {
        return respond({ auth_required: true, authenticated: true, email: 'a@b.c' })
      }
      return respond([])
    }),
  )
}

function Providers({ children }: { children: ReactNode }) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return (
    <QueryClientProvider client={queryClient}>
      <I18nProvider>
        <AuthProvider>{children}</AuthProvider>
      </I18nProvider>
    </QueryClientProvider>
  )
}

function Probe() {
  const { session, loading } = useAuth()
  if (loading) return <span>loading</span>
  return (
    <span data-testid="state">
      {session?.auth_required ? 'required' : 'open'}:{session?.authenticated ? 'in' : 'out'}
    </span>
  )
}

beforeEach(() => vi.unstubAllGlobals())
afterEach(() => vi.unstubAllGlobals())

describe('AuthProvider', () => {
  it('reports an open sandbox when no password is configured', async () => {
    mockSession({ auth_required: false, authenticated: true, email: null })
    render(<Probe />, { wrapper: Providers })

    await waitFor(() => expect(screen.getByTestId('state')).toHaveTextContent('open:in'))
  })

  it('reports that a login is needed when one is configured', async () => {
    mockSession({ auth_required: true, authenticated: false, email: null })
    render(<Probe />, { wrapper: Providers })

    await waitFor(() => expect(screen.getByTestId('state')).toHaveTextContent('required:out'))
  })
})

describe('LoginPage', () => {
  beforeEach(() => mockSession({ auth_required: true, authenticated: false, email: null }))

  it('sends the credentials that were typed', async () => {
    const user = userEvent.setup()
    render(<LoginPage />, { wrapper: Providers })

    await user.type(screen.getByLabelText('Email'), 'admin@example.com')
    await user.type(screen.getByLabelText('Password'), 'hunter2')
    await user.click(screen.getByRole('button', { name: 'Sign in' }))

    await waitFor(() => {
      const calls = vi.mocked(fetch).mock.calls
      const login = calls.find(([url]) => String(url).includes('/auth/login'))
      expect(login).toBeDefined()
      expect(JSON.parse(String(login?.[1]?.body))).toEqual({
        email: 'admin@example.com',
        password: 'hunter2',
      })
    })
  })

  it('shows the reason when the password is wrong', async () => {
    const user = userEvent.setup()
    vi.stubGlobal(
      'fetch',
      vi.fn((input: RequestInfo | URL) => {
        const url = String(input)
        if (url.includes('/auth/session')) {
          return respond({ auth_required: true, authenticated: false, email: null })
        }
        return respond({ detail: 'Incorrect email or password' }, 401)
      }),
    )

    render(<LoginPage />, { wrapper: Providers })
    await user.type(screen.getByLabelText('Email'), 'admin@example.com')
    await user.type(screen.getByLabelText('Password'), 'wrong')
    await user.click(screen.getByRole('button', { name: 'Sign in' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Incorrect email or password')
  })

  it('never puts the password in the DOM as readable text', async () => {
    const user = userEvent.setup()
    render(<LoginPage />, { wrapper: Providers })

    const password = screen.getByLabelText('Password')
    await user.type(password, 'hunter2')
    expect(password).toHaveAttribute('type', 'password')
  })
})
