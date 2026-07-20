import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createContext, type ReactNode, use } from 'react'
import { api } from './api'
import type { SessionState } from './types'

interface AuthValue {
  session: SessionState | undefined
  loading: boolean
  signIn: (email: string, password: string) => Promise<void>
  signOut: () => Promise<void>
}

const AuthContext = createContext<AuthValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()

  const { data: session, isPending } = useQuery({
    queryKey: ['auth', 'session'],
    queryFn: api.session,
    retry: false,
  })

  const refresh = () => queryClient.invalidateQueries()

  const login = useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      api.login(email, password),
    onSuccess: refresh,
  })

  const logout = useMutation({ mutationFn: api.logout, onSuccess: refresh })

  const value: AuthValue = {
    session,
    loading: isPending,
    signIn: async (email, password) => {
      await login.mutateAsync({ email, password })
    },
    signOut: async () => {
      await logout.mutateAsync()
    },
  }

  return <AuthContext value={value}>{children}</AuthContext>
}

export function useAuth(): AuthValue {
  const value = use(AuthContext)
  if (!value) throw new Error('useAuth must be used inside AuthProvider')
  return value
}
