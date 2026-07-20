import { describe, expect, it } from 'vitest'
import { duration, money, timestamp, truncate } from './format'

describe('money', () => {
  it('prefixes AZN with the manat sign', () => {
    expect(money(7.01)).toBe('₼ 7.01')
  })

  it('always shows two decimals', () => {
    expect(money(5)).toBe('₼ 5.00')
  })

  it('handles negative amounts used for fees', () => {
    expect(money(-0.01)).toBe('₼ -0.01')
  })

  it('falls back to the code for unmapped currencies', () => {
    expect(money(10, 'GBP')).toBe('GBP 10.00')
  })

  it('maps the other supported currencies', () => {
    expect(money(1, 'USD')).toBe('$ 1.00')
    expect(money(1, 'EUR')).toBe('€ 1.00')
  })
})

describe('timestamp', () => {
  it('formats as DD-MM-YYYY HH:mm', () => {
    expect(timestamp('2026-03-24T13:58:00')).toBe('24-03-2026 13:58')
  })

  it('pads single digit parts', () => {
    expect(timestamp('2026-01-05T09:07:00')).toBe('05-01-2026 09:07')
  })
})

describe('duration', () => {
  it('shows milliseconds below a second', () => {
    expect(duration(250)).toBe('250ms')
  })

  it('switches to seconds at a second or more', () => {
    expect(duration(1500)).toBe('1.50s')
  })

  it('renders a dash when missing', () => {
    expect(duration(null)).toBe('-')
  })
})

describe('truncate', () => {
  it('leaves short values alone', () => {
    expect(truncate('short', 10)).toBe('short')
  })

  it('appends an ellipsis when cutting', () => {
    expect(truncate('abcdefghij', 4)).toBe('abcd…')
  })
})
