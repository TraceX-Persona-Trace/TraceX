import { useEffect, useState, useCallback } from 'react'
import type { InvestigationResponse } from '../api/types'
import { getInvestigations, deleteInvestigation, createInvestigation } from '../api/investigations'
import LoadingSpinner from './LoadingSpinner'
import ErrorMessage from './ErrorMessage'
import InvestigationForm from './InvestigationForm'

interface Props {
  onSelect: (inv: InvestigationResponse) => void
}

export default function InvestigationList({ onSelect }: Props) {
  const [items, setItems] = useState<InvestigationResponse[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [deletingId, setDeletingId] = useState<number | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getInvestigations()
      setItems(data.items)
      setTotal(data.total)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load investigations.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  async function handleCreate(data: Parameters<typeof createInvestigation>[0]) {
    await createInvestigation(data)
    setShowForm(false)
    await load()
  }

  async function handleDelete(id: number, title: string) {
    if (!window.confirm(`Delete "${title}"? This cannot be undone.`)) return
    setDeletingId(id)
    try {
      await deleteInvestigation(id)
      await load()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete investigation.')
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>TraceX</h1>
          <p style={styles.subtitle}>Ethical OSINT Identity Intelligence Platform</p>
        </div>
        <button style={styles.newBtn} onClick={() => setShowForm(true)}>
          + New Investigation
        </button>
      </div>

      {showForm && (
        <div style={styles.formWrapper}>
          <InvestigationForm
            mode="create"
            onSubmit={handleCreate}
            onCancel={() => setShowForm(false)}
          />
        </div>
      )}

      {error && <ErrorMessage message={error} onRetry={load} />}

      {loading ? (
        <LoadingSpinner />
      ) : items.length === 0 ? (
        <div style={styles.empty}>
          No investigations yet. Create one to get started.
        </div>
      ) : (
        <div style={styles.listWrapper}>
          <p style={styles.count}>{total} investigation{total !== 1 ? 's' : ''}</p>
          <ul style={styles.list}>
            {items.map(inv => (
              <li key={inv.id} style={styles.card}>
                <button style={styles.cardBody} onClick={() => onSelect(inv)}>
                  <div style={styles.cardTitle}>{inv.title}</div>
                  {inv.description && (
                    <div style={styles.cardDesc}>{inv.description}</div>
                  )}
                  <div style={styles.cardMeta}>
                    <span style={badge(inv.status)}>{inv.status}</span>
                    <span style={badge(inv.mode)}>{inv.mode}</span>
                    <span style={styles.metaText}>
                      {new Date(inv.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </button>
                <button
                  style={styles.deleteBtn}
                  onClick={() => handleDelete(inv.id, inv.title)}
                  disabled={deletingId === inv.id}
                  title="Delete investigation"
                >
                  {deletingId === inv.id ? '…' : '✕'}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
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
    padding: '0.1rem 0.5rem',
    borderRadius: 9999,
    fontSize: '0.75rem',
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
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: '1.5rem',
    flexWrap: 'wrap' as const,
    gap: '0.75rem',
  },
  title: { margin: 0, fontSize: '1.6rem', fontWeight: 700 },
  subtitle: { margin: '0.2rem 0 0', color: '#57606a', fontSize: '0.9rem' },
  newBtn: {
    padding: '0.5rem 1.1rem',
    background: '#3b82d4',
    color: '#fff',
    border: 'none',
    borderRadius: 6,
    cursor: 'pointer',
    fontSize: '0.875rem',
    fontWeight: 500,
    alignSelf: 'center',
  },
  formWrapper: { marginBottom: '1.5rem' },
  empty: {
    padding: '2rem',
    textAlign: 'center',
    color: '#57606a',
    border: '1px dashed #e5e7eb',
    borderRadius: 8,
    fontSize: '0.9rem',
  },
  count: { margin: '0 0 0.5rem', fontSize: '0.8rem', color: '#57606a' },
  listWrapper: {},
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
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '0.25rem',
    padding: '0.85rem 1rem',
    background: 'transparent',
    border: 'none',
    cursor: 'pointer',
    textAlign: 'left' as const,
    color: 'inherit',
  },
  cardTitle: { fontWeight: 600, fontSize: '0.95rem' },
  cardDesc: { color: '#57606a', fontSize: '0.82rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' as const },
  cardMeta: { display: 'flex', gap: '0.4rem', alignItems: 'center', marginTop: '0.2rem' },
  metaText: { color: '#57606a', fontSize: '0.75rem', marginLeft: 'auto' },
  deleteBtn: {
    padding: '0 0.85rem',
    background: 'transparent',
    border: 'none',
    borderLeft: '1px solid #e5e7eb',
    cursor: 'pointer',
    color: '#9ca3af',
    fontSize: '0.85rem',
    flexShrink: 0,
  },
}
