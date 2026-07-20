import type { IconName } from '@/components/icons/Icon'
import type { Dictionary } from '@/i18n/en'

type NavKey = keyof Dictionary['nav']

export interface NavItem {
  to: string
  labelKey: NavKey
  icon: IconName
}

export interface NavGroup {
  labelKey?: NavKey
  items: NavItem[]
}

/** The second group has no counterpart in epoint. */
export const NAV_GROUPS: NavGroup[] = [
  {
    items: [
      { to: '/', labelKey: 'transactions', icon: 'analytics' },
      { to: '/balance', labelKey: 'balance', icon: 'reports' },
      { to: '/cards', labelKey: 'cards', icon: 'bankCards' },
      { to: '/invoices', labelKey: 'invoices', icon: 'invoices' },
      { to: '/bank-transfers', labelKey: 'bankTransfers', icon: 'sign' },
      { to: '/api-management', labelKey: 'apiManagement', icon: 'apiConnection' },
    ],
  },
  {
    labelKey: 'sandboxTools',
    items: [
      { to: '/callbacks', labelKey: 'callbacks', icon: 'mail' },
      { to: '/requests', labelKey: 'requestLog', icon: 'sign' },
      { to: '/test-cards', labelKey: 'testCards', icon: 'subscribe' },
      { to: '/signature', labelKey: 'signatureTool', icon: 'settings' },
    ],
  },
]
