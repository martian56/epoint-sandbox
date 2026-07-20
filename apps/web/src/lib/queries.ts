import { useQuery } from '@tanstack/react-query'
import { api } from './api'
import { useActiveMerchantKey } from './merchant'

const REFRESH_MS = 5000

export const useMerchants = () =>
  useQuery({ queryKey: ['merchants'], queryFn: () => api.merchants() })

export const useTransactions = () => {
  const merchant = useActiveMerchantKey()
  return useQuery({
    queryKey: ['transactions', merchant],
    queryFn: () => api.transactions({ merchant }),
    refetchInterval: REFRESH_MS,
  })
}

export const useCallbacks = () => {
  const merchant = useActiveMerchantKey()
  return useQuery({
    queryKey: ['callbacks', merchant],
    queryFn: () => api.callbacks({ merchant }),
    refetchInterval: REFRESH_MS,
  })
}

export const useRequestLog = () => {
  const merchant = useActiveMerchantKey()
  return useQuery({
    queryKey: ['requests', merchant],
    queryFn: () => api.requests({ merchant }),
    refetchInterval: REFRESH_MS,
  })
}

export const useTestCards = () =>
  useQuery({ queryKey: ['test-cards'], queryFn: () => api.testCards() })

function scoped<T>(key: string, fetch: (merchant: string | undefined) => Promise<T>) {
  return () => {
    const merchant = useActiveMerchantKey()
    return useQuery({ queryKey: [key, merchant], queryFn: () => fetch(merchant) })
  }
}

export const useSavedCards = scoped('saved-cards', (merchant) => api.savedCards({ merchant }))
export const useInvoices = scoped('invoices', (merchant) => api.invoices({ merchant }))
export const useBalance = scoped('balance', (merchant) => api.balance({ merchant }))
export const useNotifications = scoped('notifications', (merchant) =>
  api.notifications({ merchant }),
)
export const useB2B = scoped('b2b', (merchant) => api.b2b({ merchant }))
