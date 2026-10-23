// Centralized backend calls for Boardly.
//
// Every network call the app makes goes through this module, talking to the
// FastAPI backend over the contract in openapi.yaml. Component code never
// calls fetch() directly — it only imports functions from here.

// Same-origin '/api' by default: nginx (Docker/Kubernetes) and the Vite dev
// server both proxy it to the backend, so the browser never needs CORS.
export const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })

  if (!response.ok) {
    const detail = await response.text()
    throw new Error(`API error ${response.status} on ${path}: ${detail}`)
  }

  if (response.status === 204) return null
  return response.json()
}

export function getBoard() {
  return request('/board')
}

export function createCard({ title, description = '', column = 'new' }) {
  return request('/cards', {
    method: 'POST',
    body: JSON.stringify({ title, description, column }),
  })
}

export function updateCard(id, { title, description }) {
  const body = {}
  if (title !== undefined) body.title = title
  if (description !== undefined) body.description = description
  return request(`/cards/${id}`, { method: 'PATCH', body: JSON.stringify(body) })
}

export function moveCard(id, { column }) {
  return request(`/cards/${id}/move`, {
    method: 'PATCH',
    body: JSON.stringify({ column }),
  })
}

export function deleteCard(id) {
  return request(`/cards/${id}`, { method: 'DELETE' })
}
