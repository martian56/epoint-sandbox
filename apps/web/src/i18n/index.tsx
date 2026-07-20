import { createContext, type ReactNode, use, useCallback, useMemo, useState } from 'react'
import { az } from './az'
import { type Dictionary, en } from './en'

export const LOCALES = ['en', 'az'] as const
export type Locale = (typeof LOCALES)[number]

const DICTIONARIES: Record<Locale, Dictionary> = { en, az }
const STORAGE_KEY = 'epoint-sandbox.locale'

function isLocale(value: unknown): value is Locale {
  return LOCALES.includes(value as Locale)
}

function readStoredLocale(): Locale {
  if (typeof localStorage === 'undefined') return 'en'
  const stored = localStorage.getItem(STORAGE_KEY)
  return isLocale(stored) ? stored : 'en'
}

interface I18nValue {
  locale: Locale
  setLocale: (locale: Locale) => void
  t: Dictionary
}

const I18nContext = createContext<I18nValue | null>(null)

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(readStoredLocale)

  const setLocale = useCallback((next: Locale) => {
    setLocaleState(next)
    localStorage.setItem(STORAGE_KEY, next)
    document.documentElement.lang = next
  }, [])

  const value = useMemo(() => ({ locale, setLocale, t: DICTIONARIES[locale] }), [locale, setLocale])

  return <I18nContext value={value}>{children}</I18nContext>
}

export function useI18n(): I18nValue {
  const value = use(I18nContext)
  if (!value) throw new Error('useI18n must be used inside I18nProvider')
  return value
}

/** For components that only need the strings. */
export function useT(): Dictionary {
  return useI18n().t
}
