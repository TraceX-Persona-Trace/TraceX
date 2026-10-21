export interface CreateInvestigationRequest {
  title: string
  description?: string
  mode?: 'demo' | 'live'
}

export interface UpdateInvestigationRequest {
  title?: string
  description?: string
  status?: 'active' | 'archived'
  mode?: 'demo' | 'live'
}

export interface InvestigationResponse {
  id: number
  title: string
  description: string | null
  status: 'active' | 'archived'
  mode: 'demo' | 'live'
  created_at: string
  updated_at: string
}

export interface InvestigationListResponse {
  items: InvestigationResponse[]
  total: number
}

export interface EvidenceResponse {
  id: number
  investigation_id: number
  source_type: string
  source_name: string
  source_url: string | null
  title: string | null
  content: string | null
  evidence_type: string
  confidence: number
  collected_at: string
  metadata_json: string | null
  normalised_value: string | null  // Chunk 6: canonical matchable value
}

export interface EvidenceListResponse {
  items: EvidenceResponse[]
  total: number
}

export interface CreateEvidenceRequest {
  source_type?: string
  source_name: string
  source_url?: string
  title?: string
  content?: string
  evidence_type: string
  confidence?: number
  metadata_json?: string
  normalised_value?: string  // Chunk 6: canonical matchable value
}

export interface UpdateEvidenceRequest {
  source_type?: string
  source_name?: string
  source_url?: string
  title?: string
  content?: string
  evidence_type?: string
  confidence?: number
  metadata_json?: string
  normalised_value?: string  // Chunk 6: canonical matchable value
}

// ---- Reconstruction (Chunk 5A backend contract) ----

export interface ReconstructionAttribute {
  evidence_id: number
  evidence_type: string
  source_type: string
  source_name: string
  source_url: string | null
  label: string | null       // Evidence.title — human-readable display label
  value: string | null       // Evidence.normalised_value — canonical matchable value (may be null)
  detail: string | null      // Evidence.content — may be null
  confidence: number         // 0.0–1.0, sourced directly from Evidence.confidence
  collected_at: string
}

export interface ReconstructionResult {
  investigation_id: number
  status: 'ok' | 'empty'
  evidence_used: number
  attributes: ReconstructionAttribute[]
  generated_at: string
}

// ---- Matching (Chunk 6 backend contract) ----

export interface MatchHit {
  query_evidence_id: number
  matched_evidence_id: number
  matched_investigation_id: number
  matched_investigation_title: string
  evidence_type: string
  match_rule: string
  query_value: string
  matched_value: string
  source_confidence: number  // Evidence.confidence of matched row (real, not synthetic)
}

export interface MatchResult {
  investigation_id: number
  query_attributes: number
  hits: MatchHit[]
  status: 'ok' | 'no_matches' | 'no_matchable_attributes'
  generated_at: string
}

// ---- Intelligence (Chunk 7 backend contract) ----

export interface IntelligenceSignal {
  signal_type: string
  title: string
  explanation: string
  severity: 'info' | 'low' | 'medium' | 'high'
  evidence_ids: number[]
  investigation_ids: number[]
  match_rule: string | null
  attribute_value: string | null
  evidence_type: string | null
  source_confidence: number | null  // real Evidence.confidence, never synthetic
}

export interface IntelligenceResult {
  investigation_id: number
  signals: IntelligenceSignal[]
  summary: string
  total_evidence: number
  total_signals: number
  provider: string       // "deterministic" | future: "openai", "anthropic", etc.
  generated_at: string
}
