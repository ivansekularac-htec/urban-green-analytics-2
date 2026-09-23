import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { Home } from './Home'

afterEach(() => {
  vi.restoreAllMocks()
})

function renderHome() {
  return render(
    <MemoryRouter>
      <Home />
    </MemoryRouter>,
  )
}

describe('Home', () => {
  it('lists farms returned by the API', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify([{ id: 1, name: 'UG Farm 001', city: 'Berlin', status: 'ACTIVE' }]),
        { status: 200 },
      ),
    )

    renderHome()

    expect(await screen.findByText('UG Farm 001')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /UG Farm 001/ })).toHaveAttribute('href', '/farms/1')
  })

  it('shows an empty state when the user has no farms', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify([]), { status: 200 }),
    )

    renderHome()

    expect(await screen.findByText('No farms assigned.')).toBeInTheDocument()
  })
})