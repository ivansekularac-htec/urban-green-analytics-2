import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError, apiFetch } from './api'

afterEach(() => {
  vi.restoreAllMocks()
  localStorage.clear()
})

describe('apiFetch', () => {
  it('sends the bearer token when one is stored', async () => {
    localStorage.setItem('token', 'abc')
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), { status: 200 }),
    )

    await apiFetch('/farms')

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/farms',
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: 'Bearer abc' }),
      }),
    )
  })

  it('throws ApiError on a non-OK response', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ detail: 'Nope' }), { status: 401 }),
    )

    await expect(apiFetch('/auth/me')).rejects.toMatchObject({
      status: 401,
      message: 'Nope',
    } satisfies Partial<ApiError>)
  })

  it('turns a validation error list into a readable message', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(
        JSON.stringify({ detail: [{ loc: ['body', 'email'], msg: 'invalid email' }] }),
        { status: 422 },
      ),
    )

    await expect(apiFetch('/users')).rejects.toMatchObject({
      status: 422,
      message: 'invalid email',
    } satisfies Partial<ApiError>)
  })
})
