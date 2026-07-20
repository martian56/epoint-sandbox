import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'

const ROOT = join(import.meta.dirname, '../../../..')

const SOURCE = join(ROOT, 'design-tokens.json')
const THEME = join(ROOT, 'apps/web/src/styles/theme.css')
const CHECKOUT = join(ROOT, 'apps/api/src/epoint_sandbox/web/static/tokens.css')

type Tokens = Record<string, Record<string, string>>

function expectedDeclarations(): string[] {
  const tokens = JSON.parse(readFileSync(SOURCE, 'utf8')) as Tokens
  const lines: string[] = []
  for (const [group, entries] of Object.entries(tokens)) {
    if (group.startsWith('$')) continue
    for (const [name, value] of Object.entries(entries)) {
      lines.push(`--${group}-${name}: ${value};`)
    }
  }
  return lines
}

describe('design tokens', () => {
  const declarations = expectedDeclarations()

  it('generates a declaration for every token', () => {
    expect(declarations.length).toBeGreaterThan(20)
  })

  it.each([
    ['tailwind theme', THEME],
    ['checkout stylesheet', CHECKOUT],
  ])('%s is up to date with design-tokens.json', (_label, path) => {
    const content = readFileSync(path, 'utf8')
    const missing = declarations.filter((line) => !content.includes(line))

    expect(missing, 'run `bun run tokens` to regenerate').toEqual([])
  })

  it('keeps both generated files carrying the same tokens', () => {
    const theme = readFileSync(THEME, 'utf8')
    const checkout = readFileSync(CHECKOUT, 'utf8')

    for (const line of declarations) {
      expect(theme.includes(line)).toBe(checkout.includes(line))
    }
  })

  it('applies the values measured from the epoint dashboard', () => {
    const raw = readFileSync(SOURCE, 'utf8')

    expect(raw).toContain('"tint-200": "#ffd8eb"')
    expect(raw).toContain('"canvas": "#fcfcfc"')
    expect(raw).toContain('"brand": "#b83b8c"')
    expect(raw).toContain('"card": "9px"')
  })
})
