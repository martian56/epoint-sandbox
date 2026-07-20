import { createContext, type ReactNode, use, useCallback, useMemo, useState } from 'react'
import { useMerchants } from './queries'
import type { Merchant } from './types'

const STORAGE_KEY = 'epoint-sandbox.merchant'

interface MerchantValue {
  merchants: Merchant[]
  active: Merchant | undefined
  setActive: (publicKey: string) => void
}

const MerchantContext = createContext<MerchantValue | null>(null)

export function MerchantProvider({ children }: { children: ReactNode }) {
  const { data } = useMerchants()
  const [selected, setSelected] = useState<string | null>(() =>
    typeof localStorage === 'undefined' ? null : localStorage.getItem(STORAGE_KEY),
  )

  const setActive = useCallback((publicKey: string) => {
    setSelected(publicKey)
    localStorage.setItem(STORAGE_KEY, publicKey)
  }, [])

  const value = useMemo(() => {
    const merchants = data ?? []
    const active = merchants.find((m) => m.public_key === selected) ?? merchants[0]
    return { merchants, active, setActive }
  }, [data, selected, setActive])

  return <MerchantContext value={value}>{children}</MerchantContext>
}

export function useMerchant(): MerchantValue {
  const value = use(MerchantContext)
  if (!value) throw new Error('useMerchant must be used inside MerchantProvider')
  return value
}

/** Active merchant's public key, for scoping queries. */
export function useActiveMerchantKey(): string | undefined {
  return useMerchant().active?.public_key
}
