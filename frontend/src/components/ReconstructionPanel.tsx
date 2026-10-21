import { useState } from 'react'
import type { ReconstructionResult, ReconstructionAttribute } from '../api/types'
import { runReconstruction } from '../api/reconstruction'
import LoadingSpinner from './LoadingSpinner'
import ErrorMessage from './ErrorMessage'

interface Props {
  investigationId: number
}

export default function ReconstructionPanel({ investigationId }: Props) {
  const [result, setResult] = useState<ReconstructionResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleRun() {
    setLoading(true)
    setError(null)
    try {
      const data = await runReconstruction(investigationId)
      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Reconstruction failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={styles.section}>
      <div style={styles.header}>
        <h3 style={styles.title}>Person Reconstruction</h3>
        <button
          style={loading ? styles.runBtnDisabled : styles.runBtn}
          onClick={handleRun}
          disabled={loading}
        >
          {loading ? 'Running…' : result ? 'Re-run' : 'Run Reconstruction'}
        </button>
      </div>

      {loading && <LoadingSpinner />}

      {!loading && error && (
        <ErrorMessage message={error} onRetry={handleRun} />
      )}

      {!loading && !error && result && (
        <ResultView result={result} />
      )}

      {!loading && !error && !result && (
        <p style={styles.hint}>
          Run reconstruction to derive a structured profile from this investigation's evidence.
        </p>
      )}
    </div>
  )
}

function ResultView({ result }: { result: ReconstructionResult }) {
  if (result.status === 'empty') {
    return (
      <div style={styles.empty}>
        No evidence available to reconstruct. Add evidence items above, then re-run.
      </div>
    )
  }

  return (
    <div>
      <p style={styles.summary}>
        {result.evidence_used} evidence item{result.evidence_used !== 1 ? 's' : ''} used
        &nbsp;·&nbsp;
        Generated {new Date(result.generated_at).toLocaleString()}
      </p>
      <ul style={styles.list}>
        {result.attributes.map(attr => (
          <AttributeRow key={attr.evidence_id} attr={attr} />
        ))}
      </ul>
    </div>
  )
}

function AttributeRow({ attr }: { attr: ReconstructionAttribute }) {
  // Priority: label (human title) → value (normalised, if no label) → source_name (fallback)
  const displayValue = attr.label ?? attr.value ?? attr.source_name

  return (
    <li style={styles.card}>
      <div style={styles.cardBody}>
        <div style={styles.cardTop}>
          <span style={styles.cardTitle}>{displayValue}</span>
          <div style={styles.badges}>
            <span style={sourceTypeBadge(attr.source_type)}>{attr.source_type}</span>
            <span style={evidenceTypeBadge()}>{attr.evidence_type}</span>
            <span style={confidenceBadge(attr.confidence)}>
              {Math.round(attr.confidence * 100)}%
            </span>
          </div>
        </div>

        {/* Show source_name as subtitle only when it differs from the primary display */}
        {displayValue !== attr.source_name && (
          <div style={styles.sourceName}>{attr.source_name}</div>
        )}

        {attr.detail && (
          <p style={styles.detail}>{attr.detail}</p>
        )}

        {attr.source_url && (
          <a
            href={attr.source_url}
            target="_blank"
            rel="noopener noreferrer"
            style={styles.link}
          >
            {attr.source_url}
          </a>
        )}

        <div style={styles.metaRow}>
          <span style={styles.metaText}>
            Collected {new Date(attr.collected_at).toLocaleString()}
            &nbsp;·&nbsp;
            <span style={styles.evidenceRef}>evidence #{attr.evidence_id}</span>
          </span>
        </div>
      </div>
    </li>
  )
}

// ---- badge helpers (mirrors EvidenceList.tsx pattern) ----

function sourceTypeBadge(value: string): React.CSSProperties {
  const map: Record<string, { bg: string; color: string }> = {
    manual: { bg: '#f3f4f6', color: '#374151' },
    osint:  { bg: '#eff6ff', color: '#1d4ed8' },
    import: { bg: '#faf5ff', color: '#6b21a8' },
    demo:   { bg: '#ecfdf5', color: '#065f46' },
  }
  const c = map[value] ?? { bg: '#f3f4f6', color: '#374151' }
  return badgeStyle(c)
}

function evidenceTypeBadge(): React.CSSProperties {
  return badgeStyle({ bg: '#f0f9ff', color: '#0369a1' })
}

function confidenceBadge(confidence: number): React.CSSProperties {
  let bg = '#f3f4f6'
  let color = '#374151'
  if (confidence >= 0.8)      { bg = '#dcfce7'; color = '#166534' }
  else if (confidence >= 0.5) { bg = '#fef9c3'; color = '#92400e' }
  else                        { bg = '#fee2e2'; color = '#991b1b' }
  return badgeStyle({ bg, color })
}

function badgeStyle({ bg, color }: { bg: string; color: string }): React.CSSProperties {
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

// ---- styles ----

const styles: Record<string, React.CSSProperties> = {
  section: {
    marginTop: '2rem',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '0.75rem',
  },
  title: {
    margin: 0,
    fontSize: '1rem',
    fontWeight: 600,
    color: '#1f2328',
  },
  runBtn: {
    padding: '0.35rem 0.9rem',
    background: '#7c5cd8',
    color: '#fff',
    border: 'none',
    borderRadius: 6,
    cursor: 'pointer',
    fontSize: '0.8rem',
    fontWeight: 500,
  },
  runBtnDisabled: {
    padding: '0.35rem 0.9rem',
    background: '#c4b5fd',
    color: '#fff',
    border: 'none',
    borderRadius: 6,
    cursor: 'not-allowed',
    fontSize: '0.8rem',
    fontWeight: 500,
  },
  hint: {
    margin: 0,
    color: '#57606a',
    fontSize: '0.875rem',
    padding: '1rem',
    border: '1px dashed #e5e7eb',
    borderRadius: 8,
    textAlign: 'center' as const,
  },
  empty: {
    padding: '1.5rem',
    textAlign: 'center' as const,
    color: '#57606a',
    border: '1px dashed #e5e7eb',
    borderRadius: 8,
    fontSize: '0.875rem',
  },
  summary: {
    margin: '0 0 0.6rem',
    fontSize: '0.8rem',
    color: '#57606a',
  },
  list: {
    listStyle: 'none',
    padding: 0,
    margin: 0,
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '0.5rem',
  },
  card: {
    display: 'flex',
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
  badges: {
    display: 'flex',
    gap: '0.3rem',
    flexWrap: 'wrap' as const,
    flexShrink: 0,
  },
  sourceName: { fontSize: '0.8rem', color: '#57606a' },
  detail: {
    margin: 0,
    fontSize: '0.825rem',
    color: '#374151',
    lineHeight: 1.5,
  },
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
  evidenceRef: { fontFamily: 'monospace', fontSize: '0.72rem' },
}
