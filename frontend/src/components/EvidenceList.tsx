import { useState, useEffect, useCallback } from 'react'
import type { EvidenceResponse } from '../api/types'
import { listEvidence, deleteEvidence } from '../api/evidence'
import LoadingSpinner from './LoadingSpinner'
import ErrorMessage from './ErrorMessage'
import { formatDate } from '../utils/formatDate'

interface Props {
  investigationId: number
  onEdit: (evidence: EvidenceResponse) => void
  refreshKey?: number
}

export default function EvidenceList({ investigationId, onEdit, refreshKey }: Props) {
  const [items, setItems] = useState<EvidenceResponse[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [deletingId, setDeletingId] = useState<number | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await listEvidence(investigationId)
      setItems(data.items)
      setTotal(data.total)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load evidence.')
    } finally {
      setLoading(false)
    }
  }, [investigationId])

  useEffect(() => { load() }, [load, refreshKey])

  async function handleDelete(ev: EvidenceResponse) {
    if (!window.confirm(`Delete "${ev.title ?? ev.source_name}"? This cannot be undone.`)) return
    setDeletingId(ev.id)
    try {
      await deleteEvidence(investigationId, ev.id)
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete evidence.')
    } finally {
      setDeletingId(null)
    }
  }

  if (loading) return <LoadingSpinner />
  if (error) return <ErrorMessage message={error} onRetry={load} />

  return (
    <div>
      <p style={styles.count}>{total} evidence item{total !== 1 ? 's' : ''}</p>

      {items.length === 0 ? (
        <div style={styles.empty}>
          No evidence yet. Add the first item above.
        </div>
      ) : (
        <ul style={styles.list}>
          {items.map(ev => (
            <li key={ev.id} style={styles.card}>
              <div style={styles.cardBody}>
                <div style={styles.cardTop}>
                  <span style={styles.cardTitle}>{ev.title ?? ev.source_name}</span>
                  <div style={styles.badges}>
                    <span style={sourceTypeBadge(ev.source_type)}>{ev.source_type}</span>
                    <span style={evidenceTypeBadge(ev.evidence_type)}>{ev.evidence_type}</span>
                    <span style={confidenceBadge(ev.confidence)}>
                      {Math.round(ev.confidence * 100)}%
                    </span>
                  </div>
                </div>

                {ev.title && ev.title !== ev.source_name && (
                  <div style={styles.sourceName}>{ev.source_name}</div>
                )}

                {ev.content && (
                  <p style={styles.content}>{ev.content}</p>
                )}

                {ev.source_url && (
                  <a
                    href={ev.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={styles.link}
                  >
                    {ev.source_url}
                  </a>
                )}

                <div style={styles.metaRow}>
                  <span style={styles.metaText}>
                    Collected {formatDate(ev.collected_at)}
                  </span>
                </div>
              </div>

              <div style={styles.actions}>
                <button
                  style={styles.editBtn}
                  onClick={() => onEdit(ev)}
                  title="Edit evidence"
                >
                  Edit
                </button>
                <button
                  style={styles.deleteBtn}
                  onClick={() => handleDelete(ev)}
                  disabled={deletingId === ev.id}
                  title="Delete evidence"
                >
                  {deletingId === ev.id ? '…' : '✕'}
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

function sourceTypeBadge(value: string): React.CSSProperties {
  const map: Record<string, { bg: string; color: string }> = {
    manual: { bg: '#f3f4f6', color: '#374151' },
    osint:  { bg: '#eff6ff', color: '#1d4ed8' },
    import: { bg: '#faf5ff', color: '#6b21a8' },
    demo:   { bg: '#ecfdf5', color: '#065f46' },
  }
  const c = map[value] ?? { bg: '#f3f4f6', color: '#374151' }
  return badge(c)
}

function evidenceTypeBadge(value: string): React.CSSProperties {
  return badge({ bg: '#f0f9ff', color: '#0369a1' })
}

function confidenceBadge(confidence: number): React.CSSProperties {
  let bg = '#f3f4f6'
  let color = '#374151'
  if (confidence >= 0.8) { bg = '#dcfce7'; color = '#166534' }
  else if (confidence >= 0.5) { bg = '#fef9c3'; color = '#92400e' }
  else { bg = '#fee2e2'; color = '#991b1b' }
  return badge({ bg, color })
}

function badge({ bg, color }: { bg: string; color: string }): React.CSSProperties {
  return {
    display: 'inline-block',
    padding: '0.1rem 0.5rem',
    borderRadius: 9999,
    fontSize: '0.73rem',
    fontWeight: 500,
    background: bg,
    color,
    whiteSpace: 'nowrap' as const,
  }
}

const styles: Record<string, React.CSSProperties> = {
  count: { margin: '0 0 0.6rem', fontSize: '0.8rem', color: '#57606a' },
  empty: {
    padding: '1.5rem',
    textAlign: 'center',
    color: '#57606a',
    border: '1px dashed #e5e7eb',
    borderRadius: 8,
    fontSize: '0.875rem',
  },
  list: { listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column' as const, gap: '0.5rem' },
  card: {
    display: 'flex',
    alignItems: 'stretch',
    border: '1px solid #e5e7eb',
    borderRadius: 7,
    background: '#fff',
    overflow: 'hidden',
  },
  cardBody: {
    flex: 1,
    padding: '0.85rem 1rem',
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '0.3rem',
    minWidth: 0,
  },
  cardTop: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: '0.75rem',
    flexWrap: 'wrap' as const,
  },
  cardTitle: { fontWeight: 600, fontSize: '0.9rem' },
  badges: { display: 'flex', gap: '0.3rem', flexWrap: 'wrap' as const, flexShrink: 0 },
  sourceName: { fontSize: '0.8rem', color: '#57606a' },
  content: { margin: 0, fontSize: '0.825rem', color: '#374151', lineHeight: 1.5 },
  link: {
    fontSize: '0.775rem',
    color: '#3b82d4',
    textDecoration: 'none',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap' as const,
    display: 'block',
  },
  metaRow: { marginTop: '0.15rem' },
  metaText: { fontSize: '0.75rem', color: '#9ca3af' },
  actions: {
    display: 'flex',
    flexDirection: 'column' as const,
    borderLeft: '1px solid #e5e7eb',
    flexShrink: 0,
  },
  editBtn: {
    flex: 1,
    padding: '0 0.85rem',
    background: 'transparent',
    border: 'none',
    borderBottom: '1px solid #e5e7eb',
    cursor: 'pointer',
    color: '#57606a',
    fontSize: '0.775rem',
    fontWeight: 500,
  },
  deleteBtn: {
    flex: 1,
    padding: '0 0.85rem',
    background: 'transparent',
    border: 'none',
    cursor: 'pointer',
    color: '#9ca3af',
    fontSize: '0.85rem',
  },
}
