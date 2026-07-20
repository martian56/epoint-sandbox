import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it } from 'vitest'
import { az } from './az'
import { en } from './en'
import { I18nProvider, LOCALES, useI18n, useT } from './index'

function Probe() {
  const { locale, setLocale } = useI18n()
  const t = useT()

  return (
    <div>
      <span data-testid="locale">{locale}</span>
      <span data-testid="title">{t.transactions.title}</span>
      <button type="button" onClick={() => setLocale('az')}>
        switch
      </button>
    </div>
  )
}

function keyPaths(value: unknown, prefix = ''): string[] {
  if (typeof value !== 'object' || value === null) return [prefix]
  return Object.entries(value).flatMap(([key, child]) =>
    keyPaths(child, prefix ? `${prefix}.${key}` : key),
  )
}

describe('dictionaries', () => {
  it('define the same key set', () => {
    expect(keyPaths(az).sort()).toEqual(keyPaths(en).sort())
  })

  it('leave no value empty', () => {
    const walk = (value: unknown, path: string) => {
      if (typeof value === 'string') {
        expect(value.trim(), `${path} is empty`).not.toBe('')
        return
      }
      for (const [key, child] of Object.entries(value as object)) {
        walk(child, path ? `${path}.${key}` : key)
      }
    }

    for (const dictionary of [en, az]) walk(dictionary, '')
  })

  it('actually translate the navigation rather than copying English', () => {
    const shared = Object.keys(en.nav).filter(
      (key) => en.nav[key as keyof typeof en.nav] === az.nav[key as keyof typeof az.nav],
    )
    // Sandbox is a loanword in both.
    expect(shared).toEqual([])
  })

  it('uses epoint own Azerbaijani terms where they were captured', () => {
    expect(az.nav.cards).toBe('Kartlar / Hesablar')
    expect(az.nav.invoices).toBe('Link ilə Ödəniş')
    expect(az.nav.apiManagement).toBe('API Idarəetmə')
    expect(az.transactions.sum).toBe('Məbləğ')
    expect(az.transactions.date).toBe('Tarix')
  })
})

describe('I18nProvider', () => {
  beforeEach(() => localStorage.clear())

  it('starts in English', () => {
    render(
      <I18nProvider>
        <Probe />
      </I18nProvider>,
    )
    expect(screen.getByTestId('locale')).toHaveTextContent('en')
    expect(screen.getByTestId('title')).toHaveTextContent(en.transactions.title)
  })

  it('switches locale and swaps the strings', async () => {
    const user = userEvent.setup()
    render(
      <I18nProvider>
        <Probe />
      </I18nProvider>,
    )

    await user.click(screen.getByRole('button', { name: 'switch' }))

    expect(screen.getByTestId('locale')).toHaveTextContent('az')
    expect(screen.getByTestId('title')).toHaveTextContent(az.transactions.title)
  })

  it('persists the choice', async () => {
    const user = userEvent.setup()
    render(
      <I18nProvider>
        <Probe />
      </I18nProvider>,
    )

    await user.click(screen.getByRole('button', { name: 'switch' }))
    expect(localStorage.getItem('epoint-sandbox.locale')).toBe('az')
  })

  it('restores a stored locale on mount', () => {
    localStorage.setItem('epoint-sandbox.locale', 'az')
    render(
      <I18nProvider>
        <Probe />
      </I18nProvider>,
    )
    expect(screen.getByTestId('locale')).toHaveTextContent('az')
  })

  it('falls back to English for an unrecognised stored value', () => {
    localStorage.setItem('epoint-sandbox.locale', 'fr')
    render(
      <I18nProvider>
        <Probe />
      </I18nProvider>,
    )
    expect(screen.getByTestId('locale')).toHaveTextContent('en')
  })

  it('exposes exactly the locales the dashboard supports', () => {
    expect([...LOCALES]).toEqual(['en', 'az'])
  })
})
