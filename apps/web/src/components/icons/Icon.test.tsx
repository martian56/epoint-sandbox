import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { NAV_GROUPS } from '@/components/layout/navigation'
import { Icon } from './Icon'
import { ICON_PATHS } from './paths'

describe('Icon', () => {
  it('renders a path for a known name', () => {
    const { container } = render(<Icon name="analytics" />)
    const path = container.querySelector('path')

    expect(path).toBeInTheDocument()
    expect(path?.getAttribute('d')).toBe(ICON_PATHS.analytics)
  })

  it('is hidden from assistive tech', () => {
    const { container } = render(<Icon name="analytics" />)
    expect(container.querySelector('svg')).toHaveAttribute('aria-hidden', 'true')
  })

  it('honours the size prop', () => {
    const { container } = render(<Icon name="settings" size={18} />)
    const svg = container.querySelector('svg')

    expect(svg).toHaveAttribute('width', '18')
    expect(svg).toHaveAttribute('height', '18')
  })

  it('has a non-empty path for every extracted glyph', () => {
    for (const [name, path] of Object.entries(ICON_PATHS)) {
      expect(path.length, `${name} has an empty path`).toBeGreaterThan(20)
    }
  })

  it('covers every icon the navigation references', () => {
    for (const group of NAV_GROUPS) {
      for (const item of group.items) {
        expect(ICON_PATHS[item.icon], `${item.labelKey} icon missing`).toBeDefined()
      }
    }
  })
})
