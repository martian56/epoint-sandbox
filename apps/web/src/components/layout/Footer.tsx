import logoUrl from '@/assets/epoint-logo.svg'
import { useT } from '@/i18n'
import type { Dictionary } from '@/i18n/en'

function buildColumns(t: Dictionary) {
  return [
    {
      heading: t.footer.sandbox,
      links: [
        { label: t.nav.transactions, href: '/' },
        { label: t.nav.callbacks, href: '/callbacks' },
        { label: t.nav.requestLog, href: '/requests' },
        { label: t.nav.signatureTool, href: '/signature' },
      ],
    },
    {
      heading: t.footer.reference,
      links: [
        { label: t.common.apiReference, href: '/docs' },
        { label: t.footer.openapi, href: '/openapi.json' },
        { label: t.nav.testCards, href: '/test-cards' },
        { label: t.footer.developerPortal, href: 'https://developer.epoint.az' },
      ],
    },
  ]
}

export function Footer() {
  const t = useT()
  const columns = buildColumns(t)

  return (
    <>
      <footer className="bg-tint-100 px-8 pt-16 pb-10">
        <div className="mx-auto grid max-w-6xl gap-10 lg:grid-cols-[2fr_1fr_1fr_1.2fr]">
          <div>
            <img src={logoUrl} alt="Epoint" className="mb-4 h-[34px] w-auto" />
            <p className="max-w-xs text-body">{t.footer.blurb}</p>
          </div>

          {columns.map((column) => (
            <nav key={column.heading} aria-label={column.heading}>
              <p className="mb-4 font-bold">{column.heading}</p>
              <ul className="grid gap-3">
                {column.links.map((link) => (
                  <li key={link.href}>
                    <a href={link.href} className="text-body hover:text-brand">
                      {link.label}
                    </a>
                  </li>
                ))}
              </ul>
            </nav>
          ))}

          <div>
            <p className="mb-4 font-bold">{t.footer.baseUrl}</p>
            <code className="block rounded-field bg-surface px-3 py-2 font-mono text-xs">
              http://localhost:8181/api/1/
            </code>
            <p className="mt-4 text-muted text-xs">{t.footer.callbackNote}</p>
          </div>
        </div>
      </footer>

      <div className="bg-black px-8 py-4 text-center text-white">{t.footer.legal}</div>
    </>
  )
}
