import { useState } from 'react'
import type { MatchResult, MatchHit } from '../api/types'
import { runMatching } from '../api/matching'
import LoadingSpinner from './LoadingSpinner'
import ErrorMessage from './ErrorMessage'
import { formatDate } from '../utils/formatDate'

interface Props {
  investigationId: number
}

export default function MatchingPanel({ investigationId }: Props) {
  const [result, setResult] = useState<MatchResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleRun() {
    setLoading(true)
    setError(null)
    try {
      const data = await runMatching(investigationId)
      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Matching failed.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={styles.section}>
      <div style={styles.header}>
        <h3 style={styles.title}>Evidence Matching</h3>
        <button
          style={loading ? styles.runBtnDisabled : styles.runBtn}
          onClick={handleRun}
          disabled={loading}
        >
          {loading ? 'Searching…' : result ? 'Re-run' : 'Run Matching'}
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
          Run matching to find cross-investigation evidence that shares the same value (email, phone, username, domain, IP).
          Set a <strong>Matchable Value</strong> on evidence items first.
        </p>
      )}
    </div>
  )
}

function ResultView({ result }: { result: MatchResult }) {
  if (result.status === 'no_matchable_attributes') {
    return (
      <div style={styles.info}>
        No evidence items have a Matchable Value set. Edit evidence items above and add a canonical value (email address, username, etc.) to enable matching.
      </div>
    )
  }

  if (result.status === 'no_matches') {
    return (
      <div style={styles.info}>
        {result.query_attributes} attribute{result.query_attributes !== 1 ? 's' : ''} checked
        &nbsp;·&nbsp;
        No matching evidence found in other investigations.
        &nbsp;·&nbsp;
        Generated {formatDate(result.generated_at)}
      </div>
    )
  }

  return (
    <div>
      <p style={styles.summary}>
        {result.hits.length} match{result.hits.length !== 1 ? 'es' : ''} found
        &nbsp;·&nbsp;
        {result.query_attributes} attribute{result.query_attributes !== 1 ? 's' : ''} checked
        &nbsp;·&nbsp;
        Generated {formatDate(result.generated_at)}
      </p>
      <ul style={styles.list}>
        {result.hits.map((hit, i) => (
          <HitRow key={i} hit={hit} />
        ))}
      </ul>
    </div>
  )
}

function HitRow({ hit }: { hit: MatchHit }) {
  return (
    <li style={styles.card}>
      <div style={styles.cardBody}>
        <div style={styles.cardTop}>
          <span style={styles.cardTitle}>{hit.query_value}</span>
          <div style={styles.badges}>
            <span style={evidenceTypeBadge()}>{hit.evidence_type}</span>
            <span style={ruleBadge()}>{hit.match_rule}</span>
            <span style={confidenceBadge(hit.source_confidence)}>
              {Math.round(hit.source_confidence * 100)}%
            </span>
          </div>
        </div>

        <div style={styles.matchRow}>
          <span style={styles.matchLabel}>Matched in</span>
          <span style={styles.matchInv}>{hit.matched_investigation_title}</span>
        </div>

        {hit.matched_value !== hit.query_value && (
          <div style={styles.matchRow}>
            <span style={styles.matchLabel}>Matched as</span>
            <span style={styles.matchValue}>{hit.matched_value}</span>
          </div>
        )}

        <div style={styles.metaRow}>
          <span style={styles.metaText}>
            <span style={styles.ref}>evidence #{hit.query_evidence_id}</span>
            <span style={styles.arrow}> → </span>
            <span style={styles.ref}>evidence #{hit.matched_evidence_id}</span>
            <span style={styles.arrow}> in investigation #{hit.matched_investigation_id}</span>
          </span>
        </div>
      </div>
    </li>
  )
}

// ---- badge helpers ----

function evidenceTypeBadge(): React.CSSProperties {
  return badge({ bg: '#f0f9ff', color: '#0369a1' })
}

function ruleBadge(): React.CSSProperties {
  return badge({ bg: '#faf5ff', color: '#6b21a8' })
}

function confidenceBadge(confidence: number): React.CSSProperties {
  let bg = '#f3f4f6'
  let color = '#374151'
  if (confidence >= 0.8)      { bg = '#dcfce7'; color = '#166534' }
  else if (confidence >= 0.5) { bg = '#fef9c3'; color = '#92400e' }
  else                        { bg = '#fee2e2'; color = '#991b1b' }
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
    background: '#0369a1',
    color: '#fff',
    border: 'none',
    borderRadius: 6,
    cursor: 'pointer',
    fontSize: '0.8rem',
    fontWeight: 500,
  },
  runBtnDisabled: {
    padding: '0.35rem 0.9rem',
    background: '#7dd3fc',
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
  info: {
    padding: '1rem',
    color: '#57606a',
    border: '1px solid #e5e7eb',
    borderRadius: 8,
    fontSize: '0.875rem',
    background: '#f7f8fa',
  },
  summary: { margin: '0 0 0.6rem', fontSize: '0.8rem', color: '#57606a' },
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
  badges: { display: 'flex', gap: '0.3rem', flexWrap: 'wrap' as const, flexShrink: 0 },
  matchRow: { display: 'flex', gap: '0.5rem', alignItems: 'baseline' },
  matchLabel: { fontSize: '0.775rem', color: '#9ca3af', flexShrink: 0 },
  matchInv: { fontSize: '0.85rem', color: '#1f2328', fontWeight: 500 },
  matchValue: { fontSize: '0.825rem', color: '#374151', fontFamily: 'monospace' },
  metaRow: { marginTop: '0.15rem' },
  metaText: { fontSize: '0.75rem', color: '#9ca3af' },
  ref: { fontFamily: 'monospace', fontSize: '0.72rem' },
  arrow: { color: '#d1d5db' },
}
