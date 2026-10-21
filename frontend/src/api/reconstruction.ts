import type { ReconstructionResult } from './types'

const BASE = '/api'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    ...init,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail ?? res.statusText)
  }
  return res.json() as Promise<T>
}

export function runReconstruction(investigationId: number): Promise<ReconstructionResult> {
  return request(`/investigations/${investigationId}/reconstruct`, { method: 'POST' })
}
