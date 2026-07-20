import { NavLink, useLocation } from 'react-router'
import { Icon } from '@/components/icons/Icon'
import { useT } from '@/i18n'
import { cx } from '@/lib/cx'
import { NAV_GROUPS, type NavItem } from './navigation'

// Metrics measured from the epoint dashboard.
function Item({ item, onNavigate }: { item: NavItem; onNavigate?: () => void }) {
  const t = useT()

  return (
    <li>
      <NavLink to={item.to} end={item.to === '/'} onClick={onNavigate}>
        {({ isActive }) => (
          <span
            className={cx(
              'flex items-center h-10 pl-[34px] pr-[15px] text-[16px]/[24px]',
              'rounded-r-[24px] transition-colors',
              isActive ? 'bg-tint-200 text-brand-deep' : 'text-ink hover:bg-tint-50',
            )}
          >
            <Icon name={item.icon} size={18} className="mr-[15px] shrink-0" />
            {t.nav[item.labelKey]}
          </span>
        )}
      </NavLink>
    </li>
  )
}

function NavItems({ onNavigate }: { onNavigate?: () => void }) {
  const t = useT()

  return (
    <>
      {NAV_GROUPS.map((group, index) => (
        <div
          key={group.labelKey ?? index}
          className={index > 0 ? 'mt-5 pt-5 mr-[15px] border-t border-line' : ''}
        >
          {group.labelKey && (
            <p className="pl-[34px] pb-2 text-xs font-bold uppercase tracking-wide text-subtle">
              {t.nav[group.labelKey]}
            </p>
          )}
          <ul>
            {group.items.map((item) => (
              <Item key={item.to} item={item} onNavigate={onNavigate} />
            ))}
          </ul>
        </div>
      ))}
    </>
  )
}

export function Sidebar() {
  return (
    <nav aria-label="Main" className="hidden lg:block w-[240px] shrink-0 py-6">
      <NavItems />
    </nav>
  )
}

export function MobileNav() {
  const t = useT()
  const location = useLocation()
  const current = NAV_GROUPS.flatMap((g) => g.items).find((i) => i.to === location.pathname)

  return (
    <details className="lg:hidden mx-6 mt-4 rounded-field border border-line bg-surface">
      <summary className="flex h-[46px] cursor-pointer items-center gap-3 px-4 font-medium">
        {current && <Icon name={current.icon} className="shrink-0 text-brand-bright" />}
        <span className="flex-1">{current ? t.nav[current.labelKey] : t.nav.menu}</span>
        <span aria-hidden className="text-muted">
          ▾
        </span>
      </summary>
      <div className="pb-3">
        <NavItems />
      </div>
    </details>
  )
}
