import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { Navbar } from './Navbar'

vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({
    user: { full_name: 'Farm Manager Demo', email: 'm@x.com', roles: ['Farm Manager'] },
    logout: vi.fn(),
  }),
}))

describe('Navbar', () => {
  it('shows Home and Dashboards for a farm manager', () => {
    render(
      <MemoryRouter>
        <Navbar />
      </MemoryRouter>,
    )
    expect(screen.getByRole('link', { name: 'Home' })).toBeInTheDocument()
    const dashboards = screen.getByRole('link', { name: 'Dashboards' })
    expect(dashboards).toHaveAttribute('href', 'http://localhost:8088')
    expect(dashboards).toHaveAttribute('target', '_blank')
    expect(screen.queryByRole('link', { name: 'Users' })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: 'Monitoring' })).not.toBeInTheDocument()
  })
})