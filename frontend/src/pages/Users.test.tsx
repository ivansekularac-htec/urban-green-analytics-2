import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { Users } from './Users'

afterEach(() => {
  vi.restoreAllMocks()
})

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status })
}

/** In-memory stand-in for the admin endpoints; POST /users adds to the list. */
function mockApi(options: { createResponse?: () => Response; assignResponse?: () => Response } = {}) {
  const users = [
    { id: 1, email: 'admin@example.com', full_name: 'System Administrator', is_active: true, roles: ['Admin'] },
    { id: 2, email: 'manager1@urbangreen.com', full_name: 'Farm Manager Demo', is_active: true, roles: ['Farm Manager'] },
  ]
  const roles = [
    { id: 1, name: 'Admin' },
    { id: 2, name: 'Farm Manager' },
    { id: 3, name: 'Operations Team' },
  ]
  const farms = [
    { id: 1, name: 'UG Farm 001' },
    { id: 2, name: 'UG Farm 002' },
  ]
  const userRoles = [
    { id: 1, user_id: 1, role_id: 1, farm_id: null },
    { id: 2, user_id: 2, role_id: 2, farm_id: 1 },
  ]

  return vi.spyOn(globalThis, 'fetch').mockImplementation(async (input, init) => {
    const [path] = String(input).split('?')
    if (init?.method === 'POST' && path === '/api/users') {
      if (options.createResponse) return options.createResponse()
      const body = JSON.parse(String(init.body))
      const created = { id: users.length + 1, email: body.email, full_name: body.full_name, is_active: true, roles: [] }
      users.push(created)
      return json(created, 201)
    }
    if (init?.method === 'POST' && path === '/api/user-roles') {
      return options.assignResponse?.() ?? json({ id: 99, ...JSON.parse(String(init.body)) }, 201)
    }
    const lists: Record<string, unknown[]> = {
      '/api/users': users,
      '/api/roles': roles,
      '/api/farms': farms,
      '/api/user-roles': userRoles,
    }
    return lists[path] ? json(lists[path]) : json({ detail: 'Not found' }, 404)
  })
}

function postedBody(fetchMock: ReturnType<typeof mockApi>, path: string) {
  const call = fetchMock.mock.calls.find(([input, init]) => init?.method === 'POST' && String(input) === path)
  return call ? JSON.parse(String(call[1]?.body)) : undefined
}

async function renderUsers() {
  render(
    <MemoryRouter>
      <Users />
    </MemoryRouter>,
  )
  await screen.findByText('Farm Manager Demo', { selector: 'p' })
}

describe('Users', () => {
  it('lists users with their role and farm assignments', async () => {
    mockApi()
    await renderUsers()

    const table = within(screen.getByRole('table'))
    expect(table.getByText('admin@example.com')).toBeInTheDocument()
    expect(table.getByText('Admin')).toBeInTheDocument()
    expect(table.getByText('Farm Manager · UG Farm 001')).toBeInTheDocument()
  })

  it('creates a user and preselects them for assignment', async () => {
    const fetchMock = mockApi()
    await renderUsers()
    const user = userEvent.setup()

    await user.type(screen.getByLabelText('Email'), 'new@urbangreen.com')
    await user.type(screen.getByLabelText('Full name'), 'New Manager')
    await user.type(screen.getByLabelText('Password'), 'secret123')
    await user.click(screen.getByRole('button', { name: 'Create user' }))

    expect(await within(screen.getByRole('table')).findByText('new@urbangreen.com')).toBeInTheDocument()
    expect(postedBody(fetchMock, '/api/users')).toEqual({
      email: 'new@urbangreen.com',
      full_name: 'New Manager',
      password: 'secret123',
    })
    expect(screen.getByLabelText('User')).toHaveValue('3')
  })

  it('explains a conflict on create as a taken email', async () => {
    mockApi({ createResponse: () => json({ detail: 'User violates a database constraint.' }, 409) })
    await renderUsers()
    const user = userEvent.setup()

    await user.type(screen.getByLabelText('Email'), 'manager1@urbangreen.com')
    await user.type(screen.getByLabelText('Full name'), 'Duplicate')
    await user.type(screen.getByLabelText('Password'), 'secret123')
    await user.click(screen.getByRole('button', { name: 'Create user' }))

    expect(await screen.findByRole('status')).toHaveTextContent(/email already exists/i)
  })

  it('assigns a role on a farm through POST /user-roles', async () => {
    const fetchMock = mockApi()
    await renderUsers()
    const user = userEvent.setup()

    await user.selectOptions(screen.getByLabelText('User'), '2')
    await user.selectOptions(screen.getByLabelText('Role'), '2')
    await user.selectOptions(screen.getByLabelText('Farm'), '2')
    await user.click(screen.getByRole('button', { name: 'Assign' }))

    await screen.findByRole('status')
    expect(postedBody(fetchMock, '/api/user-roles')).toEqual({ user_id: 2, role_id: 2, farm_id: 2 })
  })

  it('sends no farm for the Admin role', async () => {
    const fetchMock = mockApi()
    await renderUsers()
    const user = userEvent.setup()

    await user.selectOptions(screen.getByLabelText('User'), '2')
    await user.selectOptions(screen.getByLabelText('Role'), '1')
    expect(screen.getByLabelText('Farm')).toBeDisabled()
    await user.click(screen.getByRole('button', { name: 'Assign' }))

    await screen.findByRole('status')
    expect(postedBody(fetchMock, '/api/user-roles')).toEqual({ user_id: 2, role_id: 1, farm_id: null })
  })

  it('does not offer an assignment the user already has', async () => {
    mockApi()
    await renderUsers()
    const user = userEvent.setup()

    await user.selectOptions(screen.getByLabelText('User'), '2')
    await user.selectOptions(screen.getByLabelText('Role'), '2')
    await user.selectOptions(screen.getByLabelText('Farm'), '1')

    expect(screen.getByRole('button', { name: 'Assign' })).toBeDisabled()
  })

  it('shows the API error when an assignment is rejected', async () => {
    mockApi({ assignResponse: () => json({ detail: 'User role already exists.' }, 409) })
    await renderUsers()
    const user = userEvent.setup()

    await user.selectOptions(screen.getByLabelText('User'), '2')
    await user.selectOptions(screen.getByLabelText('Role'), '3')
    await user.selectOptions(screen.getByLabelText('Farm'), '2')
    await user.click(screen.getByRole('button', { name: 'Assign' }))

    expect(await screen.findByRole('status')).toHaveTextContent('User role already exists.')
  })
})
