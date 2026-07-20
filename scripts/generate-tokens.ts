/** Generates the Tailwind theme and the checkout stylesheet from design-tokens.json. */
import { readFileSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'

const ROOT = join(import.meta.dir, '..')
const SOURCE = join(ROOT, 'design-tokens.json')

const THEME_OUT = join(ROOT, 'apps/web/src/styles/theme.css')
const CHECKOUT_OUT = join(ROOT, 'apps/api/src/epoint_sandbox/web/static/tokens.css')

const BANNER = '/* Generated from design-tokens.json. Run `bun run tokens` to update. */'

type Tokens = Record<string, Record<string, string>>

function declarations(tokens: Tokens): string[] {
  const lines: string[] = []
  for (const [group, entries] of Object.entries(tokens)) {
    if (group.startsWith('$')) continue
    lines.push('')
    for (const [name, value] of Object.entries(entries)) {
      lines.push(`  --${group}-${name}: ${value};`)
    }
  }
  return lines
}

const tokens = JSON.parse(readFileSync(SOURCE, 'utf8')) as Tokens
const body = declarations(tokens).join('\n')

writeFileSync(THEME_OUT, `${BANNER}\n\n@theme {${body}\n}\n`)
writeFileSync(CHECKOUT_OUT, `${BANNER}\n\n:root {${body}\n}\n`)

const count = Object.entries(tokens)
  .filter(([group]) => !group.startsWith('$'))
  .reduce((total, [, entries]) => total + Object.keys(entries).length, 0)

console.log(`Wrote ${count} tokens to:`)
console.log(`  ${THEME_OUT}`)
console.log(`  ${CHECKOUT_OUT}`)
