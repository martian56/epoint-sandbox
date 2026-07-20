import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { type RenderOptions, render } from '@testing-library/react'
import type { ReactElement, ReactNode } from 'react'
import { I18nProvider } from '@/i18n'
import { MerchantProvider } from '@/lib/merchant'

function Providers({ children }: { children: ReactNode }) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })

  return (
    <QueryClientProvider client={queryClient}>
      <I18nProvider>
        <MerchantProvider>{children}</MerchantProvider>
      </I18nProvider>
    </QueryClientProvider>
  )
}

export function renderWithProviders(ui: ReactElement, options?: RenderOptions) {
  return render(ui, { wrapper: Providers, ...options })
}

export * from '@testing-library/react'
