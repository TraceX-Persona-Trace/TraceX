import { useState, useEffect, useCallback } from 'react'
import type { InvestigationResponse, UpdateInvestigationRequest, EvidenceResponse, CreateEvidenceRequest, UpdateEvidenceRequest } from '../api/types'
import { getInvestigation, updateInvestigation } from '../api/investigations'
import { createEvidence, updateEvidence } from '../api/evidence'
import LoadingSpinner from './LoadingSpinner'
import ErrorMessage from './ErrorMessage'
import InvestigationForm from './InvestigationForm'
import EvidenceList from './EvidenceList'
import EvidenceForm from './EvidenceForm'
import ReconstructionPanel from './ReconstructionPanel'
import MatchingPanel from './MatchingPanel'
import IntelligencePanel from './IntelligencePanel'

interface Props {
  id: number
  onBack: () => void
}

export default function InvestigationDetail({ id, onBack }: Props) {
  const [inv, setInv] = useState<InvestigationResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [editing, setEditing] = useState(false)
  const [evidenceRefreshKey, setEvidenceRefreshKey] = useState(0)
  const [showEvidenceForm, setShowEvidenceForm] = useState(false)
  const [editingEvidence, setEditingEvidence] = useState<EvidenceResponse | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getInvestigation(id)
      setInv(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load investigation.')
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => { load() }, [load])

  async function handleUpdate(data: UpdateInvestigationRequest) {
    const updated = await updateInvestigation(id, data)
    setInv(updated)
    setEditing(false)
  }

  async function handleCreateEvidence(data: CreateEvidenceRequest) {
    await createEvidence(id, data)
    setShowEvidenceForm(false)
    setEvidenceRefreshKey(k => k + 1)
  }

  async function handleUpdateEvidence(data: UpdateEvidenceRequest) {
    if (!editingEvidence) return
    await updateEvidence(id, editingEvidence.id, data)
    setEditingEvidence(null)
    setEvidenceRefreshKey(k => k + 1)
  }

  function handleEditEvidence(ev: EvidenceResponse) {
    setShowEvidenceForm(false)
    setEditingEvidence(ev)
  }

  if (loading) return <div style={styles.container}><LoadingSpinner /></div>
  if (error) return <div style={styles.container}><ErrorMessage message={error} onRetry={load} /></div>
  if (!inv) return null

  return (
    <div style={styles.container}>
      <button style={styles.back} onClick={onBack}>← Back to investigations</button>

      {editing ? (
        <InvestigationForm
          mode="edit"
          investigation={inv}
          onSubmit={handleUpdate}
          onCancel={() => setEditing(false)}
        />
      ) : (
        <div style={styles.card}>
          <div style={styles.cardHeader}>
            <h2 style={styles.title}>{inv.title}</h2>
            <button style={styles.editBtn} onClick={() => setEditing(true)}>Edit</button>
          </div>

          {inv.description && (
            <p style={styles.description}>{inv.description}</p>
          )}

          <dl style={styles.meta}>
            <div style={styles.metaRow}>
              <dt style={styles.metaDt}>Status</dt>
              <dd style={styles.metaDd}>
                <span style={badge(inv.status)}>{inv.status}</span>
              </dd>
            </div>
            <div style={styles.metaRow}>
              <dt style={styles.metaDt}>Mode</dt>
              <dd style={styles.metaDd}>
                <span style={badge(inv.mode)}>{inv.mode}</span>
              </dd>
            </div>
            <div style={styles.metaRow}>
              <dt style={styles.metaDt}>Created</dt>
              <dd style={styles.metaDd}>{new Date(inv.created_at).toLocaleString()}</dd>
            </div>
            <div style={styles.metaRow}>
              <dt style={styles.metaDt}>Updated</dt>
              <dd style={styles.metaDd}>{new Date(inv.updated_at).toLocaleString()}</dd>
            </div>
            <div style={styles.metaRow}>
              <dt style={styles.metaDt}>ID</dt>
              <dd style={{ ...styles.metaDd, color: '#57606a', fontFamily: 'monospace' }}>{inv.id}</dd>
            </div>
          </dl>
        </div>
      )}

      {/* Evidence Panel */}
      <div style={styles.evidenceSection}>
        <div style={styles.evidenceHeader}>
          <h3 style={styles.evidenceTitle}>Evidence</h3>
          {!showEvidenceForm && !editingEvidence && (
            <button style={styles.addBtn} onClick={() => setShowEvidenceForm(true)}>
              + Add Evidence
            </button>
          )}
        </div>

        {showEvidenceForm && (
          <div style={styles.formWrapper}>
            <EvidenceForm
              mode="create"
              onSubmit={handleCreateEvidence}
              onCancel={() => setShowEvidenceForm(false)}
            />
          </div>
        )}

        {editingEvidence && (
          <div style={styles.formWrapper}>
            <EvidenceForm
              mode="edit"
              evidence={editingEvidence}
              onSubmit={handleUpdateEvidence}
              onCancel={() => setEditingEvidence(null)}
            />
          </div>
        )}

        <EvidenceList
          investigationId={id}
          onEdit={handleEditEvidence}
          refreshKey={evidenceRefreshKey}
        />
      </div>

      <ReconstructionPanel investigationId={id} />
      <MatchingPanel investigationId={id} />
      <IntelligencePanel investigationId={id} />
    </div>
  )
}

