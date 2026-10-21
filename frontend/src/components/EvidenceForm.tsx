import { useState } from 'react'
import type { CreateEvidenceRequest, UpdateEvidenceRequest, EvidenceResponse } from '../api/types'

const EVIDENCE_TYPES = [
  'social_profile', 'email', 'phone', 'address', 'username',
  'image', 'document', 'domain', 'ip_address', 'other',
] as const

const SOURCE_TYPES = ['manual', 'osint', 'import', 'demo'] as const

interface CreateMode {
  mode: 'create'
  onSubmit: (data: CreateEvidenceRequest) => Promise<void>
  onCancel: () => void
}

interface EditMode {
  mode: 'edit'
  evidence: EvidenceResponse
  onSubmit: (data: UpdateEvidenceRequest) => Promise<void>
  onCancel: () => void
}

type Props = CreateMode | EditMode

export default function EvidenceForm(props: Props) {
  const isEdit = props.mode === 'edit'
  const ev = isEdit ? props.evidence : null

  const [sourceType, setSourceType] = useState(ev?.source_type ?? 'manual')
  const [sourceName, setSourceName] = useState(ev?.source_name ?? '')
  const [sourceUrl, setSourceUrl] = useState(ev?.source_url ?? '')
  const [title, setTitle] = useState(ev?.title ?? '')
  const [content, setContent] = useState(ev?.content ?? '')
  const [normalisedValue, setNormalisedValue] = useState(ev?.normalised_value ?? '')
  const [evidenceType, setEvidenceType] = useState(ev?.evidence_type ?? 'other')
  const [confidence, setConfidence] = useState(
    ev !== null ? String(Math.round(ev.confidence * 100)) : '80'
  )
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()

    if (!sourceName.trim()) {
      setError('Source name is required.')
      return
    }

    const confidenceNum = parseFloat(confidence) / 100
    if (isNaN(confidenceNum) || confidenceNum < 0 || confidenceNum > 100) {
      setError('Confidence must be between 0 and 100.')
      return
    }

    setError(null)
    setSubmitting(true)

    try {
      const payload = {
        source_type: sourceType,
        source_name: sourceName.trim(),
        source_url: sourceUrl.trim() || undefined,
        title: title.trim() || undefined,
        content: content.trim() || undefined,
        evidence_type: evidenceType,
        confidence: confidenceNum,
        normalised_value: normalisedValue.trim() || undefined,
      }

      if (isEdit) {
        await (props as EditMode).onSubmit(payload)
      } else {
        await (props as CreateMode).onSubmit(payload)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} style={styles.form}>
      <h3 style={styles.heading}>{isEdit ? 'Edit Evidence' : 'Add Evidence'}</h3>

      {error && <div style={styles.error}>{error}</div>}

      <div style={styles.row}>
        <label style={styles.label}>
          Source Type
          <select
            style={styles.input}
            value={sourceType}
            onChange={e => setSourceType(e.target.value)}
            disabled={submitting}
          >
            {SOURCE_TYPES.map(t => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </label>

        <label style={styles.label}>
          Evidence Type
          <select
            style={styles.input}
            value={evidenceType}
            onChange={e => setEvidenceType(e.target.value)}
            disabled={submitting}
          >
            {EVIDENCE_TYPES.map(t => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </label>
      </div>

      <label style={styles.label}>
        Source Name <span style={styles.required}>*</span>
        <input
          style={styles.input}
          value={sourceName}
          onChange={e => setSourceName(e.target.value)}
          placeholder="e.g. LinkedIn, Manual Entry"
          disabled={submitting}
        />
      </label>

      <label style={styles.label}>
        Title
        <input
          style={styles.input}
          value={title}
          onChange={e => setTitle(e.target.value)}
          placeholder="Optional display title"
          disabled={submitting}
        />
      </label>

      <label style={styles.label}>
        Source URL
        <input
          style={styles.input}
          type="url"
          value={sourceUrl}
          onChange={e => setSourceUrl(e.target.value)}
          placeholder="https://..."
          disabled={submitting}
        />
      </label>

      <label style={styles.label}>
        Content
        <textarea
          style={{ ...styles.input, ...styles.textarea }}
          value={content}
          onChange={e => setContent(e.target.value)}
          placeholder="Notes or extracted content"
          disabled={submitting}
          rows={3}
        />
      </label>

      <label style={styles.label}>
        Matchable Value
        <input
          style={styles.input}
          value={normalisedValue}
          onChange={e => setNormalisedValue(e.target.value)}
          placeholder="e.g. user@example.com, +15551234567, demo-user"
          disabled={submitting}
        />
        <span style={styles.fieldHint}>
          The canonical value used for cross-investigation matching (email address, phone number, username, domain, IP).
          Leave blank if not applicable.
        </span>
      </label>

      <label style={styles.label}>
        Confidence (0–100)
        <input
          style={styles.input}
          type="number"
          min={0}
          max={100}
          value={confidence}
          onChange={e => setConfidence(e.target.value)}
          disabled={submitting}
        />
      </label>

      <div style={styles.actions}>
        <button type="button" style={styles.cancelBtn} onClick={props.onCancel} disabled={submitting}>
          Cancel
        </button>
        <button type="submit" style={styles.submitBtn} disabled={submitting}>
          {submitting ? 'Saving…' : isEdit ? 'Save Changes' : 'Add Evidence'}
        </button>
      </div>
    </form>
  )
}

const styles: Record<string, React.CSSProperties> = {
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.85rem',
    background: '#f7f8fa',
    border: '1px solid #e5e7eb',
    borderRadius: 8,
    padding: '1.25rem',
  },
  heading: {
    margin: 0,
    fontSize: '1rem',
    fontWeight: 600,
    color: '#1f2328',
  },
  error: {
    padding: '0.6rem 0.9rem',
    background: '#fff8f8',
    border: '1px solid #fca5a5',
    borderRadius: 6,
    color: '#b91c1c',
    fontSize: '0.875rem',
  },
  row: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '0.75rem',
  },
  label: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.3rem',
    fontSize: '0.875rem',
    fontWeight: 500,
    color: '#1f2328',
  },
  required: { color: '#b91c1c' },
  input: {
    padding: '0.45rem 0.65rem',
    border: '1px solid #e5e7eb',
    borderRadius: 5,
    fontSize: '0.875rem',
    background: '#fff',
    color: '#1f2328',
    outline: 'none',
    fontFamily: 'inherit',
  },
  textarea: { resize: 'vertical' as const },
  fieldHint: {
    fontSize: '0.75rem',
    color: '#9ca3af',
    fontWeight: 400,
    lineHeight: 1.4,
  },
  actions: {
    display: 'flex',
    gap: '0.75rem',
    justifyContent: 'flex-end',
    marginTop: '0.1rem',
  },
  cancelBtn: {
    padding: '0.45rem 1rem',
    border: '1px solid #e5e7eb',
    borderRadius: 5,
    background: '#fff',
    color: '#57606a',
    cursor: 'pointer',
    fontSize: '0.875rem',
  },
  submitBtn: {
    padding: '0.45rem 1.2rem',
    border: 'none',
    borderRadius: 5,
    background: '#3b82d4',
    color: '#fff',
    cursor: 'pointer',
    fontSize: '0.875rem',
    fontWeight: 500,
  },
}
