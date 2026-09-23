import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { Profile } from './Profile'

vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({
    user: {
      id: 1,
      email: 'manager1@urbangreen.com',
      full_name: 'Farm Manager Demo',
      is_active: true,
      roles: ['Farm Manager'],
    },
  }),
}))

describe('Profile', () => {
  it('shows name, email, and role', () => {
    render(<Profile />)
    expect(screen.getByText('Farm Manager Demo')).toBeInTheDocument()
    expect(screen.getByText('manager1@urbangreen.com')).toBeInTheDocument()
    expect(screen.getAllByText('Farm Manager').length).toBeGreaterThan(0)
  })
})