function badge(value: string): React.CSSProperties {
  const colours: Record<string, { bg: string; color: string }> = {
    active:   { bg: '#dcfce7', color: '#166534' },
    archived: { bg: '#f3f4f6', color: '#6b7280' },
    demo:     { bg: '#eff6ff', color: '#1d4ed8' },
    live:     { bg: '#fef9c3', color: '#92400e' },
  }
  const c = colours[value] ?? { bg: '#f3f4f6', color: '#374151' }
  return {
    display: 'inline-block',
    padding: '0.15rem 0.55rem',
    borderRadius: 9999,
    fontSize: '0.8rem',
    fontWeight: 500,
    background: c.bg,
    color: c.color,
  }
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    maxWidth: 760,
    margin: '0 auto',
    padding: '2rem 1rem',
    fontFamily: '-apple-system, "Segoe UI", system-ui, sans-serif',
    color: '#1f2328',
  },
  back: {
    background: 'none',
    border: 'none',
    color: '#3b82d4',
    cursor: 'pointer',
    fontSize: '0.875rem',
    padding: 0,
    marginBottom: '1.25rem',
    display: 'block',
  },
  card: {
    border: '1px solid #e5e7eb',
    borderRadius: 8,
    background: '#fff',
    padding: '1.5rem',
  },
  cardHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: '1rem',
    marginBottom: '0.75rem',
  },
  title: { margin: 0, fontSize: '1.3rem', fontWeight: 700 },
  editBtn: {
    padding: '0.35rem 0.9rem',
    border: '1px solid #e5e7eb',
    borderRadius: 5,
    background: '#fff',
    color: '#57606a',
    cursor: 'pointer',
    fontSize: '0.8rem',
    flexShrink: 0,
  },
  description: {
    margin: '0 0 1rem',
    color: '#57606a',
    fontSize: '0.9rem',
    lineHeight: 1.5,
  },
  meta: {
    margin: 0,
    padding: 0,
    borderTop: '1px solid #e5e7eb',
    paddingTop: '1rem',
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '0.5rem',
  },
  metaRow: { display: 'flex', gap: '1rem', alignItems: 'center' },
  metaDt: {
    width: 80,
    flexShrink: 0,
    fontSize: '0.8rem',
    color: '#57606a',
    fontWeight: 500,
  },
  metaDd: { margin: 0, fontSize: '0.875rem' },
  evidenceSection: {
    marginTop: '2rem',
  },
  evidenceHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '0.75rem',
  },
  evidenceTitle: {
    margin: 0,
    fontSize: '1rem',
    fontWeight: 600,
    color: '#1f2328',
  },
  addBtn: {
    padding: '0.35rem 0.9rem',
    background: '#3b82d4',
    color: '#fff',
    border: 'none',
    borderRadius: 6,
    cursor: 'pointer',
    fontSize: '0.8rem',
    fontWeight: 500,
  },
  formWrapper: {
    marginBottom: '1rem',
  },
}
