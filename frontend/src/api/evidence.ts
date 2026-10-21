import type {
  CreateEvidenceRequest,
  UpdateEvidenceRequest,
  EvidenceResponse,
  EvidenceListResponse,
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

function evidencePath(investigationId: number, evidenceId?: number): string {
  const base = `/investigations/${investigationId}/evidence`
  return evidenceId !== undefined ? `${base}/${evidenceId}` : base
}

export function listEvidence(investigationId: number): Promise<EvidenceListResponse> {
  return request(evidencePath(investigationId))
}

export function getEvidence(investigationId: number, evidenceId: number): Promise<EvidenceResponse> {
  return request(evidencePath(investigationId, evidenceId))
}

export function createEvidence(investigationId: number, data: CreateEvidenceRequest): Promise<EvidenceResponse> {
  return request(evidencePath(investigationId), { method: 'POST', body: JSON.stringify(data) })
}

export function updateEvidence(investigationId: number, evidenceId: number, data: UpdateEvidenceRequest): Promise<EvidenceResponse> {
  return request(evidencePath(investigationId, evidenceId), { method: 'PATCH', body: JSON.stringify(data) })
}

export function deleteEvidence(investigationId: number, evidenceId: number): Promise<{ detail: string }> {
  return request(evidencePath(investigationId, evidenceId), { method: 'DELETE' })
}
