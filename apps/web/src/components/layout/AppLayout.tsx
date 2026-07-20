import type { ReactNode } from 'react'
import { Outlet } from 'react-router'
import logoUrl from '@/assets/epoint-logo.svg'
import { Button } from '@/components/ui/Button'
import { useT } from '@/i18n'
import { useAuth } from '@/lib/auth'
import { Footer } from './Footer'
import { LanguageMenu, MerchantMenu } from './HeaderMenus'
import { MobileNav, Sidebar } from './Sidebar'

function AuthControl() {
  const t = useT()
  const { session, signOut } = useAuth()

  if (!session?.auth_required) {
    return (
      <span
        title={t.login.openAccessHint}
        className="rounded-pill bg-warning-tint px-2.5 py-1 font-medium text-warning-deep text-xs"
      >
        {t.login.openAccess}
      </span>
    )
  }

  return (
    <Button variant="ghost" onClick={() => void signOut()}>
      {t.login.signOut}
    </Button>
  )
}

function Header() {
  return (
    <header className="sticky top-0 z-30 flex h-[73px] items-center justify-between bg-surface px-8">
      <div className="flex items-center gap-3">
        <img src={logoUrl} alt="Epoint" className="h-[26px] w-auto" />
        <span className="rounded-pill bg-tint-200 px-2.5 py-1 text-xs font-bold text-brand-deep">
          SANDBOX
        </span>
      </div>

      <div className="flex items-center gap-2">
        <AuthControl />
        <LanguageMenu />
        <MerchantMenu />
      </div>
    </header>
  )
}

export function PageHeader({ title, actions }: { title: string; actions?: ReactNode }) {
  return (
    <div className="mb-5 flex flex-wrap items-center justify-between gap-4">
      <h1 className="text-[32px]/[48px] font-medium">{title}</h1>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  )
}

export function AppLayout() {
  return (
    <div className="min-h-screen bg-surface">
      <Header />
      {/* Sidebar and content share one surface, the way epoint's cabinet wrapper does. */}
      <div className="bg-canvas">
        <MobileNav />
        <div className="flex min-h-[calc(100vh-73px)]">
          <Sidebar />
          <main className="min-w-0 flex-1 px-8 py-6">
            <Outlet />
          </main>
        </div>
      </div>
      <Footer />
    </div>
  )
}
