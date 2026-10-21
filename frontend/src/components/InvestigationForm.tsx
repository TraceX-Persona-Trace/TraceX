import { useState } from 'react'
import type { CreateInvestigationRequest, UpdateInvestigationRequest, InvestigationResponse } from '../api/types'

interface CreateMode {
  mode: 'create'
  onSubmit: (data: CreateInvestigationRequest) => Promise<void>
  onCancel: () => void
}

interface EditMode {
  mode: 'edit'
  investigation: InvestigationResponse
  onSubmit: (data: UpdateInvestigationRequest) => Promise<void>
  onCancel: () => void
}

type Props = CreateMode | EditMode

export default function InvestigationForm(props: Props) {
  const isEdit = props.mode === 'edit'
  const inv = isEdit ? props.investigation : null

  const [title, setTitle] = useState(inv?.title ?? '')
  const [description, setDescription] = useState(inv?.description ?? '')
  const [mode, setMode] = useState<'demo' | 'live'>(inv?.mode ?? 'demo')
  const [status, setStatus] = useState<'active' | 'archived'>(inv?.status ?? 'active')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!title.trim()) {
      setError('Title is required.')
      return
    }
    setError(null)
    setSubmitting(true)
    try {
      if (isEdit) {
        await (props as EditMode).onSubmit({ title: title.trim(), description: description.trim() || undefined, status, mode })
      } else {
        await (props as CreateMode).onSubmit({ title: title.trim(), description: description.trim() || undefined, mode })
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} style={styles.form}>
      <h2 style={styles.heading}>{isEdit ? 'Edit Investigation' : 'New Investigation'}</h2>

      {error && <div style={styles.error}>{error}</div>}

      <label style={styles.label}>
        Title <span style={styles.required}>*</span>
        <input
          style={styles.input}
          value={title}
          onChange={e => setTitle(e.target.value)}
          placeholder="Investigation title"
          disabled={submitting}
        />
      </label>

      <label style={styles.label}>
        Description
        <textarea
          style={{ ...styles.input, ...styles.textarea }}
          value={description}
          onChange={e => setDescription(e.target.value)}
          placeholder="Optional description"
          disabled={submitting}
          rows={3}
        />
      </label>

      <label style={styles.label}>
        Mode
        <select style={styles.input} value={mode} onChange={e => setMode(e.target.value as 'demo' | 'live')} disabled={submitting}>
          <option value="demo">Demo</option>
          <option value="live">Live</option>
        </select>
      </label>

      {isEdit && (
        <label style={styles.label}>
          Status
          <select style={styles.input} value={status} onChange={e => setStatus(e.target.value as 'active' | 'archived')} disabled={submitting}>
            <option value="active">Active</option>
            <option value="archived">Archived</option>
          </select>
        </label>
      )}

      <div style={styles.actions}>
        <button type="button" style={styles.cancelBtn} onClick={props.onCancel} disabled={submitting}>
          Cancel
        </button>
        <button type="submit" style={styles.submitBtn} disabled={submitting}>
          {submitting ? 'Saving…' : isEdit ? 'Save Changes' : 'Create'}
        </button>
      </div>
    </form>
  )
}

const styles: Record<string, React.CSSProperties> = {
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem',
    background: '#f7f8fa',
    border: '1px solid #e5e7eb',
    borderRadius: 8,
    padding: '1.5rem',
    maxWidth: 560,
  },
  heading: {
    margin: 0,
    fontSize: '1.1rem',
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
    fontSize: '0.9rem',
    background: '#fff',
    color: '#1f2328',
    outline: 'none',
    fontFamily: 'inherit',
  },
  textarea: { resize: 'vertical' as const },
  actions: {
    display: 'flex',
    gap: '0.75rem',
    justifyContent: 'flex-end',
    marginTop: '0.25rem',
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
