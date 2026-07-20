const CURRENCY_SYMBOLS: Record<string, string> = {
  AZN: '₼',
  USD: '$',
  EUR: '€',
  RUB: '₽',
}

export function money(amount: number, currency = 'AZN'): string {
  const symbol = CURRENCY_SYMBOLS[currency] ?? currency
  return `${symbol} ${amount.toFixed(2)}`
}

export function timestamp(iso: string): string {
  const date = new Date(iso)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${pad(date.getDate())}-${pad(date.getMonth() + 1)}-${date.getFullYear()} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

export function duration(ms: number | null): string {
  if (ms === null) return '-'
  return ms < 1000 ? `${ms}ms` : `${(ms / 1000).toFixed(2)}s`
}

export function truncate(value: string, max = 32): string {
  return value.length <= max ? value : `${value.slice(0, max)}…`
}
