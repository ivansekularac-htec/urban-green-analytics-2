import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { RequireRole } from './RequireRole'

const auth = vi.hoisted(() => ({ user: null as { roles: string[] } | null }))

vi.mock('../context/AuthContext', () => ({
  useAuth: () => auth,
}))

afterEach(() => {
  auth.user = null
})

function renderUsersRoute() {
  return render(
    <MemoryRouter initialEntries={['/users']}>
      <Routes>
        <Route path="/" element={<div>Home page</div>} />
        <Route
          path="/users"
          element={
            <RequireRole role="Admin">
              <div>Admin page</div>
            </RequireRole>
          }
        />
      </Routes>
    </MemoryRouter>,
  )
}

describe('RequireRole', () => {
  it('renders the page for a user with the role', () => {
    auth.user = { roles: ['Admin'] }
    renderUsersRoute()
    expect(screen.getByText('Admin page')).toBeInTheDocument()
  })

  it('redirects a user without the role to Home', () => {
    auth.user = { roles: ['Farm Manager'] }
    renderUsersRoute()
    expect(screen.getByText('Home page')).toBeInTheDocument()
    expect(screen.queryByText('Admin page')).not.toBeInTheDocument()
  })
})
