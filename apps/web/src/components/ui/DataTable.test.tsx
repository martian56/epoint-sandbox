import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { renderWithProviders as render, screen, within } from '@/test/render'
import { type Column, DataTable } from './DataTable'

interface Row {
  id: string
  name: string
  secret: string
}

const ROWS: Row[] = [
  { id: '1', name: 'Alpha', secret: 'hidden-alpha' },
  { id: '2', name: 'Beta', secret: 'hidden-beta' },
]

const COLUMNS: Column<Row>[] = [
  { key: 'name', header: 'Name', priority: 1, minWidth: 100, render: (r) => r.name },
  { key: 'secret', header: 'Secret', priority: 9, minWidth: 5000, render: (r) => r.secret },
]

function setup(rows = ROWS) {
  return render(<DataTable columns={COLUMNS} rows={rows} getRowKey={(r) => r.id} />)
}

function expandButton(index = 0) {
  const button = screen.getAllByRole('button', { name: 'Expand row' })[index]
  if (!button) throw new Error(`No expand button at index ${index}`)
  return button
}

describe('DataTable', () => {
  it('renders a row per record', () => {
    setup()
    expect(screen.getByText('Alpha')).toBeInTheDocument()
    expect(screen.getByText('Beta')).toBeInTheDocument()
  })

  it('shows the empty message when there are no rows', () => {
    render(
      <DataTable
        columns={COLUMNS}
        rows={[]}
        getRowKey={(r: Row) => r.id}
        emptyMessage="Nothing here"
      />,
    )
    expect(screen.getByText('Nothing here')).toBeInTheDocument()
  })

  it('collapses low priority columns that do not fit', () => {
    setup()
    expect(screen.queryByRole('columnheader', { name: 'Secret' })).not.toBeInTheDocument()
  })

  it('reveals collapsed columns when a row is expanded', async () => {
    const user = userEvent.setup()
    setup()

    expect(screen.queryByText('hidden-alpha')).not.toBeInTheDocument()

    await user.click(expandButton())

    expect(screen.getByText('hidden-alpha')).toBeInTheDocument()
    expect(screen.queryByText('hidden-beta')).not.toBeInTheDocument()
  })

  it('collapses an expanded row again', async () => {
    const user = userEvent.setup()
    setup()

    await user.click(expandButton())
    await user.click(screen.getByRole('button', { name: 'Collapse row' }))

    expect(screen.queryByText('hidden-alpha')).not.toBeInTheDocument()
  })

  it('renders the footer when provided', () => {
    render(
      <DataTable
        columns={COLUMNS}
        rows={ROWS}
        getRowKey={(r) => r.id}
        footer={<span>Total: 2</span>}
      />,
    )
    expect(screen.getByText('Total: 2')).toBeInTheDocument()
  })

  it('keeps each row independent', async () => {
    const user = userEvent.setup()
    setup()

    await user.click(expandButton(1))

    const table = screen.getByRole('table')
    expect(within(table).getByText('hidden-beta')).toBeInTheDocument()
    expect(within(table).queryByText('hidden-alpha')).not.toBeInTheDocument()
  })
})
