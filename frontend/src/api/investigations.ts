import type {
  CreateInvestigationRequest,
  UpdateInvestigationRequest,
  InvestigationResponse,
  InvestigationListResponse,
} from './types'

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

export function createInvestigation(
  data: CreateInvestigationRequest,
): Promise<InvestigationResponse> {
  return request('/investigations', {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function getInvestigations(): Promise<InvestigationListResponse> {
  return request('/investigations')
}

export function getInvestigation(id: number): Promise<InvestigationResponse> {
  return request(`/investigations/${id}`)
}

export function updateInvestigation(
  id: number,
  data: UpdateInvestigationRequest,
): Promise<InvestigationResponse> {
  return request(`/investigations/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

export function deleteInvestigation(id: number): Promise<{ detail: string }> {
  return request(`/investigations/${id}`, { method: 'DELETE' })
}
