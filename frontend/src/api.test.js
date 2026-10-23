import { afterEach, describe, expect, it, vi } from 'vitest'
import { createCard, deleteCard, getBoard, moveCard, updateCard } from './api'

function mockFetch(status, body) {
  const fetchMock = vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(body),
    text: () => Promise.resolve(JSON.stringify(body)),
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

afterEach(() => vi.unstubAllGlobals())

describe('api', () => {
  it('loads the board from the same-origin /api prefix', async () => {
    const fetchMock = mockFetch(200, { columns: [], cards: [] })
    await expect(getBoard()).resolves.toEqual({ columns: [], cards: [] })
    expect(fetchMock).toHaveBeenCalledWith('/api/board', expect.any(Object))
  })

  it('creates a card in the requested column', async () => {
    const fetchMock = mockFetch(201, { id: '1', title: 'A', description: '', column: 'todo' })
    await createCard({ title: 'A', column: 'todo' })
    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/cards')
    expect(options.method).toBe('POST')
    expect(JSON.parse(options.body)).toEqual({ title: 'A', description: '', column: 'todo' })
  })

  it('only sends the fields being updated', async () => {
    const fetchMock = mockFetch(200, {})
    await updateCard('42', { title: 'New title' })
    const [url, options] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/cards/42')
    expect(JSON.parse(options.body)).toEqual({ title: 'New title' })
  })

  it('moves a card with PATCH /cards/{id}/move', async () => {
    const fetchMock = mockFetch(200, {})
    await moveCard('42', { column: 'done' })
    expect(fetchMock.mock.calls[0][0]).toBe('/api/cards/42/move')
    expect(fetchMock.mock.calls[0][1].method).toBe('PATCH')
  })

  it('returns null for 204 responses', async () => {
    mockFetch(204, null)
    await expect(deleteCard('42')).resolves.toBeNull()
  })

  it('throws with the status code when the backend fails', async () => {
    mockFetch(500, { detail: 'boom' })
    await expect(getBoard()).rejects.toThrow('API error 500 on /board')
  })
})
