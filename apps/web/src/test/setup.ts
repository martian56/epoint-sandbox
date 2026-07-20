import '@testing-library/jest-dom/vitest'

declare global {
  var testContainerWidth: number
}

globalThis.testContainerWidth = 400

/** Reports a fixed width so column collapsing is exercised. */
class ResizeObserverStub {
  constructor(private callback: ResizeObserverCallback) {}

  observe(target: Element) {
    this.callback(
      [{ target, contentRect: { width: globalThis.testContainerWidth } } as ResizeObserverEntry],
      this as unknown as ResizeObserver,
    )
  }

  unobserve() {}
  disconnect() {}
}

globalThis.ResizeObserver = ResizeObserverStub as unknown as typeof ResizeObserver
