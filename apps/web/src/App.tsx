import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Route, Routes } from 'react-router'
import { AppLayout } from '@/components/layout/AppLayout'
import { I18nProvider } from '@/i18n'
import { AuthProvider, useAuth } from '@/lib/auth'
import { MerchantProvider } from '@/lib/merchant'
import { ApiManagementPage } from '@/pages/ApiManagementPage'
import { BalancePage } from '@/pages/BalancePage'
import { BankTransfersPage } from '@/pages/BankTransfersPage'
import { CallbacksPage } from '@/pages/CallbacksPage'
import { CardsPage } from '@/pages/CardsPage'
import { InvoicesPage } from '@/pages/InvoicesPage'
import { LoginPage } from '@/pages/LoginPage'
import { RequestLogPage } from '@/pages/RequestLogPage'
import { SignaturePage } from '@/pages/SignaturePage'
import { TestCardsPage } from '@/pages/TestCardsPage'
import { TransactionsPage } from '@/pages/TransactionsPage'

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
})

function Dashboard() {
  return (
    <MerchantProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<AppLayout />}>
            <Route index element={<TransactionsPage />} />
            <Route path="balance" element={<BalancePage />} />
            <Route path="cards" element={<CardsPage />} />
            <Route path="invoices" element={<InvoicesPage />} />
            <Route path="bank-transfers" element={<BankTransfersPage />} />
            <Route path="api-management" element={<ApiManagementPage />} />
            <Route path="callbacks" element={<CallbacksPage />} />
            <Route path="requests" element={<RequestLogPage />} />
            <Route path="test-cards" element={<TestCardsPage />} />
            <Route path="signature" element={<SignaturePage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </MerchantProvider>
  )
}

function Gate() {
  const { session, loading } = useAuth()

  if (loading) return <div className="min-h-screen bg-canvas" />
  if (session?.auth_required && !session.authenticated) return <LoginPage />
  return <Dashboard />
}

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <I18nProvider>
        <AuthProvider>
          <Gate />
        </AuthProvider>
      </I18nProvider>
    </QueryClientProvider>
  )
}
