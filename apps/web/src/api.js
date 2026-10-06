// Cliente mínimo del API FastAPI del contenedor dm_analytics.
// VITE_API_URL apunta al puerto expuesto en docker-compose (8000).
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function apiGet(path) {
  const res = await fetch(`${API_URL}${path}`)
  if (!res.ok) {
    throw new Error(`Error ${res.status} al consultar ${path}`)
  }
  return res.json()
}

// Envía datos al API (POST/PUT/DELETE). Retorna el JSON de respuesta
// o null cuando el endpoint responde 204 No Content.
export async function apiSend(path, method, body) {
  const res = await fetch(`${API_URL}${path}`, {
    method,
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  })
  if (!res.ok) {
    throw new Error(`Error ${res.status} en ${method} ${path}`)
  }
  return res.status === 204 ? null : res.json()
}
