import { useState } from 'react'
import type { IntelligenceResult, IntelligenceSignal } from '../api/types'
import { getIntelligence } from '../api/intelligence'
import LoadingSpinner from './LoadingSpinner'
import ErrorMessage from './ErrorMessage'

interface Props {
  investigationId: number
}

export default function IntelligencePanel({ investigationId }: Props) {
  const [result, setResult] = useState<IntelligenceResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleRun() {
    setLoading(true)
    setError(null)
    try {
      const data = await getIntelligence(investigationId)
      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Intelligence analysis failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={styles.section}>
      <div style={styles.header}>
        <h3 style={styles.title}>Investigation Intelligence</h3>
        <button
          style={loading ? styles.runBtnDisabled : styles.runBtn}
          onClick={handleRun}
          disabled={loading}
        >
          {loading ? 'Analysing…' : result ? 'Re-analyse' : 'Analyse'}
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
          Run analysis to generate structured intelligence from this investigation's
          evidence, reconstruction, and cross-investigation matching data.
        </p>
      )}
    </div>
  )
}

function ResultView({ result }: { result: IntelligenceResult }) {
  return (
    <div>
      {/* Summary bar */}
      <div style={styles.summaryBar}>
        <span style={styles.summaryText}>{result.summary}</span>
        <span style={styles.summaryMeta}>
          {result.total_evidence} evidence
          &nbsp;·&nbsp;
          {result.total_signals} signal{result.total_signals !== 1 ? 's' : ''}
          &nbsp;·&nbsp;
          <span style={styles.provider}>{result.provider}</span>
          &nbsp;·&nbsp;
          {new Date(result.generated_at).toLocaleString()}
        </span>
      </div>

      {result.signals.length === 0 ? (
        <div style={styles.empty}>No signals generated.</div>
      ) : (
        <ul style={styles.list}>
          {result.signals.map((sig, i) => (
            <SignalRow key={i} signal={sig} />
          ))}
        </ul>
      )}
    </div>
  )
}

function SignalRow({ signal }: { signal: IntelligenceSignal }) {
  return (
    <li style={{ ...styles.card, borderLeft: `3px solid ${severityColor(signal.severity)}` }}>
      <div style={styles.cardBody}>
        <div style={styles.cardTop}>
          <span style={styles.cardTitle}>{signal.title}</span>
          <div style={styles.badges}>
            <span style={severityBadge(signal.severity)}>{signal.severity}</span>
            <span style={typeBadge()}>{signal.signal_type.replace(/_/g, ' ')}</span>
          </div>
        </div>

        <p style={styles.explanation}>{signal.explanation}</p>

        <div style={styles.traceRow}>
          {signal.evidence_ids.length > 0 && (
            <span style={styles.trace}>
              evidence: {signal.evidence_ids.map(id => `#${id}`).join(', ')}
            </span>
          )}
          {signal.investigation_ids.length > 1 && (
            <span style={styles.trace}>
              investigations: {signal.investigation_ids.map(id => `#${id}`).join(', ')}
            </span>
          )}
          {signal.match_rule && (
            <span style={styles.trace}>rule: {signal.match_rule}</span>
          )}
          {signal.source_confidence !== null && signal.source_confidence !== undefined && (
            <span style={confidenceStyle(signal.source_confidence)}>
              {Math.round(signal.source_confidence * 100)}% confidence
            </span>
          )}
        </div>
      </div>
    </li>
  )
}

// ---- colour helpers ----

function severityColor(sev: string): string {
  const map: Record<string, string> = {
    info:   '#e5e7eb',
    low:    '#93c5fd',
    medium: '#fbbf24',
    high:   '#f87171',
  }
  return map[sev] ?? '#e5e7eb'
}

function severityBadge(sev: string): React.CSSProperties {
  const map: Record<string, { bg: string; color: string }> = {
    info:   { bg: '#f3f4f6', color: '#6b7280' },
    low:    { bg: '#eff6ff', color: '#1d4ed8' },
    medium: { bg: '#fef9c3', color: '#92400e' },
    high:   { bg: '#fee2e2', color: '#991b1b' },
  }
  const c = map[sev] ?? { bg: '#f3f4f6', color: '#374151' }
  return badge(c)
}

function typeBadge(): React.CSSProperties {
  return badge({ bg: '#f0f9ff', color: '#0369a1' })
}

function confidenceStyle(conf: number): React.CSSProperties {
  let bg = '#f3f4f6'; let color = '#374151'
  if (conf >= 0.85)      { bg = '#dcfce7'; color = '#166534' }
  else if (conf >= 0.65) { bg = '#fef9c3'; color = '#92400e' }
  else                   { bg = '#fee2e2'; color = '#991b1b' }
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

// ---- styles ----

const styles: Record<string, React.CSSProperties> = {
  section: { marginTop: '2rem' },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '0.75rem',
  },
  title: { margin: 0, fontSize: '1rem', fontWeight: 600, color: '#1f2328' },
  runBtn: {
    padding: '0.35rem 0.9rem',
    background: '#166534',
    color: '#fff',
    border: 'none',
    borderRadius: 6,
    cursor: 'pointer',
    fontSize: '0.8rem',
    fontWeight: 500,
  },
  runBtnDisabled: {
    padding: '0.35rem 0.9rem',
    background: '#86efac',
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
    lineHeight: 1.5,
  },
  summaryBar: {
    background: '#f7f8fa',
    border: '1px solid #e5e7eb',
    borderRadius: 8,
    padding: '0.75rem 1rem',
    marginBottom: '0.75rem',
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '0.25rem',
  },
  summaryText: { fontSize: '0.875rem', color: '#1f2328', fontWeight: 500 },
  summaryMeta: { fontSize: '0.75rem', color: '#9ca3af' },
  provider: { fontFamily: 'monospace', fontSize: '0.72rem' },
  empty: {
    padding: '1rem',
    color: '#57606a',
    fontSize: '0.875rem',
    textAlign: 'center' as const,
    border: '1px dashed #e5e7eb',
    borderRadius: 8,
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
    gap: '0.35rem',
    minWidth: 0,
  },
  cardTop: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: '0.75rem',
    flexWrap: 'wrap' as const,
  },
  cardTitle: { fontWeight: 600, fontSize: '0.875rem' },
  badges: { display: 'flex', gap: '0.3rem', flexWrap: 'wrap' as const, flexShrink: 0 },
  explanation: { margin: 0, fontSize: '0.825rem', color: '#374151', lineHeight: 1.5 },
  traceRow: {
    display: 'flex',
    gap: '0.5rem',
    flexWrap: 'wrap' as const,
    marginTop: '0.1rem',
    alignItems: 'center',
  },
  trace: {
    fontSize: '0.72rem',
    color: '#9ca3af',
    fontFamily: 'monospace',
  },
}
