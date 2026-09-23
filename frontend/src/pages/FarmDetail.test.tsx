import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { FarmDetail } from './FarmDetail'

afterEach(() => {
  vi.restoreAllMocks()
})

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status })
}

function mockFarm() {
  vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
    const url = String(input)
    if (url.includes('/harvests')) {
      return json([
        { id: 5, farm_id: 1, crop_id: 1, weight_kg: '3', created_at: 1700000000 },
        { id: 6, farm_id: 1, crop_id: 2, weight_kg: '4', created_at: 1700000000 },
      ])
    }
    if (url.includes('/farm-crops')) {
      return json([
        { id: 10, farm_id: 1, crop_id: 1, started_at: 1700000000 },
        { id: 11, farm_id: 1, crop_id: 2, started_at: 1700000000 },
      ])
    }
    if (url.includes('/crops')) {
      return json([
        { id: 1, name: 'Basil' },
        { id: 2, name: 'Mint' },
      ])
    }
    if (url.includes('/farms/1')) {
      return json({ id: 1, name: 'UG Farm 001', city: 'Berlin' })
    }
    return json({ detail: 'Not found.' }, 404)
  })
}

function renderFarm(path: string) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/farms/:farmId" element={<FarmDetail />} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('FarmDetail', () => {
  it('shows the farm, its crops, and grouped harvests', async () => {
    mockFarm()
    renderFarm('/farms/1')

    expect(await screen.findByRole('heading', { name: 'UG Farm 001' })).toBeInTheDocument()
    expect(await screen.findByRole('button', { name: /Basil/ })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Mint/ })).toBeInTheDocument()
    expect(await screen.findByText(/1 harvests · 3 kg/)).toBeInTheDocument()
  })

  it('filters crops and harvests by crop name in the browser', async () => {
    mockFarm()
    renderFarm('/farms/1')
    const user = userEvent.setup()

    await screen.findByRole('button', { name: /Mint/ })
    await user.type(screen.getByPlaceholderText('Crop name'), 'Basil')

    expect(screen.getByRole('button', { name: /Basil/ })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Mint/ })).not.toBeInTheDocument()
    expect(screen.getByText(/1 harvests · 3 kg/)).toBeInTheDocument()
    expect(screen.queryByText(/1 harvests · 4 kg/)).not.toBeInTheDocument()
  })
})