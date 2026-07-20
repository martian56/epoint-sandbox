import { type ReactNode, useEffect, useRef, useState } from 'react'
import { LOCALES, type Locale, useI18n } from '@/i18n'
import { cx } from '@/lib/cx'
import { useMerchant } from '@/lib/merchant'

function useDismissOnOutsideClick(onDismiss: () => void) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handler = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) onDismiss()
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [onDismiss])

  return ref
}

interface DropdownProps {
  label: ReactNode
  children: (close: () => void) => ReactNode
  align?: 'left' | 'right'
}

/** Matches epoint's .drop-lg. */
function Dropdown({ label, children, align = 'right' }: DropdownProps) {
  const [open, setOpen] = useState(false)
  const ref = useDismissOnOutsideClick(() => setOpen(false))

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
        className="flex items-center gap-2 rounded-pill px-2 py-1.5 hover:bg-tint-50"
      >
        {label}
        <span aria-hidden className="text-muted text-xs">
          ▾
        </span>
      </button>

      {open && (
        <div
          className={cx(
            'absolute top-full z-20 mt-2 min-w-[220px] rounded-field bg-surface p-1',
            'shadow-dropdown border border-line',
            align === 'right' ? 'right-0' : 'left-0',
          )}
        >
          {children(() => setOpen(false))}
        </div>
      )}
    </div>
  )
}

export function LanguageMenu() {
  const { locale, setLocale } = useI18n()

  return (
    <Dropdown label={<span className="font-medium uppercase">{locale}</span>}>
      {(close) =>
        LOCALES.map((code: Locale) => (
          <button
            key={code}
            type="button"
            onClick={() => {
              setLocale(code)
              close()
            }}
            className={cx(
              'block w-full rounded-field px-3 py-2 text-left uppercase hover:bg-tint-50',
              code === locale && 'text-brand-bright font-medium',
            )}
          >
            {code}
          </button>
        ))
      }
    </Dropdown>
  )
}

export function MerchantMenu() {
  const { merchants, active, setActive } = useMerchant()

  return (
    <Dropdown
      label={
        <>
          <span className="flex h-9 w-9 items-center justify-center rounded-pill bg-tint-100 font-bold text-brand-deep">
            {active?.name.charAt(0) ?? 'S'}
          </span>
          <span className="hidden sm:inline font-medium">{active?.name ?? 'Merchant'}</span>
        </>
      }
    >
      {(close) =>
        merchants.map((merchant) => (
          <button
            key={merchant.public_key}
            type="button"
            onClick={() => {
              setActive(merchant.public_key)
              close()
            }}
            className={cx(
              'block w-full rounded-field px-3 py-2 text-left hover:bg-tint-50',
              merchant.public_key === active?.public_key && 'bg-tint-50',
            )}
          >
            <span
              className={cx(
                'block font-medium',
                merchant.public_key === active?.public_key && 'text-brand-bright',
              )}
            >
              {merchant.name}
            </span>
            <span className="block font-mono text-muted text-xs">{merchant.public_key}</span>
          </button>
        ))
      }
    </Dropdown>
  )
}
